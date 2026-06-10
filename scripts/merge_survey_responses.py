#!/usr/bin/env python3
"""Merge MS Forms survey exports into one tidy long-format CSV.

Reads the per-respondent xlsx exports from the vault
(`1 - Thesis/Survey/respondents/UPM Idiom Replacement Evaluation #N(1-1).xlsx`),
joins each form's 20 item slots to the deterministic assignment ledger
(`Survey/respondent_assignments/respondent_NN.csv`), and writes
`Survey/results/responses_long.csv`.

Layout of each xlsx (verified 2026-06-03): a header row + one data row,
87 columns: 7 metadata columns (ID, start time, completion time, email,
name, eligibility, consent) followed by 20 blocks of 4 columns
(grammaticality, meaning, simplicity, optional free-text), in form order.

Run:
    uv run --with pandas,openpyxl python scripts/merge_survey_responses.py
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

SURVEY_DIR = Path.home() / "Documents/Obsidian Vault/1 - Thesis/Survey"
RESPONDENTS_DIR = SURVEY_DIR / "respondents"
ASSIGNMENTS_DIR = SURVEY_DIR / "respondent_assignments"
RESULTS_DIR = SURVEY_DIR / "results"

N_ITEMS = 20
META_COLS = 7  # ID, start, completion, email, name, eligibility, consent

OUT_FIELDS = [
    "respondent_id",
    "form_position",
    "source_id",
    "system_id",
    "is_bad_ref",
    "is_repeat_second_showing",
    "grammaticality",
    "meaning",
    "simplicity",
    "freetext",
    "eligibility",
    "completion_minutes",
]


def parse_rating(value) -> str:
    """Normalise a rating cell: int 0-100 or empty string for missing."""
    if value is None or value == "":
        return ""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return ""
    if not 0 <= n <= 100:
        print(f"  WARNING: rating out of range: {value!r}")
    return str(int(round(n)))


def load_assignment(respondent_id: int) -> list[dict]:
    path = ASSIGNMENTS_DIR / f"respondent_{respondent_id:02d}.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == N_ITEMS, f"{path.name}: expected {N_ITEMS} rows, got {len(rows)}"
    return rows


def main() -> int:
    xlsx_files = sorted(RESPONDENTS_DIR.glob("*.xlsx"))
    if not xlsx_files:
        print(f"No xlsx files found in {RESPONDENTS_DIR}")
        return 1

    RESULTS_DIR.mkdir(exist_ok=True)
    out_rows: list[dict] = []
    present: list[int] = []
    blank_counts: dict[int, int] = {}
    freetext_count = 0

    for path in xlsx_files:
        m = re.search(r"#(\d+)", path.name)
        if not m:
            print(f"  SKIP (no form number in name): {path.name}")
            continue
        rid = int(m.group(1))
        present.append(rid)

        # NOTE: MS Forms exports carry a broken <dimension> tag (A1:A1), which
        # makes read_only mode see an empty sheet. Full load recalculates it.
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        assert len(rows) >= 2, f"{path.name}: no data row"
        data = rows[1]
        n_cols = META_COLS + 4 * N_ITEMS
        assert len(data) >= n_cols, f"{path.name}: {len(data)} cols, expected {n_cols}"

        start_t, end_t = data[1], data[2]
        completion_minutes = ""
        if isinstance(start_t, datetime) and isinstance(end_t, datetime):
            completion_minutes = f"{(end_t - start_t).total_seconds() / 60:.1f}"
        elif isinstance(start_t, (int, float)) and isinstance(end_t, (int, float)):
            completion_minutes = f"{(end_t - start_t) * 24 * 60:.1f}"
        eligibility = data[5] or ""

        assignment = load_assignment(rid)
        blanks = 0
        for k in range(N_ITEMS):
            base = META_COLS + 4 * k
            gram = parse_rating(data[base])
            mean = parse_rating(data[base + 1])
            simp = parse_rating(data[base + 2])
            text = (data[base + 3] or "").strip() if isinstance(data[base + 3], str) else ""
            blanks += [gram, mean, simp].count("")
            if text:
                freetext_count += 1
            a = assignment[k]
            assert int(a["form_position"]) == k + 1, f"{path.name}: position mismatch at {k+1}"
            out_rows.append(
                {
                    "respondent_id": rid,
                    "form_position": k + 1,
                    "source_id": a["source_id"],
                    "system_id": a["system_id"],
                    "is_bad_ref": a["is_bad_ref"],
                    "is_repeat_second_showing": a["is_repeat_second_showing"],
                    "grammaticality": gram,
                    "meaning": mean,
                    "simplicity": simp,
                    "freetext": text,
                    "eligibility": eligibility,
                    "completion_minutes": completion_minutes,
                }
            )
        blank_counts[rid] = blanks

    out_path = RESULTS_DIR / "responses_long.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        w.writerows(out_rows)

    # Reconciliation report
    present_set = set(present)
    expected_completed = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 20, 22, 23, 24, 25, 26, 27, 28}
    print(f"Merged {len(present)} forms -> {len(out_rows)} rows -> {out_path}")
    print(f"Forms present: {sorted(present_set)}")
    missing = expected_completed - present_set
    extra = present_set - expected_completed
    if missing:
        print(f"Listed completed on 2026-06-01 but NO export file: {sorted(missing)}")
    if extra:
        print(f"Export file present but not in 2026-06-01 completed list: {sorted(extra)}")
    print(f"Free-text comments collected: {freetext_count}")
    print("Blank ratings per respondent (of 60 cells):")
    for rid in sorted(blank_counts):
        if blank_counts[rid]:
            print(f"  #{rid}: {blank_counts[rid]} blank")
    if not any(blank_counts.values()):
        print("  none: every respondent rated all 60 cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
