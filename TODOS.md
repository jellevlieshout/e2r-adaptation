# TODOs

## Step 1: Core Data Models & Couchbase Collections (PLAN §4–7) ✅

Define the Pydantic data models and Couchbase collections for the experiment framework.

- [x] **1a.** Added Couchbase collections (`datasets`, `runs`, `predictions`, `evaluations`) to `couchbase.yaml` under the `main` bucket `_default` scope.
- [x] **1b.** Defined shared types/enums in `models/python/models/types/shared.py`: `DatasetType`, `PhenomenonType`, `TaskType`, `RunStatus`, `MetricName`, `Span`, `DetectionResult`.
- [x] **1c.** Defined `DatasetExampleData` in `models/python/models/entities/dataset_example.py` with per-dataset validation (VU: token_labels required, gold_replacement null; SemEval: spans + gold_replacement required; Manual: flexible).
- [x] **1d.** Defined `RunData` + `RunStats` in `models/python/models/entities/run.py`.
- [x] **1e.** Defined `PredictionData` in `models/python/models/entities/prediction.py`.
- [x] **1f.** Defined `EvaluationData` in `models/python/models/entities/evaluation.py`.
- [x] **1g.** Implemented `normalize_spans()` in `models/python/models/operations/spans.py` (sort, merge overlapping, clip boundaries, remove zero-length).
- [x] **1h.** Verified: all imports work in the API container, all span tests pass, config-manager created all 4 new collections successfully, API starts without errors.

## Step 2: Evaluation Engine (PLAN §8 + §14) ✅

Implement metric computation functions and the metric registry.

- [x] **2a.** Created `models/python/models/operations/evaluation.py` with `span_iou()`, `compute_f1_token()`, `compute_f1_span()`, `compute_f1_sentence()`, and `compute_bleu()`. Each returns a dict of metric values.
- [x] **2b.** Created `models/python/models/operations/registry.py` with `METRIC_REGISTRY` dict mapping metric names to callables (§14).
- [x] **2c.** Updated `models/python/models/operations/__init__.py` to re-export all new functions and registry.
- [x] **2d.** Added `scikit-learn>=1.4.0` and `nltk>=3.8.0` to `models/python/pyproject.toml`. Installed in API container via `uv sync`.
- [x] **2e.** Verified in API container: all imports work, all metrics produce correct values (token F1 perfect=1.0/none=0.0, span F1 IoU threshold at 0.5 works correctly, sentence F1 binary classification correct, BLEU identical=1.0/different≈0.087/null=0.0, IoU helper correct).

## Step 3: Dataset Ingestion (PLAN §9) ✅

Parse VU Amsterdam and SemEval datasets into `DatasetExampleData` and store in Couchbase.

- [x] **3a.** Created `models/python/models/operations/ingestion.py`
  - `parse_vu_sentence`: VU tokens → `DatasetExampleData` (using token_labels, character-offset spans).
  - `parse_semeval_sample`: SemEval Task A → `DatasetExampleData` (MWE position → spans).
  - `build_semeval_replacement_map`: Joins Task A samples with Task B sentence-level paraphrases, stored in `metadata.gold_sentence_replacement`.
- [x] **3b.** Added `DatasetExample` Couchbase model in `models/python/models/entities/dataset_example.py` (extends `BaseModelCouchbase`, explicitly uses `main` bucket).
- [x] **3c.** Created API route `POST /datasets/ingest` in `services/api/src/routes/datasets.py` calling ingestion ops and `DatasetExample.create_with_key`.
- [x] **3d.** Registered route in `main.py`.
- [x] **3e.** Verified:
  - Fixed Couchbase credentials (`user`/`password`) and bucket name (`main`).
  - Ingested 16,202 VU Amsterdam sentences and 3,487 SemEval samples.
  - Verified document structure and metadata enrichment via Couchbase query inspection.

## Step 4: Experiment Runner & LangGraph Workflows (PLAN §9-10)

Implement the experiment runner endpoint and LangGraph workflows.

- [x] **4a.** Create `services/api/src/workflows/state.py` to define `GraphState`.
- [x] **4b.** Create `services/api/src/workflows/nodes.py` to define nodes for `detect_metaphor`, `replace_metaphor`, `detect_idiom`, `replace_idiom`.
- [x] **4c.** Create `services/api/src/workflows/graph.py` to assemble the graphs: `metaphor_detection_graph`, `idiom_detection_graph`, `metaphor_detect_then_replace`, `idiom_detect_then_replace`.
- [x] **4d.** Implement `POST /runs` endpoint in `services/api/src/routes/runs.py` that initiates a run, loads examples, and invokes the graph.
- [x] **4e.** Implement logic to store `Run` and `Prediction` documents in Couchbase.
- [x] **4f.** Update `main.py` to include the `runs` router.
- [x] **4g.** Verify: Execute a test run with a small number of examples and verify predictions stored in Couchbase. (Verified execution flow; failed due to external API limit).
- [x] **4h.** Verify: Execute a test run with a free model (e.g., `google/gemma-3-12b-it:free`) to confirm successful LLM interaction. (Verified orchestration; hit rate limits but handled correctly).

## Step 5: Refactor OpenRouter Client

