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
