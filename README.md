# e2r-adaptation

Companion code for the master's thesis **"Easy-to-Read (E2R) Adaptation of Figurative Language"** (Jelle van Lieshout, Universidad Politécnica de Madrid, 2026, supervised by Dr. Mari Carmen Suárez-Figueroa). The thesis report lives at [jellevlieshout/thesis-report](https://github.com/jellevlieshout/thesis-report).

The system detects figurative language (idioms and metaphors) in English sentences and rewrites the sentences in plain, literal English, following Easy-to-Read guidelines. All experiments reported in the thesis were run with this codebase, and every reported number can be traced to a persisted run document (see the run index in the thesis Annex).

## What the system does

Two phenomena, two tasks:

- **Detection**: decide whether a sentence contains figurative language and mark the exact expressions. Idiom detection follows the SemEval-2022 Task 2 annotation conventions; metaphor detection follows the VU Amsterdam Metaphor Corpus (VUAMC) MIP procedure.
- **Replacement**: rewrite the full sentence with each figurative expression replaced by its literal meaning, keeping the rest of the sentence as close to the original as possible.

Three system conditions implement the replacement task, and their contrast is the designed experiment behind the thesis:

1. **Monolithic baseline**: one prompt that asks the model to rewrite the sentence in plain, literal English.
2. **Single-call detect-then-replace**: one structured LLM call that returns detection output and a literal paraphrase together.
3. **Three-step agentic pipeline**: three sequential LLM calls (detect, explain, transform) in a LangGraph workflow, with intermediate results carried in the graph state so each step is inspectable on its own.

Detection output is schema-constrained (a Pydantic `TaskOutput` model enforced via LangChain's `with_structured_output()`, with automatic retries on invalid output). Two deterministic post-processing steps then derive character-offset spans and per-token labels for evaluation.

## Architecture

| Component | Choice |
|---|---|
| Backend | FastAPI (Python 3.13); runs launched asynchronously as background tasks |
| Workflows | LangGraph, one graph per (phenomenon, task) combination plus the three-step pipeline |
| Persistence | Couchbase 7.6, four collections: `datasets`, `runs`, `predictions`, `evaluations` |
| Model serving | vLLM on a UPM A100 GPU node (identifiers prefixed `vllm:`); OpenRouter as a development-time fallback |
| Frontend | React/TypeScript SPA (TanStack Query): run dashboards, span visualisation, replacement diff views, metric comparison charts |
| Orchestration | Polytope (`polytope.yml`) |
| Observability | LangSmith tracing on all LLM invocations |

Two open-weights models are evaluated, both with greedy decoding (temperature 0):

- `meta-llama/Meta-Llama-3.1-8B-Instruct` (FP16), the deliverable system;
- `casperhansen/llama-3.3-70b-instruct-awq` (AWQ-quantised), the scale comparator.

Every run document records the full prompt text and its SHA-256 hash, so results are exactly reproducible and prompt drift between runs is detectable.

## Datasets

- **SemEval-2022 Task 2** (idioms): 3,487 sentences, with Task B gold paraphrases used for reference-based replacement metrics.
- **VU Amsterdam Metaphor Corpus** (metaphors): 16,202 sentences with token-level annotations, parsed from the source XML.

Custom parsers in the API convert both corpora into a common example schema and write them to the `datasets` collection (`POST /datasets/ingest`).

## Evaluation

Automatic metrics, computed per run and persisted as `evaluations` documents (re-computable via `POST /runs/{run_id}/evaluate`):

- **Token F1** (VUAMC only), **Span F1** (IoU >= 0.5, one-to-one matching), and **Sentence F1** for detection;
- **BLEU** and **BERTScore** against SemEval Task B gold paraphrases for replacement.

Because no automatic metric scores figurative-language replacement reliably, the thesis adds a human evaluation: an adapted Direct Assessment survey (81 items, 27 sources under each of the 3 system conditions) rated on grammaticality, meaning preservation, and simplicity by native English speakers, with embedded quality-control items. The survey tooling lives in `scripts/` (item selection, form assembly, bad-reference generation, response merging and analysis).

## Repository layout

```
services/       API (FastAPI), frontend (React), Couchbase, config-manager
models/         Pydantic + Couchbase entity models (datasets, runs, predictions, evaluations)
clients/        client libraries
prompts/        versioned prompt files, one set per phenomenon
                (detect / explain / transform / monolithic_replace)
datasets/       SemEval-2022 Task 2 and VUAMC source data
scripts/        survey pipeline, open-weights sweep runner,
                UPM vLLM startup/shutdown, dataset verification
polytope.yml    orchestration entry point
```

## Running

The stack is orchestrated by [Polytope](https://polytope.com): `polytope run stack` starts the API, frontend, Couchbase, and config-manager together (secrets and values via `set-values-and-secrets`, see the example file). Note: the Couchbase volume is not mounted in development, so datasets must be re-ingested after a container restart.

To serve the open-weights models, `scripts/upm_vllm_startup.sh` starts vLLM on the UPM cluster and exposes it through a basic-auth-protected ngrok tunnel; see `scripts/UPM_VLLM_README.md`.

## Findings, in brief

Across the thesis experiments, model scale lifted detection but not human-perceived replacement quality, and decomposing the task into the three-step pipeline gave a consistent directional advantage on meaning preservation (+0.31 standardised units, p = 0.06-0.08) that approaches but does not reach conventional significance. Full results, hedges included, are in the thesis report.