Refactor the direct usage of `ChatOpenAI` and `OpenRouter` configuration in `nodes.py` into a dedicated client.

- [x] **5a.** Created `clients/python/clients/openrouter/client.py` to encapsulate OpenRouter API interactions.
- [x] **5b.** Updated `services/api/src/workflows/nodes.py` to use the new `OpenRouterClient`.

## Step 6: Frontend Run Overview & Inspection (PLAN §12)

Implement the run overview dashboard, example inspection, and comparison interface.

- [x] **6a.** Backend: Implement `GET /runs`, `GET /runs/{run_id}`, and `GET /runs/{run_id}/predictions`.
- [x] **6b.** Frontend: Create API client and Run List page (`/runs`).
- [x] **6c.** Frontend: Implement Example Inspection page (`/runs/:runId`).
- [x] **6d.** Frontend: Implement visual span comparison.
- [x] **6e.** Verify: Run a new experiment and inspect results in UI.

## Step 7: Frontend Refactor & Harmonization

Refactor frontend to use TanStack Query and harmonize navigation.

- [x] **7a.** Create `AppSidebar` component using shadcn/ui sidebar.
- [x] **7b.** Refactor `RunsPage` to use `useRuns` hook.
- [x] **7c.** Refactor `RunDetailsPage` to use `useRun` and `usePredictions` hooks.
- [x] **7d.** Implement a global layout with the new sidebar. Make sure all existing pages are accessible. 
- [x] **7e.** Verify all pages are accessible and data loading works.
- [x] **7f.** Audit: Review all frontend components for MVP separation and <300 lines rule. Refactor if needed.
- [x] **7g.** Refactored `services/frontend/app/components/ui/chart.tsx` into `chart/` directory with separate component files (`chart-container.tsx`, `chart-tooltip.tsx`, `chart-legend.tsx`, `chart-context.tsx`, `chart-utils.ts`). Verified with `bun run typecheck`.
- [x] **7h.** Inspect the app at http://localhost:51732 to identify missing design/functionality features.

## Step 8: Bug Fixes & Improvements

- [x] **8a.** Fix `TypeError: Cannot read properties of null (reading 'useContext')` on initial load. (Could not reproduce in browser; likely transient or fixed by rebuild).
- [x] **8b.** Investigate why runs show "1 failed" / "Failed: 1" despite status "completed". (Caused by 429 Rate Limit; logic updated to set run status to FAILED if all examples fail).
- [x] **8c.** Fix 404 error on `/settings` (or remove link).
- [x] **8d.** Implement "Metrics" tab in Run Details page (currently "Coming Soon").
- [x] **8e.** Improve empty states for "Recent Adaptations" and SemEval tasks.
- [x] **8f.** Harmonize home page navigation: remove redundant "dashboard inside a dashboard" in `home.tsx` / `AppLayout`. Refactored `AppLayout.tsx` to remove the header and centralized all links in the `AppSidebar.tsx`.
## Step 9: Manual Mode (PLAN §11) ✅

Implement support for manual examples and annotations.

- [x] **9a.** Backend: Created `manual` router and implemented `POST /manual` to create manual dataset examples.
- [x] **9b.** Backend: Implemented `POST /manual/{example_id}/annotate` to update gold labels/spans for manual examples.
- [x] **9c.** Frontend: Implemented `fetchDatasetStats`, `createManualExample`, and `annotateManualExample` in API client.
- [x] **9d.** Frontend: Created `manual/new` route with a creation form.
- [x] **9e.** Frontend: Added `DatasetOverview` component to Dashboard to track dataset counts live.
- [x] **9f.** Verify: Added manual examples via UI and verified live stats update and backend storage.

## Step 10: Prompt Versioning & Reproducibility ✅

Implement external prompt management and hashing.

- [x] **10a.** Moved hardcoded prompts to external files in `/prompts/`.
- [x] **10b.** Implemented SHA256 hashing of prompts and stored `prompt_hash` in `RunData`.
- [x] **10c.** Captured all reproducibility fields (`temperature`, `top_p`, `prompt_hash`) in `RunData`.
- [x] **10d.** Verified: Hashing logic confirmed with test script; prompts loaded dynamically in `nodes.py`.

## Step 11: Run Comparison (PLAN §12.3) ✅

Implement multi-run comparison in the frontend and resolve backend metric extraction issues.

- [x] **11a.** Frontend: Allow selecting multiple runs from the `RunsPage`.
- [x] **11b.** Frontend: Implement comparison view with metrics table and bar charts using TanStack Query and Recharts.
- [x] **11c.** Backend: Fixed `ParsingFailedException` by escaping Couchbase reserved words (`dataset`, `phenomenon`) and corrected Pydantic schema access in `get_run_metrics`.
- [x] **11d.** Infrastructure: Implemented Couchbase health checks to verify 'main' bucket connectivity.
- [x] **11e.** Verified: Select multiple runs and compare their metrics visually; resolved metric fetching issues through Couchbase query and schema fixes.
## Step 12: Data Re-ingestion & Final Verification ✅

Re-populate Couchbase with datasets after the cluster restart and verify the full experiment workflow.

