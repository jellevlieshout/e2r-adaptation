#!/usr/bin/env python3
"""Survey analysis: QC screening, per-annotator z-scores, RQ comparisons.

Implements Survey/PLAN.md sections 4 and 5 on the merged long-format CSV
produced by merge_survey_responses.py.

QC (PLAN section 5, adapted for MAR):
  - completion threshold: drop respondents with <10 of 20 items rated on
    all three dimensions
  - repeat-pair filter: drop respondents whose mean |first - second| across
    the 2 pairs x 3 dimensions exceeds 25 points
  - bad-ref filter (ADAPTED): PLAN 5a compares each bad-ref score against the
    same respondent's rating of the real system output for that source, but
    the sampler never assigns the bad-ref's source as a real item to the same
    respondent. Adaptation: compare each bad-ref's meaning score against the
    respondent's own mean meaning score on real items; if BOTH bad-refs score
    at or above that mean, FLAG (not drop). Headline numbers are reported with
    flagged respondents included and excluded.

Analysis (PLAN section 4):
  - per-annotator z-scores over all rated cells (own mean/SD), per Graham 2013
  - aggregate real items only; no imputation; n reported per cell
  - RQ1: 8b_agentic vs 70b_agentic, RQ2: 8b_agentic vs 8b_monolithic,
    paired by source on per-source z-means (Wilcoxon + paired t)

Run:
    uv run --with pandas,scipy,matplotlib python scripts/analyze_survey_responses.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SURVEY_DIR = Path.home() / "Documents/Obsidian Vault/1 - Thesis/Survey"
RESULTS_DIR = SURVEY_DIR / "results"
DIMS = ["grammaticality", "meaning", "simplicity"]
SYSTEMS = ["8b_agentic", "8b_monolithic", "70b_agentic"]
SYSTEM_LABELS = {
    "8b_agentic": "Llama-3.1-8B agentic",
    "8b_monolithic": "Llama-3.1-8B monolithic",
    "70b_agentic": "Llama-3.3-70B agentic",
}


def ci95_half_width(values: np.ndarray) -> float:
    """Half-width of the 95% CI of the mean (t-distribution)."""
    n = len(values)
    if n < 2:
        return float("nan")
    return float(stats.t.ppf(0.975, n - 1) * values.std(ddof=1) / np.sqrt(n))


def qc_screen(df: pd.DataFrame) -> pd.DataFrame:
    """Per-respondent QC verdicts. Returns one row per respondent."""
    rows = []
    for rid, g in df.groupby("respondent_id"):
        fully_rated = g[DIMS].notna().all(axis=1).sum()
        drop_completion = fully_rated < 10

        # Repeat-pair consistency: second showing vs first showing of the
        # same (source, system) pair within this respondent.
        seconds = g[g.is_repeat_second_showing]
        diffs = []
        for _, row in seconds.iterrows():
            first = g[
                (g.source_id == row.source_id)
                & (g.system_id == row.system_id)
                & ~g.is_repeat_second_showing
            ]
            if first.empty:
                continue
            first = first.iloc[0]
            for d in DIMS:
                if pd.notna(row[d]) and pd.notna(first[d]):
                    diffs.append(abs(row[d] - first[d]))
        repeat_mad = float(np.mean(diffs)) if diffs else float("nan")
        drop_repeat = bool(diffs) and repeat_mad > 25

        # Bad-ref check (adapted, see module docstring). Target dim: meaning.
        real = g[~g.is_bad_ref & ~g.is_repeat_second_showing]
        real_meaning_mean = real["meaning"].mean()
        bad = g[g.is_bad_ref]["meaning"].dropna()
        if len(bad) == 0 or pd.isna(real_meaning_mean):
            badref_status = "unscoreable"
            flag_badref = False
        else:
            misses = int((bad >= real_meaning_mean).sum())
            flag_badref = len(bad) >= 2 and misses >= 2
            badref_status = f"{misses}/{len(bad)} misses"

        verdict = "drop" if (drop_completion or drop_repeat) else ("flag" if flag_badref else "pass")
        reasons = []
        if drop_completion:
            reasons.append(f"only {fully_rated}/20 items fully rated (<10)")
        if drop_repeat:
            reasons.append(f"repeat-pair mean |diff| {repeat_mad:.1f} > 25")
        if flag_badref:
            reasons.append(f"both bad-refs scored >= own real-item meaning mean ({real_meaning_mean:.0f})")
        rows.append(
            {
                "respondent_id": rid,
                "eligibility": g["eligibility"].iloc[0],
                "items_fully_rated": fully_rated,
                "repeat_pair_mean_abs_diff": round(repeat_mad, 1) if diffs else "",
                "badref_meaning": badref_status,
                "verdict": verdict,
                "reasons": "; ".join(reasons),
            }
        )
    return pd.DataFrame(rows)


def zscore_per_annotator(df: pd.DataFrame) -> pd.DataFrame:
    """Add z_<dim> columns: each annotator's ratings standardised by their own
    mean/SD pooled across all rated cells (all 3 dims, QC items included),
    per PLAN section 4 ("across all items they rated")."""
    df = df.copy()
    for d in DIMS:
        df[f"z_{d}"] = np.nan
    for rid, g in df.groupby("respondent_id"):
        pooled = g[DIMS].to_numpy(dtype=float).ravel()
        pooled = pooled[~np.isnan(pooled)]
        mu, sd = pooled.mean(), pooled.std(ddof=1)
        if sd == 0:
            continue
        idx = df.respondent_id == rid
        for d in DIMS:
            df.loc[idx, f"z_{d}"] = (df.loc[idx, d] - mu) / sd
    return df


def aggregate(df_real: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-(source, system) item table and per-system summary."""
    item_rows = []
    for (src, sysid), g in df_real.groupby(["source_id", "system_id"]):
        row = {"source_id": src, "system_id": sysid}
        for d in DIMS:
            vals = g[d].dropna().to_numpy(dtype=float)
            zvals = g[f"z_{d}"].dropna().to_numpy(dtype=float)
            row[f"n_{d}"] = len(vals)
            row[f"raw_{d}"] = round(vals.mean(), 1) if len(vals) else np.nan
            row[f"z_{d}"] = round(zvals.mean(), 3) if len(zvals) else np.nan
            row[f"z_{d}_ci95"] = round(ci95_half_width(zvals), 3) if len(zvals) >= 2 else np.nan
        zs = [row[f"z_{d}"] for d in DIMS if pd.notna(row[f"z_{d}"])]
        row["z_composite"] = round(float(np.mean(zs)), 3) if zs else np.nan
        item_rows.append(row)
    items = pd.DataFrame(item_rows).sort_values(["system_id", "source_id"])

    sys_rows = []
    for sysid, g in df_real.groupby("system_id"):
        row = {"system_id": sysid}
        for d in DIMS:
            vals = g[d].dropna().to_numpy(dtype=float)
            zvals = g[f"z_{d}"].dropna().to_numpy(dtype=float)
            row[f"n_{d}"] = len(vals)
            row[f"raw_{d}"] = round(vals.mean(), 1)
            row[f"z_{d}"] = round(zvals.mean(), 3)
            row[f"z_{d}_ci95"] = round(ci95_half_width(zvals), 3)
        row["z_composite"] = round(
            float(np.mean([row[f"z_{d}"] for d in DIMS])), 3
        )
        sys_rows.append(row)
    summary = pd.DataFrame(sys_rows).set_index("system_id").loc[SYSTEMS].reset_index()
    return items, summary


