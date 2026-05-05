"""Fire the open-weights re-run sweep for Steps 21f / 21g, plus the survey
condition runs for Steps 22c / 22e.

Runs are dispatched serially to the local API; the API itself parallelises
inside each run via the OpenRouter/vLLM concurrency cap. Serial here just
keeps the cluster from being slammed by overlapping runs while a single
ngrok-fronted vLLM is the only backend.

Steps covered:

- 21f (detection):              4 runs per model — VU + SemEval, v1, T=0, limit=200
- 21g (detect-then-replace):    4 runs per model — VU + SemEval, v1+v2, T=0, limit=200
- 22c (monolithic survey-pool): 1 run on Llama-3.1-8B over the 30 selected sources
- 22e (agentic 70B survey-pool): 1 run on Llama-3.3-70B-AWQ over the 30 selected sources

Usage:
    # Once the API is pointing at the cluster (ngrok URL set in
    # set-values-and-secrets, container respawned):
    uv run python scripts/run_open_weights_sweep.py \\
        --api http://localhost:3030 \\
        --model vllm:meta-llama/Llama-3.1-8B-Instruct \\
        --suite 21f-21g

    # Step 22c/22e takes a CSV of selected sources and only fires runs over
    # those example_ids. The runs filter is currently a hint — the API does
    # not yet support per-example filtering, so the script flags the gap and
    # prints a follow-up TODO.
    uv run python scripts/run_open_weights_sweep.py \\
        --api http://localhost:3030 \\
        --model vllm:meta-llama/Llama-3.1-8B-Instruct \\
        --suite 22c

The script polls each run until it reaches a terminal status, logs the run_id
and final metrics line, and exits non-zero if any run fails.
"""

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class RunSpec:
    label: str
    dataset: str
    phenomenon: str
    task_type: str
    prompt_version: str
    temperature: float = 0.0
    limit: Optional[int] = 200


def http_post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())


def http_get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=180) as resp:
        return json.loads(resp.read())


def fire(api: str, model_name: str, spec: RunSpec) -> str:
    body = {
        "dataset": spec.dataset,
        "phenomenon": spec.phenomenon,
        "task_type": spec.task_type,
        "model_name": model_name,
        "temperature": spec.temperature,
        "prompt_version": spec.prompt_version,
        "limit": spec.limit,
    }
    print(f"  POST /runs    {spec.label}")
    resp = http_post(f"{api}/runs", body)
    run_id = resp["run_id"]
    print(f"  -> run_id={run_id}  status={resp.get('status')}")
    return run_id


def poll(api: str, run_id: str, *, interval_s: float = 5.0, timeout_s: float = 7200.0) -> dict:
    start = time.time()
    while time.time() - start < timeout_s:
        run = http_get(f"{api}/runs/{run_id}")
        status = run.get("status")
        if status in {"completed", "failed"}:
            return run
        time.sleep(interval_s)
    raise TimeoutError(f"Run {run_id} did not finish within {timeout_s:.0f}s")


def fetch_metrics(api: str, run_id: str) -> dict:
    try:
        http_post(f"{api}/runs/{run_id}/evaluate", {})
    except urllib.error.HTTPError as e:
        print(f"  /evaluate non-fatal: {e}")
    try:
        return http_get(f"{api}/runs/{run_id}/metrics")
    except urllib.error.HTTPError as e:
        return {"error": str(e)}


def suite_21f_21g(limit: int) -> list[RunSpec]:
    """Step 17 + Step 20 re-runs on a single open-weights model."""
    return [
        # 21f — detection at v1, T=0, limit=200
        RunSpec("21f.vu.metaphor.detect.v1",      "vu_amsterdam", "metaphor", "detection",            "v1", limit=limit),
        RunSpec("21f.semeval.idiom.detect.v1",    "semeval",      "idiom",    "detection",            "v1", limit=limit),
        # 21g — detect-then-replace at v1 and v2
        RunSpec("21g.vu.metaphor.dtr.v1",         "vu_amsterdam", "metaphor", "detect_then_replace",  "v1", limit=limit),
        RunSpec("21g.semeval.idiom.dtr.v1",       "semeval",      "idiom",    "detect_then_replace",  "v1", limit=limit),
        RunSpec("21g.vu.metaphor.dtr.v2",         "vu_amsterdam", "metaphor", "detect_then_replace",  "v2", limit=limit),
        RunSpec("21g.semeval.idiom.dtr.v2",       "semeval",      "idiom",    "detect_then_replace",  "v2", limit=limit),
    ]


def suite_22c() -> list[RunSpec]:
    """Step 22c — Llama-3.1-8B monolithic on SemEval idioms."""
    return [
        RunSpec("22c.semeval.idiom.monolithic.v1", "semeval", "idiom", "monolithic_replace", "v1", limit=200),
    ]


def suite_22e() -> list[RunSpec]:
    """Step 22e — Llama-3.3-70B-AWQ agentic detect-then-replace on SemEval idioms."""
    return [
        RunSpec("22e.semeval.idiom.dtr.v2", "semeval", "idiom", "detect_then_replace", "v2", limit=200),
    ]


def fmt_metrics(metrics: dict) -> str:
    if not metrics or "metrics" not in metrics:
        return json.dumps(metrics)
    items = sorted(metrics["metrics"].items())
    return ", ".join(f"{k}={v:.3f}" for k, v in items)


def run_suite(api: str, model_name: str, specs: Iterable[RunSpec]) -> int:
    failed = 0
    for spec in specs:
        print(f"\n--- {spec.label} ({model_name}) ---")
        try:
            run_id = fire(api, model_name, spec)
            run = poll(api, run_id)
            stats = run.get("stats", {})
            print(f"  status={run.get('status')}  completed={stats.get('completed')}  failed={stats.get('failed')}  total={stats.get('total_examples')}")
            metrics = fetch_metrics(api, run_id)
            print(f"  metrics: {fmt_metrics(metrics)}")
            if run.get("status") == "failed":
                failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--api", default="http://localhost:3030", help="Base URL of the e2r-adaptation API")
    parser.add_argument("--model", required=True, help="Model identifier (e.g. vllm:meta-llama/Llama-3.1-8B-Instruct)")
    parser.add_argument(
        "--suite",
        required=True,
        choices=["21f-21g", "22c", "22e"],
        help="Which run sweep to fire",
    )
    parser.add_argument("--limit", type=int, default=200, help="Examples per run for 21f-21g")
    args = parser.parse_args()

    if args.suite == "21f-21g":
        specs = suite_21f_21g(args.limit)
    elif args.suite == "22c":
        specs = suite_22c()
        if "8B" not in args.model and "8b" not in args.model.lower():
            print(f"WARN: suite 22c expects an 8B model; got {args.model!r}", file=sys.stderr)
    elif args.suite == "22e":
        specs = suite_22e()
        if "70" not in args.model:
            print(f"WARN: suite 22e expects a 70B model; got {args.model!r}", file=sys.stderr)
    else:
        raise SystemExit(f"unknown suite: {args.suite}")

    print(f"API:   {args.api}")
    print(f"Model: {args.model}")
    print(f"Suite: {args.suite} ({len(specs)} run{'s' if len(specs) != 1 else ''})")
    failed = run_suite(args.api, args.model, specs)
    if failed:
        print(f"\n{failed} run(s) failed", file=sys.stderr)
        return 1
    print("\nAll runs completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