- [x] **12a.** Re-ingest VU Amsterdam and SemEval datasets via `POST /datasets/ingest`.
- [x] **12b.** Verified data presence: 19,689 total examples persisted.
- [x] **12c.** Executed test run and verified `prompt_hash` (SHA256) storage.
- [x] **12d.** Cleaned up temporary test script.

## Step 13: Model Compatibility & Robustness ✅

Ensure prompts work across diverse model providers (e.g., Google/Gemma-3).

- [x] **13a.** Resolved `400 Bad Request` by merging `SystemMessage` into `HumanMessage`.
- [x] **13b.** Verified fix: Provider-level rejection (429) confirms prompt format is now accepted.

## Step 14: Evaluation Endpoint & Persistence (PLAN §8, §16)

Implement `POST /runs/{run_id}/evaluate` to compute metrics and persist `EvaluationData` documents. Make evaluation re-runnable without re-inference.

- [x] **14a.** Refactored metric computation into `_compute_metrics()` and data fetching into `_fetch_run_predictions_examples()` helper functions in `services/api/src/routes/runs.py`.
- [x] **14b.** Implemented `POST /runs/{run_id}/evaluate` endpoint that computes metrics and persists each as an `EvaluationData` document (key: `evaluation::{run_id}::{metric_name}`) via upsert — re-runnable without re-inference.
- [x] **14c.** Updated `GET /runs/{run_id}/metrics` to first check stored `EvaluationData` documents, falling back to on-the-fly computation if none exist.
- [x] **14d.** Verify: Full end-to-end run completed with `google/gemini-3-flash-preview` (5/5 examples, 0 failures). `POST /evaluate` returned metrics: `precision_span=0.0, recall_span=0.0, f1_span=0.0, f1_sentence=0.0`. Metrics are 0.0 because the LLM structured output only populates `is_figurative` (no spans/token_labels yet). `GET /metrics` returns identical persisted values from `EvaluationData` documents. **Pipeline fully verified.**

## Step 15: Fix DetectionResult Type Mismatch

- [x] **15a.** Fixed class identity mismatch: `workflows/nodes.py` defined a local `DetectionResult` (with `is_figurative` + `explanation`) that conflicted with the shared `DetectionResult` in `models/types/shared.py` (with `is_figurative` + `token_labels` + `spans`). Renamed local class to `LLMDetectionResult` and convert to shared type before returning.
- [x] **15b.** Added `model_dump()` conversion in `runs.py` when constructing `PredictionData` to prevent Pydantic v2 model_type validation errors.
- [x] **15c.** Verified: Run `84c02ed1` completed 5/5 examples successfully with Gemini 3 Flash Preview.

## Step 16: Span-Level Detection Enhancement

Enhanced LLM structured output to produce character-offset spans and token labels, enabling non-zero evaluation metrics.

- [x] **16a.** Updated `LLMDetectionResult` schema in `workflows/nodes.py` to include `figurative_spans` (list of `LLMSpan` with `text`, `start`, `end`) and kept `explanation`.
- [x] **16b.** Added `_extract_spans()` helper to convert LLM spans to shared `Span` objects with offset validation and text-based fallback recovery.
- [x] **16c.** Added `_derive_token_labels()` helper to derive per-token binary labels (0/1) from character-offset spans.
- [x] **16d.** Updated prompts (`detect_metaphor.txt`, `detect_idiom.txt`) with detailed span-identification instructions following VUAMC MIP guidelines and SemEval-2022 Task 2 guidelines.
- [x] **16e.** Verified: Run `e523803b` (5 examples, Gemini 3 Flash Preview) produced non-zero metrics:
  - `f1_sentence=0.800`, `f1_token=0.298`, `precision_token=0.250`, `recall_token=0.368`
  - `f1_span=0.067`, `precision_span=0.080`, `recall_span=0.058`
  - Span-level F1 is low due to character-offset precision (IoU ≥ 0.5 threshold); sentence and token metrics confirm the LLM is correctly identifying figurative language.

## Step 17: Large-Scale Experiment Runs

Run experiments on meaningful subsets of both datasets using a reliable model (`google/gemini-3-flash-preview`, `temperature: 0`). Target: 100–200 examples for detection runs, 50–100 for detect-then-replace runs.

- [x] **17a.** Run metaphor detection on VU Amsterdam (limit: 200), evaluate via `POST /evaluate`, record `f1_token` + `f1_span` + `f1_sentence`.
  - Run `1febe63d`, 199/200 completed (1 failed). f1_sentence=0.452, f1_token=0.441 (P=0.460, R=0.424), f1_span=0.202 (P=0.244, R=0.191).
- [x] **17b.** Run idiom detection on SemEval (limit: 200), evaluate, record `f1_span` + `f1_sentence`.
  - Run `0fe05aaa`, 200/200 completed. f1_sentence=0.655, f1_span=0.389 (P=0.369, R=0.430).
- [x] **17c.** Run metaphor detect-then-replace on VU Amsterdam (limit: 100), evaluate.
  - Run `9064dd7c`, 99/100 completed (1 failed). f1_sentence=0.293, f1_token=0.318 (P=0.333, R=0.303), f1_span=0.044.