def paired_comparison(items: pd.DataFrame, sys_a: str, sys_b: str) -> list[dict]:
    """Paired-by-source tests of sys_a vs sys_b on per-source z-means."""
    out = []
    a = items[items.system_id == sys_a].set_index("source_id")
    b = items[items.system_id == sys_b].set_index("source_id")
    common = a.index.intersection(b.index)
    for d in DIMS + ["composite"]:
        col = "z_composite" if d == "composite" else f"z_{d}"
        pairs = pd.DataFrame({"a": a.loc[common, col], "b": b.loc[common, col]}).dropna()
        diff = pairs.a - pairs.b
        t_stat, t_p = stats.ttest_rel(pairs.a, pairs.b)
        try:
            w_stat, w_p = stats.wilcoxon(pairs.a, pairs.b)
        except ValueError:
            w_stat, w_p = np.nan, np.nan
        out.append(
            {
                "comparison": f"{sys_a} vs {sys_b}",
                "dimension": d,
                "n_sources": len(pairs),
                "mean_z_diff": round(diff.mean(), 3),
                "t_p": round(float(t_p), 4),
                "wilcoxon_p": round(float(w_p), 4) if not np.isnan(w_p) else "",
            }
        )
    return out


def make_charts(summary: pd.DataFrame, df: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Chart 1: raw means with 95% CI, per dimension by system
    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.25
    x = np.arange(len(DIMS))
    real = df[~df.is_bad_ref]
    for i, sysid in enumerate(SYSTEMS):
        g = real[real.system_id == sysid]
        means, errs = [], []
        for d in DIMS:
            vals = g[d].dropna().to_numpy(dtype=float)
            means.append(vals.mean())
            errs.append(ci95_half_width(vals))
        ax.bar(x + (i - 1) * width, means, width, yerr=errs, capsize=3, label=SYSTEM_LABELS[sysid])
    ax.set_xticks(x)
    ax.set_xticklabels([d.capitalize() for d in DIMS])
    ax.set_ylabel("Raw rating (0-100)")
    ax.set_ylim(0, 100)
    ax.set_title("Direct Assessment ratings by system (mean, 95% CI)")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "ratings_by_system.png", dpi=150)
    plt.close(fig)

    # Chart 2: repeat-pair consistency scatter (first vs second showing)
    fig, ax = plt.subplots(figsize=(5, 5))
    firsts, seconds = [], []
    for rid, g in df.groupby("respondent_id"):
        for _, row in g[g.is_repeat_second_showing].iterrows():
            first = g[
                (g.source_id == row.source_id)
                & (g.system_id == row.system_id)
                & ~g.is_repeat_second_showing
            ]
            if first.empty:
                continue
            first = first.iloc[0]
            for d in DIMS:
                if pd.notna(row[d]) and pd.notna(first[d]):
                    firsts.append(first[d])
                    seconds.append(row[d])
    ax.scatter(firsts, seconds, alpha=0.4, s=18)
    ax.plot([0, 100], [0, 100], "k--", lw=0.8)
    ax.fill_between([0, 100], [-25, 75], [25, 125], alpha=0.08, color="green")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel("First showing rating")
    ax.set_ylabel("Second showing rating")
    r = np.corrcoef(firsts, seconds)[0, 1]
    ax.set_title(f"Repeat-pair consistency (r = {r:.2f}, n = {len(firsts)})")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "repeat_pair_consistency.png", dpi=150)
    plt.close(fig)


