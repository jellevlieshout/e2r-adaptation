# Figurative Language Detection & Literal Paraphrasing Experiment Framework

## System Specification

---

## 1. Purpose

This system provides a structured, reproducible experimentation framework for:

* Detecting figurative language
* Generating literal paraphrases
* Evaluating model performance
* Logging and inspecting runs
* Supporting research-level experimentation

The system explicitly separates:

* **Metaphor detection** (VU Amsterdam Corpus)
* **Idiom detection and simplification** (SemEval Task 2)

The architecture must support:

* Large-scale automated experiments
* Manual input and annotation
* Deterministic evaluation
* Reproducibility
* Future metric extensibility

---

## 2. Conceptual Separation

| Dataset | Phenomenon | Detection Granularity | Gold Replacement |
|----------|------------|----------------------|------------------|
| VU Amsterdam | Metaphor | Token + Span | No |
| SemEval Task 2 | Idiom | Span | Yes |

Internally use:

```
phenomenon: "metaphor" | "idiom"
```

Never mix metaphor terminology with idiom terminology in prompts or logic.

---

## 3. System Architecture

### Backend

* FastAPI (API layer)
* LangGraph (workflow orchestration)
* LangSmith (trace logging)
* Couchbase (persistent storage)

### Frontend

* React
* Run dashboard
* Example inspection interface
* Span visualisation
* Metrics comparison

---

## 4. Storage Design (Couchbase)

**Bucket:**

```
metaphor_experiments
```

**Collections:**

```
datasets
runs
predictions
evaluations
```

---

## 5. Data Models

### 5.1 Dataset Document

**Key:**

```
dataset::{dataset_name}::{example_id}
```

**Schema:**

```json
{
  "type": "dataset_example",
  "dataset": "vu_amsterdam | semeval | manual",
  "phenomenon": "metaphor | idiom",
  "example_id": "string",
  "text": "string",
  "tokens": ["optional"],
  "gold_detection": {
    "token_labels": [0,1,0,0],
    "spans": [{"start": 12, "end": 19}],
    "is_figurative": true
  },
  "gold_replacement": "string | null",
  "metadata": {},
  "created_at": "timestamp"
}
```

**Rules:**

VU:
* `token_labels` required
* `spans` derived from `token_labels` at ingestion
* `gold_replacement` must be null

SemEval:
* `spans` required
* `gold_replacement` required

Manual:
* Gold fields optional

All spans must use character offsets.

### 5.2 Run Document

**Key:**

```
run::{run_id}
```

**Schema:**

```json
{
  "type": "run",
  "run_id": "uuid",
  "dataset": "vu_amsterdam | semeval | manual",
  "phenomenon": "metaphor | idiom",
  "task_type": "detection | replacement | detect_then_replace",
  "model_name": "string",
  "temperature": 0,
  "top_p": 1,
  "prompt_version": "string",
  "prompt_hash": "sha256",
  "created_at": "timestamp",
  "status": "running | completed | failed",
  "stats": {
    "total_examples": 0,
    "completed": 0,
    "failed": 0
  }
}
```

### 5.3 Prediction Document

**Key:**

```
prediction::{run_id}::{example_id}
```

**Schema:**

```json
{
  "type": "prediction",
  "run_id": "uuid",
  "example_id": "string",
  "dataset": "vu_amsterdam",
  "phenomenon": "metaphor",
  "task_type": "detect_then_replace",
  "input_text": "string",
  "predicted_detection": {
    "is_figurative": true,
    "token_labels": [0,1,0],
    "spans": [{"start": 12, "end": 19}]
  },
  "predicted_replacement": "string | null",
  "raw_model_output": "string",
  "latency_ms": 0,
  "token_usage": {},
  "confidence": 0.8,
  "created_at": "timestamp"
}
```

### 5.4 Evaluation Document

**Key:**

```
evaluation::{run_id}::{metric_name}
```

**Schema:**

```json
{
  "type": "evaluation",
  "run_id": "uuid",
  "metric_name": "f1_token | f1_span | f1_sentence | bleu",
  "value": 0.74,
  "metadata": {
    "dataset": "vu_amsterdam",
    "phenomenon": "metaphor"
  },
  "created_at": "timestamp"
}
```

---

## 6. Structured LLM Output Contract

All model outputs must conform to:

```json
{
  "detection": {
    "is_figurative": true,
    "token_labels": [0,1,0],
    "spans": [{"start": 12, "end": 19}]
  },
  "replacement": {
    "literal_paraphrase": "..."
  },
  "confidence": 0.82
}
```