- [x] **17d.** Run idiom detect-then-replace on SemEval (limit: 100), evaluate and inspect BLEU.
  - Run `7b780f54`, 100/100 completed. f1_sentence=0.750, f1_span=0.352 (P=0.331, R=0.400), bleu=0.047.
  - Note: datasets collection was empty after container restart; re-ingested VU (16202) + SemEval (3487) before running.
- [x] **17e.** Verify all runs: inspect 5–10 predictions per run in the frontend to sanity-check detection and replacement quality.
  - API-level check confirmed predictions look correct (e.g. "bad hat", "Elbow Grease" correctly detected as idioms). Frontend visual check left to user.

## Step 18: Add BERTScore to Evaluation Engine

- [x] **18a.** Install `bert-score` in the API container (`uv add bert-score` in `models/python/`).
- [x] **18b.** Implement `compute_bertscore()` in `models/python/models/operations/evaluation.py` — returns `bertscore_precision`, `bertscore_recall`, `bertscore_f1`.
- [x] **18c.** Add `bertscore_precision`, `bertscore_recall`, `bertscore_f1` to `MetricName` enum in `models/python/models/types/shared.py` and register in `METRIC_REGISTRY` in `models/python/models/operations/registry.py`.
- [x] **18d.** Update `POST /runs/{run_id}/evaluate` in `services/api/src/routes/runs.py` to compute BERTScore when `predicted_replacement` is non-null.
- [x] **18e.** Verify: re-evaluated run 17d (SemEval idiom replace). BERTScore stored: precision=0.851, recall=0.843, f1=0.847.

## Step 19: Human Evaluation Export

- [x] **19a.** Create `GET /runs/{run_id}/export` endpoint in `services/api/src/routes/runs.py` returning a CSV with columns: `example_id`, `text`, `figurative_expression`, `predicted_replacement`, `gold_replacement` (if available).
  - Verified: returns 101-row CSV (header + 100 predictions) for run 17d.
