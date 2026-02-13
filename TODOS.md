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