**Validation Rules:**

* Spans must be sorted
* Spans must not overlap
* 0 ≤ start < end ≤ len(text)
* `token_labels` length must match tokens
* If no figurative language:
  * `spans = []`
  * `is_figurative = false`

Retry up to 2 times on invalid schema.

---

## 7. Span Canonicalisation

Implement:

```python
normalize_spans(spans, text_length)
```

**Steps:**

1. Sort spans
2. Merge overlapping spans
3. Clip to boundaries
4. Remove zero-length spans

Must be applied:

* Before storage
* Before evaluation

---

## 8. Evaluation Engine

**Endpoint:**

```
POST /runs/{run_id}/evaluate
```

Evaluation is separate from inference.

### 8.1 Metaphor (VU)

**Token-Level F1:**

Use:

```python
sklearn.metrics.precision_recall_fscore_support
```

Store:

* `f1_token`
* `precision_token`
* `recall_token`

**Span-Level F1:**

Matching rule: IoU ≥ 0.5

Compute:

* TP
* FP
* FN
* `precision_span`
* `recall_span`
* `f1_span`

### 8.2 Idiom (SemEval)

**Span-Level F1:**

Same IoU rule.

**Sentence-Level F1:**

Binary rule:

```python
is_figurative = len(spans) > 0
```

Store:

* `f1_sentence`

### 8.3 Replacement Evaluation (Idioms Only)

Compute BLEU only if:

```python
gold_replacement != null
```

Use:

```python
nltk.translate.bleu_score.sentence_bleu
```

Store:

* `bleu`

---

## 9. Experiment Runner

**Endpoint:**

```
POST /runs
```

**Example Body:**

```json
{
  "dataset": "vu_amsterdam",
  "task_type": "detect_then_replace",
  "model_name": "gpt-4.1",
  "prompt_version": "metaphor_detection_v2",
  "temperature": 0,
  "few_shot_examples": 3
}
```

**Execution Flow:**

1. Create run document
2. Load dataset examples
3. Execute LangGraph workflow
4. Store predictions
5. Update run stats
6. Mark run complete

Parallel execution allowed.

---

## 10. LangGraph Workflows

Define separate workflows:

* `metaphor_detection_graph`
* `idiom_detection_graph`
* `metaphor_detect_then_replace_graph`
* `idiom_detect_then_replace_graph`

Prompts must explicitly state:

* "metaphorical usage" for VU
* "idiomatic expression" for SemEval

Do not reuse identical prompts.

---

## 11. Manual Mode

**Create manual example:**

```
POST /manual
```

**Optional annotation:**

```
POST /manual/{example_id}/annotate
```

Manual examples can be included in runs.

---

## 12. React UI

### 12.1 Run Overview

Display:

* Model
* Dataset
* Phenomenon
* Prompt version
* Metrics
* Example count
* Completion %

### 12.2 Example Inspection

Display:

* Original text
* Gold spans (red)
* Predicted spans (blue)
* Overlap (purple)
* Gold replacement
* Predicted replacement
* Diff viewer
* Raw JSON output
* Latency

### 12.3 Run Comparison

Allow multiple run selection:

* Metrics table
* Bar chart comparison

---

## 13. Prompt Versioning

Prompts stored in:

```
/prompts/metaphor/
/prompts/idiom/
```

At run creation:

* Compute SHA256
* Store hash in run document

---

## 14. Metric Registry

```python
METRIC_REGISTRY = {
    "f1_token": compute_f1_token,
    "f1_span": compute_f1_span,
    "f1_sentence": compute_f1_sentence,
    "bleu": compute_bleu
}
```

Future extensibility:

* BERTScore
* Semantic similarity
* Human evaluation ingestion

---

## 15. Failure Handling

If output invalid:

* Retry twice
* If still invalid:
  * Store prediction with null fields
  * Increment `run.failed`

---

## 16. Reproducibility Requirements

Each run must store:

* Model name
* Model version (if available)
* Temperature
* Top_p
* Prompt hash
* Dataset version
* Timestamp

Evaluation must be re-runnable without re-inference.

---

## 17. Definition of Done

The system is complete when:

* VU runs produce token + span F1
* SemEval runs produce span + sentence F1 + BLEU
* Manual examples supported
* React UI visualises spans
* All outputs strictly validated
* Runs reproducible
* Evaluation re-runnable independently