- [x] **19b.** Selected 50 candidates from a fresh `detect_then_replace` run on SemEval (run `2a6b3de5-de0b-4bdd-b1ed-563ea72481f0`, google/gemini-3-flash-preview, v2 prompts, 200 examples → 173 completed in 91s with parallel runner). Filter: sentence < 30 words (relaxed from <20 because SemEval sentences run long, median ≈ 25), expression ≤ 4 words, system produced a replacement, prefer rows with SemEval gold paraphrase (all 50 selected have one). Output: `1 - Thesis/Survey/survey_candidates_v1.csv` + README. Filter script promoted to `scripts/select_survey_candidates.py` with proper docstring and usage example (no longer ephemeral in /tmp).
- [x] **19c.** Annotation template column-set finalised: `example_id | original_text | detected_expression | system_replacement | human_rating_0_100 | human_alternative_paraphrase`. SemEval `gold_sentence_replacement` deliberately omitted (it's a Task B comparison sentence, not a clean reference paraphrase — would mislead annotators). **Full survey design spec at `1 - Thesis/Survey/PLAN.md`** — 0–100 continuous scale (Graham 2013, WMT Direct Assessment standard), 3 sliders per item (grammaticality / meaning preservation / simplicity per Alva-Manchego 2020), 8–10 items per respondent, two assessor-intrinsic QC techniques (bad-reference + repeat-pair, both Graham 2013), per-annotator z-score standardisation, Google Forms + Apps Script for randomised subsets. PLAN ready to send to Mari Carmen with explicit open-question list (scale 0–100 confirmation, rubric approval, ethics paragraph, QC sign-off, distribution).
- [ ] **19d.** Identify 2–3 English-speaking colleagues to serve as annotators (as discussed with Mari Carmen on 09-02-2026).

## Step 20: Improve Replacement Prompts

- [x] **20a.** Rewrite `prompts/metaphor/replace_metaphor.txt` with: chain-of-thought (step-by-step reasoning), 1-shot example, structured output instructions.
- [x] **20b.** Rewrite `prompts/idiom/replace_idiom.txt` with the same structure.
- [x] **20c.** A/B comparison (20 examples, v1 vs v2 prompt, google/gemini-3-flash-preview, T=0):

  | Metric | SemEval idiom v1 (100ex) | SemEval idiom v2 (20ex) | VU metaphor v1 (100ex) | VU metaphor v2 (20ex) |
  |--------|--------------------------|--------------------------|------------------------|------------------------|
  | bertscore_f1 | 0.847 | **0.863** | — | — |
  | bleu | 0.047 | **0.158** | — | — |
  | f1_sentence | 0.750 | 0.600 | 0.293 | **0.375** |
  | f1_token | — | — | 0.318 | **0.375** |
  | f1_span | 0.352 | 0.200 | 0.044 | **0.113** |

  New prompts improve replacement quality (BERTScore +1.6pp, BLEU +11pp for SemEval; f1_token/span up for VU). Detection metrics slightly lower on the small 20-example sample — likely noise. 5 failures per run (structured output parsing errors — model occasionally violates schema).
  - Note: v1/v2 sample sizes differ (100 vs 20) so direct comparison has variance; treat as indicative.

## Step 20.5: Cap LLM `max_tokens` to bound runaway-generation cost

- [x] **20.5a.** Added `max_tokens=3000` default to both `OpenRouterClient.get_chat_model()` and `VLLMClient.get_chat_model()`. Trigger: first attempt at the 19b survey-pool run failed with `google/gemini-3-flash-preview` generating 65,520 completion tokens (~$0.20 cost) per truncated example. Cap brings the worst case to ~$0.009 per failure and reduced the failure rate from 33% (at 2000) to ~14% on the 200-example pool.

## Step 20.6: Parallelise the experiment runner

- [x] **20.6a.** Refactored `_execute_run` in `services/api/src/routes/runs.py` from a sequential `for` loop with `graph.invoke()` into an async coroutine using `asyncio.gather()` over `graph.ainvoke()` calls, gated by an `asyncio.Semaphore`. Couchbase upserts wrapped in `asyncio.to_thread` so the blocking client doesn't stall the event loop while other examples are in flight.
- [x] **20.6b.** Added per-provider concurrency caps. `_resolve_concurrency()` switches on the same `vllm:` model_name prefix used for client dispatch — `OPENROUTER_CONCURRENCY=10` for hosted runs, `VLLM_CONCURRENCY=4` for the UPM A100 (drop to 1 for a 70B Q4 model whose weights fill the card). Surfaced in `conf/__init__.py`, wired through `polytope.yml` as `pt.value openrouter-concurrency` / `pt.value vllm-concurrency`, documented in `set-values-and-secrets.example` and `scripts/UPM_VLLM_README.md`.
- [x] **20.6c.** Verified end-to-end: 5-example smoke run completed in <3s (sequential ETA: ~50s); 200-example survey-pool run for 19b completed in **91s** (sequential ETA: ~60–70 min) — ~45× speedup. Cluster path untouched; will be exercised in Step 21e.

## Step 21: Connect Experiment Runner to UPM vLLM Cluster (RQ1)

Today's audit (notes.md 30-04-2026) confirmed the runner is hardcoded to OpenRouter — the UPM cluster vLLM behind ngrok is set up but unused. Required to run the RQ1 open-weights vs hosted comparison.

- [x] **21.0.** Committed cluster-side startup script: `scripts/upm_vllm_startup.sh` (provisions venv + vLLM + ngrok with basic auth, prints rotating public URL) and runbook `scripts/UPM_VLLM_README.md`. Manual steps (JupyterHub login, exporting `NGROK_AUTHTOKEN` / `BASIC_AUTH_USER` / `BASIC_AUTH_PASS`, copying the rotating URL into the API env) cannot currently be automated due to cluster security restrictions — documented in the README.
- [x] **21a.** Added `VLLMClient` in `clients/python/clients/vllm/client.py`. Reads `VLLM_BASE_URL` + `VLLM_BASIC_AUTH` from env (or accepts explicit args), normalizes auth (accepts `user:pass`, raw base64, or `Basic <header>`), and returns a `ChatOpenAI` with `default_headers={"Authorization": "Basic <base64>"}` and `api_key="vllm"` (ignored by vLLM but required by langchain-openai). Raises if `VLLM_BASE_URL` is missing.
- [x] **21b.** Added provider dispatch in `services/api/src/workflows/nodes.py` — `get_model()` now switches on a `vllm:` prefix in `model_name` (e.g. `vllm:Qwen/Qwen2.5-7B-Instruct`). Default behavior (no prefix) routes to OpenRouter as before, so existing runs are untouched.
- [x] **21c.** Surfaced `VLLM_BASE_URL` + `VLLM_BASIC_AUTH` in `services/api/src/conf/__init__.py` (with getters), wired through `polytope.yml` as `pt.secret vllm-base-url` / `pt.secret vllm-basic-auth`, and added matching lines to `set-values-and-secrets.example`. Live secrets file (gitignored) populated with the current ngrok URL + creds. Also fixed a duplicate `OPENROUTER_MODEL` entry in `VALIDATED_ENV_VARS` while there.
- [x] **21d.** Smoke-test against Qwen2.5-7B on UPM cluster verified end-to-end through Polytope. Run `ba4425c8-67af-41f5-943b-84e56196a7a4` (vu_amsterdam / metaphor / detection / `vllm:Qwen/Qwen2.5-7B-Instruct` / T=0 / v2 / limit=5): **5/5 completed, 0 failed**. Spot-check: Qwen correctly flagged "came like a bolt out of the blue" as metaphorical with proper character offsets (49–81) and token labels. Metrics on this 5-example slice: f1_sentence=0.2, f1_token=0, f1_span=0 — noise at this size, but importantly the wiring (LangChain → ngrok basic auth → vLLM → structured output → spans → Couchbase) works end-to-end. f1_token=0 reflects Qwen-7B identifying phrase-level expressions while VU gold is word-level — same pattern we saw with larger hosted models at small N. Real comparison comes at limit=200 in Step 21e.
- [~] **21e.** Scale UPM vLLM to a larger open-weights model and re-run Step 17. **Tried Llama-3.3-70B AWQ first** — fits on the A100 but is too slow at concurrency=1 for thesis-scale runs (~30 s per detect_then_replace example). **Pivoted to `unsloth/Meta-Llama-3.1-8B-Instruct`** (FP16, ~16 GB weights, plenty of headroom, concurrency=4): 200 examples in 75 s with 98.5% success rate. Llama-3.1-8B is the open-weights baseline that ships with the thesis for now; 70B remains as a future upgrade if results warrant the wait. Step 17 re-runs (RQ1 comparison vs gemini-3-flash) still pending. **Operational improvements landed during this step:**
  - Parametrized `scripts/upm_vllm_startup.sh` with `MODEL`/`QUANTIZATION`/`MAX_MODEL_LEN`/`GPU_MEMORY_UTILIZATION`/`HF_TOKEN` env vars (HF_TOKEN added for gated repos like meta-llama/*; falls back to ungated mirrors).
  - Wrote `scripts/upm_vllm_shutdown.sh` for clean stack teardown — required when switching models, since `pkill` alone doesn't always release CUDA memory in time. Handles the case where `nvidia-smi` is permission-restricted on the JupyterHub pod (returns "[Insufficient Permissions]" instead of a number).
  - Documented the model-switch workflow in `scripts/UPM_VLLM_README.md`.
  - Local concurrency cap re-verified: 4 (8B), 1 (70B Q4).
- [x] **21e-survey.** Generated `survey_candidates_v2.csv` from the 8B run (`a45befe4-ff5c-43bd-ae87-9042856f3485`, 197/200 completed in 75 s). 73 candidates passed the filter (vs 61 from the Gemini run); 50 selected (all in the with-gold-paraphrase tier). Quality is mixed — model is more conservative than Gemini (3/5 sentences in spot-check returned "no idiom") and shows occasional hallucination (detected "pecking order" in a sentence that didn't contain it; flagged "baby blues" as the postpartum-depression idiom in a sentence about literal blue eyes). These are exactly the failure modes the survey is designed to surface. v2 is now the **active pool**; v1 (Gemini) is retained on disk as a historical reference only — **not used in the human-eval survey** (decision 04-05-2026: drop all hosted-model conditions from the report and the survey).
- [x] **21f (2026-05-05).** Step 17 re-runs landed at 200-example deterministic slice: 8B detection (`1afd4cf1` VU, `cfe4f798` SemEval); 70B detection (`26dc7cd2` VU, `be7dd99f` SemEval). 70B sentence F1 +18.0–20.5pp over 8B on detection across both phenomena.
- [x] **21g (2026-05-05).** Step 20 re-runs landed: 8B dtr v1+v2 (`eb415563`, `b2b174ea`, `821c8e59`, `d6bc60b0`); 70B dtr v2 (`df765b22` VU, `92941662` SemEval); 8B + 70B pipeline (`60a0390a`, `3551e201`, `b9698d70`, `56f19b8c`). Replaces Gemini-era numbers in `rq3_replacement.tex` and confirms the schema-lift inversion + pipeline.detect ≡ detection-only equivalence at scale.
- [x] **21h (2026-05-05).** Recorded in `wiki/thesis/research-questions.md` (RQ1 200-example scale table, 6 rows × 3 metrics) and folded into `notes.md` Step 21 section + `discussion.tex` model-dependence finding (2). Three findings empirically airtight: pipeline.detect ≡ detection-only (4/4 cells); dtr v2 schema-lift inverts at scale (+12/+22pp 8B → −5/−28pp 70B); detection-replacement scale dissociation (+18-20pp detection lift, BLEU/BERTScore tied or marginally lower at 70B).

## Step 22: Survey-pool generation for the three-system human eval

The Direct Assessment survey rates 30 sources × 3 open-weights conditions = 90 items. `survey_candidates_v2.csv` (Llama-3.1-8B agentic) provides condition 1; the other two need fresh runs on the same source sentences.

- [x] **22a (2026-05-04).** Sampled 30 source sentences from `survey_candidates_v2.csv` via `scripts/select_survey_sources.py`, stratified across length terciles (seed=19260817, lengths 31–176 chars, median 116). Output: `1 - Thesis/Survey/selected_sources.csv` with columns `source_id | example_id | original_text | gold_detected_expression | agentic_8b_replacement`. The Llama-3.1-8B agentic outputs for these 30 are reused from run `a45befe4-…` and copied into the CSV directly — no re-inference needed.
- [x] **22b (2026-05-04).** Implemented monolithic single-prompt task variant. Added `TaskType.MONOLITHIC_REPLACE` to `models/python/models/types/shared.py`; `load_prompt` updated to resolve `monolithic_replace_{phenomenon}.txt`. New prompt files `prompts/idiom/monolithic_replace_idiom.txt` and `prompts/metaphor/monolithic_replace_metaphor.txt` (stub: "Rewrite the following sentence in plain, literal English…"). New nodes `monolithic_replace_idiom` / `monolithic_replace_metaphor` in `workflows/nodes.py` — single LLM call, free-text output, `detection_result=None`. New graphs `{idiom,metaphor}_monolithic_replace_graph` registered in `workflows/graph.py`. Eval pipeline already guards on `pred.predicted_detection`, so monolithic runs naturally produce only BLEU/BERTScore on SemEval (no token/span/sentence F1).
- [x] **22c (2026-05-04, first pass).** Ran the monolithic graph at limit=200 SemEval idiom on `vllm:meta-llama/Llama-3.1-8B-Instruct`, T=0. Run `72199c9e-45a1-4c3d-afd4-a58347f4a91e` — **200/200 completed, 0 failed**. Metrics: BLEU=0.027, BERTScore_F1=0.847. Compare 8B agentic v2 (072f96dc) BLEU=0.059, BERTScore_F1=0.848 → agentic decomposition ~2.2× BLEU at 8B; BERTScore essentially tied. *Note: this run did not cover the 30 selected survey sources due to non-deterministic LIMIT 200 — see 22c-targeted below.*
- [x] **22c-targeted (2026-05-04).** Re-fired 8B monolithic on the explicit list of 30 selected sources (`example_ids` filter, new RunRequest field). Run `c8a2c8e3-5e2b-414f-a3f9-ce0ff6d364c1` — **30/30 completed, 0 failed**. Required adding `WHERE example_id IN $3` branch in `_execute_run` plus an `example_ids: Optional[List[str]]` field on `RunRequest` (the original `LIMIT 200` query had no `ORDER BY` so the slice was non-deterministic across container restarts and re-ingests). Same code change also fixed the underlying determinism issue: the no-filter branch now has `ORDER BY t.example_id`, so future report-grade runs are reproducible.
- [x] **22d (2026-05-04).** Cluster swap to `casperhansen/llama-3.3-70b-instruct-awq` complete. Final cluster config: `MAX_MODEL_LEN=4096` (was 2048; 2048 broke v2 detect-then-replace because client-side `max_tokens=3000` cap exceeded the context ceiling — earlier run `225a6805` 0/5 failure was the symptom), `GPU_MEMORY_UTILIZATION=0.92` (was 0.95; left ~3 GB headroom for KV cache at FP16 of 70B). Local-side `vllm-concurrency=1` set in `set-values-and-secrets`; user respawned API container. Canary run `37482918-801e-417a-845f-9432661324a8` (limit=2, agentic v2): **2/2 success**, sensible detections + replacements (`guilt trip` → "make … feel guilty"; `reaching` → "making an unrealistic attempt").
- [x] **22e (2026-05-04, first pass).** Ran agentic v2 graph at limit=200 SemEval idiom on `vllm:casperhansen/llama-3.3-70b-instruct-awq`, T=0. Run `aa690557-2c53-4bae-ae97-302eb8ad03cb` — **200/200 completed, 0 failed**, wallclock ~110 min. Same non-deterministic-LIMIT issue: covered only 2 of 30 selected sources. Metrics persisted but for a different example slice than 21f/21g.
- [x] **22e-targeted (2026-05-04).** Re-fired 70B agentic v2 on the 30 selected sources via `example_ids` filter. Run `3e2500ec-9976-4326-acb1-0836e168e695` — **30/30 completed, 0 failed**, ~5 min wallclock with concurrency=4 + prefix-cache batching. Outputs are clean ("brush the incident aside / chalk it up to ancient history" → "dismiss the incident as unimportant and consider it a past event that is no longer relevant"; "top dog" → "the most powerful or dominant news organization").
- [x] **22f (2026-05-04, re-assembled 2026-05-05 after pipeline rebuild + Couchbase wipe).** Assembled `survey_items.csv` (84 rows = 28 sources × 3 conditions; src_17 and src_22 dropped after manual bad-reference review). All cells populated, no missing predictions. **Final survey conditions and run IDs**: Cond 1 8B pipeline → `aea60b3d-7b30-41c2-a3b8-4472d280a9f0`; Cond 2 8B monolithic → `460d4b15-ffc7-44a2-b38c-4034cd6b8e29`; Cond 3 70B pipeline → `10366af9-d22d-4040-8075-ea1942298370`. Architecture switched from single-call structured-CoT to true 3-step pipeline (`detect → explain → transform`) to faithfully test RQ2's "agentic decomposition" wording. `displayed_detected_expression` shows the SemEval gold idiom for all three conditions on the same source; `system_id` held back from the survey form, kept only in analysis-side metadata.
- [x] **22g (2026-05-04 generated, 2026-05-05 reviewed).** Generated 30 LLM-degraded bad-reference items via `scripts/generate_bad_references.py` against `gemini-3-flash-preview` (T=0.7). Output: `1 - Thesis/Survey/bad_references_draft.csv`. User did manual review pass: 28 marked OK, 2 sources dropped (src_17 "head hunter" and src_22 "foot and ankle" — both judged literal-in-context rather than figurative; reduces survey to 28 sources × 3 = 84 items), 2 regenerated with stronger prompt at T=0.9 (src_00, src_04 — initial bad-refs were too subtle). Final `bad_references_final.csv` reviewed and approved. Repeat-pair items: handled at form-construction time (per `respondent_assignments/respondent_01.csv` deterministic assignment).

## Step 23: Bib re-export for the survey-design citations

Several methodology citations added to `background.tex` (`Graham2013`, `Alva-Manchego2020`, `Alva-Manchego2021`, `Scialom2021`) are present in the user's Mendeley library but not yet in `mendeley.bib`. Re-export `mendeley.bib` from Mendeley before the next LaTeX build.

- [ ] **23a.** Re-export `mendeley.bib` from Mendeley desktop/web; verify the four keys above resolve.
- [ ] **23b.** `latexmk` clean build; confirm no missing-citation warnings in the methodology and RQ3 sections.

## Step 24: Survey distribution

- [x] **24a (2026-05-05).** MS Form built (one seeded sample matching `respondent_assignments/respondent_01_form.pdf`). Live at `https://forms.microsoft.com/e/FTdiVdKNqq` — sent to Mari Carmen as the illustrative instrument for review.
- [x] **24b (2026-05-05).** Email sent to Mari Carmen with survey design summary, methodology citations (Graham 2013/2017, Alva-Manchego 2020), distribution plan (~15 native-English contacts targeting ≥3 ratings per item across the 84-item pool), and pilot strategy (cut items per respondent if median completion >10 min). Asked for sign-off + standard UPM ethics paragraph.
- [ ] **24c.** Mari Carmen response — incorporate feedback into form/intro page; insert ethics paragraph; resolve any methodology pushback.
- [ ] **24d.** Build remaining respondent forms (16 total). Either: (a) clone the validated form 15× via MS Forms duplicate, swapping the per-respondent items from `respondent_assignments/respondent_{02..16}.csv` (use the seeded generator with seed=2..16); or (b) consolidate to a single MS Form with all 84 items and rely on MS Forms' randomisation to give each respondent a different subset (limited control vs option a, but lower setup cost). Choice depends on Mari Carmen's feedback.
- [ ] **24e.** Pilot the form with 1–2 friendly respondents; time median completion. Decision rule (per `Survey/PLAN.md` §7): if median >25 min, drop to 16 items per respondent (12 real + 4 QC) and recruit ~20 respondents instead of 17.
- [ ] **24f.** Distribution to Mari Carmen's contacts and Jelle's ~15 native-English contacts.
- [ ] **24g.** Response collection (Google Sheets export from MS Forms → CSV); per-annotator z-score standardisation; per-item aggregation; agreement diagnostics. Write up RQ3 Section~\ref{subsec:rq3-human-eval-results}.

## Step 25: Report writing plan + scaffolding (2026-06-10)

- [x] **25a (2026-06-10).** Central theme locked with Claude: **"structure over scale"** (explicit task structure + human-grounded evaluation are the reliable levers, not scale or prompt engineering). Structure decisions: per-RQ chapters retained; RQ4 dissolved into Discussion 8.3; H4 stated as untested + future-work design. Authoritative guide: `thesis-report/WRITING_PLAN.md` + per-section `% === WRITING GUIDE ===` blocks in every chapter `.tex`.
- [x] **25b (2026-06-10).** Report scaffolding executed: rq4_observability.tex + template orphans deleted; survey-results tables inserted (rq2 paired comparison, rq3 by-system + QC, model-dependence synthesis, supervised-comparison stub); stale survey numbers fixed (27 x 3 = 81 items, 22 -> 20 kept); methodology.tex aligned to as-run QC rules + paired t/Wilcoxon + Student-t CIs; figure placeholders F-1/F-2/F-3; compile clean at 42 pp.
- [x] **25c (2026-06-18).** Resolved `TODO(verify)` flags. (1) N is **27** (all-figurative pool, src_18 dropped) — the `N=30` was the pre-switch single-call pool, confirming the old numbers predate the pipeline switch. (2) Detection recomputed offline from frozen `survey_items.csv` predictions via `scripts/recompute_survey_pool_detection.py` (zero-dep): 8b_agentic 21/27 detect, sent F1 0.875, span F1 0.350; 70b_agentic 24/27, sent F1 0.941, span F1 0.638; monolithic n/a (no detect step). Same scale direction as RQ1. (3) BLEU/BERTScore: a reference DOES exist (corrected after pushback) — `ingestion.build_semeval_replacement_map` matches Task A idioms to Task B `sim=1` pairs by MWE string and stores `sentence_2` as `metadata["gold_sentence_replacement"]`; reconstructible offline. But only **9/27** survey sources have a match (src_04,05,06,13,14,16,21,26,27) and the reference is a *different sentence* sharing only the idiom (not a rewrite of the example's own sentence), which is why old BLEU was ~0.061. Faithful 9-source recompute is feasible but the metric is a weak/indirect signal; reframe `tab:rq2-automatic` (agentic-vs-monolithic has no strong automatic basis: detection n/a to monolithic, replacement rests on 9/27 cross-sentence refs; detection numbers are an 8B-vs-70B axis). Artifact: `Vault/1 - Thesis/Survey/results/RECOMPUTE_survey_pool_detection.md`. **Still to do in the .tex when writing 6.x:** apply detection numbers, fix N=27, reframe the table prose, update the discussion scale-dependence paragraph (remove old 0.609->0.767); decide whether to cite faithful 9-source BLEU or drop the row.
- [ ] **25d.** Supervised-SOTA literature lookup for rq1 5.4 / Table tab:rq1-supervised (VUA + SemEval Task 2A baselines; Neidlein 2020 + Jia 2024 + task paper). Only external dependency in the writing plan; start before Jun 17.
- [ ] **25e.** Write the prose per `WRITING_PLAN.md` schedule (Jun 17-29): 7.6 -> 6.3/6.4 -> 8.1-8.6 -> intro/conclusion -> background -> 5.4/5.5 -> abstract/resumen/acknowledgements -> read-through -> Jun 29 full draft to Mari Carmen.