def fmt_md_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def main() -> int:
    df = pd.read_csv(RESULTS_DIR / "responses_long.csv")
    for d in DIMS:
        df[d] = pd.to_numeric(df[d], errors="coerce")
    for col in ("is_bad_ref", "is_repeat_second_showing"):
        df[col] = df[col].astype(str).str.lower() == "true"

    qc = qc_screen(df)
    qc.to_csv(RESULTS_DIR / "qc_report.csv", index=False)
    dropped = qc[qc.verdict == "drop"].respondent_id.tolist()
    flagged = qc[qc.verdict == "flag"].respondent_id.tolist()
    survivors = qc[qc.verdict != "drop"].respondent_id.tolist()
    print(f"QC: {len(survivors)} kept, dropped {dropped or 'none'}, flagged {flagged or 'none'}")

    kept = zscore_per_annotator(df[df.respondent_id.isin(survivors)])
    # z-score sanity: per-annotator pooled mean ~0, SD ~1
    for rid, g in kept.groupby("respondent_id"):
        pooled = g[[f"z_{d}" for d in DIMS]].to_numpy(dtype=float).ravel()
        pooled = pooled[~np.isnan(pooled)]
        assert abs(pooled.mean()) < 1e-9 and abs(pooled.std(ddof=1) - 1) < 1e-9, rid

    real = kept[~kept.is_bad_ref & ~kept.is_repeat_second_showing]
    items, summary = aggregate(real)
    items.to_csv(RESULTS_DIR / "item_scores.csv", index=False)
    summary.to_csv(RESULTS_DIR / "summary_by_system.csv", index=False)

    # Coverage check: every (source, system) pair >= 3 ratings on every dim
    min_n = items[[f"n_{d}" for d in DIMS]].min().min()
    n_pairs = len(items)
    print(f"Coverage: {n_pairs} (source, system) pairs, min ratings per pair/dim = {min_n}")

    comparisons = paired_comparison(items, "8b_agentic", "8b_monolithic") + paired_comparison(
        items, "8b_agentic", "70b_agentic"
    )
    comp_df = pd.DataFrame(comparisons)
    comp_df.to_csv(RESULTS_DIR / "rq_comparisons.csv", index=False)

    # Sensitivity: same summary excluding bad-ref-flagged respondents
    if flagged:
        strict = real[~real.respondent_id.isin(flagged)]
        _, summary_strict = aggregate(strict)
    else:
        summary_strict = None

    make_charts(summary, kept)

    # Eligibility split
    elig_counts = (
        df.groupby("respondent_id")["eligibility"].first().value_counts().to_dict()
    )

    md = ["# Survey preliminary results (generated " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M") + ")", ""]
    md += [
        f"Respondents merged: {df.respondent_id.nunique()}. QC kept: {len(survivors)}; "
        f"dropped: {dropped if dropped else 'none'}; flagged (bad-ref, kept in headline): "
        f"{flagged if flagged else 'none'}.",
        "",
        f"Eligibility mix: {elig_counts}",
        "",
        f"Coverage: every (source, system) pair has >= {min_n} ratings per dimension "
        f"({n_pairs} pairs).",
        "",
        "## Ratings by system",
        "",
        fmt_md_table(summary[["system_id"] + [f"raw_{d}" for d in DIMS] + [f"z_{d}" for d in DIMS] + ["z_composite"]]),
        "",
        "## RQ comparisons (paired by source, z-scores)",
        "",
        fmt_md_table(comp_df),
        "",
    ]
    if summary_strict is not None:
        md += [
            "## Sensitivity: excluding bad-ref-flagged respondents",
            "",
            fmt_md_table(summary_strict[["system_id"] + [f"raw_{d}" for d in DIMS] + ["z_composite"]]),
            "",
        ]
    md += [
        "## QC report",
        "",
        fmt_md_table(qc),
        "",
        "Charts: `ratings_by_system.png`, `repeat_pair_consistency.png`.",
    ]
    (RESULTS_DIR / "RESULTS.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote RESULTS.md, item_scores.csv, summary_by_system.csv, rq_comparisons.csv, qc_report.csv")
    print()
    print(summary.to_string(index=False))
    print()
    print(comp_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
