import asyncio
import csv
import io
import logging
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models.entities.dataset_example import DatasetExample, DatasetExampleData
from models.entities.evaluation import EvaluationData
from models.entities.prediction import PredictionData
from models.entities.run import RunData, RunStatus
from models.types.shared import DatasetType, MetricName, PhenomenonType, TaskType
from workflows.graph import get_graph
from workflows.nodes import VLLM_MODEL_PREFIX
from workflows.state import GraphState
from models.operations import (
    compute_f1_token,
    compute_f1_span,
    compute_f1_sentence,
    compute_bleu,
    compute_bertscore,
    load_prompt,
    compute_prompt_hash
)
from clients.couchbase.couchbase import get_keyspace, Keyspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])


class RunRequest(BaseModel):
    dataset: DatasetType
    phenomenon: PhenomenonType
    task_type: TaskType
    model_name: str
    temperature: float = 0.0
    top_p: float = 1.0
    prompt_version: str
    few_shot_examples: int = 0
    limit: Optional[int] = None  # For testing


class RunResponse(BaseModel):
    run_id: str
    status: RunStatus
    message: str


class RunMetricsResponse(BaseModel):
    run_id: str
    metrics: dict[str, float]
    examples_evaluated: int


def _resolve_concurrency(model_name: str) -> int:
    """Pick the per-provider concurrency cap based on the model_name dispatch prefix.

    OpenRouter spreads load across many backend GPUs, so 10 concurrent calls is
    safe by default. The UPM A100 cluster runs vLLM on a single 40 GB GPU; the
    KV cache competes with model weights for VRAM, so the cap is conservative
    (4). When running a 70B Q4 model on the A100, the model itself fills the
    card and concurrency must drop to 1 — set VLLM_CONCURRENCY=1 then.
    """
    if model_name.startswith(VLLM_MODEL_PREFIX):
        return int(os.environ.get("VLLM_CONCURRENCY", "4"))
    return int(os.environ.get("OPENROUTER_CONCURRENCY", "10"))


async def _execute_run(run_data: RunData, limit: Optional[int] = None):
    logger.info(f"Starting run execution: {run_data.run_id}")

    try:
        # 1. Load dataset examples
        ks: Keyspace = DatasetExample.get_keyspace()

        query = """
            SELECT VALUE t FROM ${keyspace} t
            WHERE t.`dataset` = $1 AND t.`phenomenon` = $2
        """
        if limit:
            query += f" LIMIT {limit}"

        rows = list(ks.query(
            query,
            positional_parameters=[run_data.dataset.value, run_data.phenomenon.value]
        ))

        run_data.stats.total_examples = len(rows)

        graph = get_graph(run_data.phenomenon.value, run_data.task_type.value)

        pred_ks = get_keyspace("predictions", bucket_name="main")
        pred_collection = pred_ks.get_collection()
        run_ks = get_keyspace("runs", bucket_name="main")
        run_collection = run_ks.get_collection()

        concurrency = _resolve_concurrency(run_data.model_name)
        logger.info(f"Run {run_data.run_id}: {len(rows)} examples, concurrency={concurrency}")
        sem = asyncio.Semaphore(concurrency)

        async def process(example_data: dict) -> None:
            example_id = example_data.get("example_id")
            input_text = example_data.get("text", "")

            state_input: GraphState = {
                "input_text": input_text,
                "dataset": run_data.dataset.value,
                "phenomenon": run_data.phenomenon.value,
                "model_name": run_data.model_name,
                "temperature": run_data.temperature,
                "detection_result": None,
                "replacement_result": None,
                "latency_ms": 0,
                "token_usage": {},
                "errors": []
            }

            async with sem:
                try:
                    result_state = await graph.ainvoke(state_input)

                    has_errors = len(result_state.get("errors", [])) > 0

                    detection = result_state.get("detection_result")
                    if detection is not None and hasattr(detection, "model_dump"):
                        detection = detection.model_dump()

                    pred = PredictionData(
                        run_id=run_data.run_id,
                        example_id=example_id,
                        dataset=run_data.dataset,
                        phenomenon=run_data.phenomenon,
                        task_type=run_data.task_type,
                        input_text=input_text,
                        predicted_detection=detection,
                        predicted_replacement=result_state.get("replacement_result"),
                        latency_ms=result_state.get("latency_ms"),
                        token_usage=result_state.get("token_usage"),
                        raw_model_output=str(result_state.get("errors")) if has_errors else None,
                        confidence=0.0
                    )

                    if has_errors:
                        logger.warning(f"Errors in run {run_data.run_id} example {example_id}: {result_state['errors']}")
                        run_data.stats.failed += 1
                    else:
                        run_data.stats.completed += 1

                    # Couchbase client is sync; offload to a worker thread so we
                    # don't block the event loop while other examples are in flight.
                    await asyncio.to_thread(
                        pred_collection.upsert,
                        pred.document_key(),
                        pred.model_dump(mode="json"),
                    )

                except Exception as e:
                    logger.error(f"Exception processing example {example_id}: {e}")
                    run_data.stats.failed += 1

        await asyncio.gather(*(process(row) for row in rows))

        if run_data.stats.completed == 0 and run_data.stats.failed > 0:
            run_data.status = RunStatus.FAILED
        else:
            run_data.status = RunStatus.COMPLETED

        await asyncio.to_thread(
            run_collection.upsert,
            run_data.document_key(),
            run_data.model_dump(mode="json"),
        )

        logger.info(f"Run {run_data.run_id} completed. Stats: {run_data.stats}")

    except Exception as e:
        logger.error(f"Run execution failed: {e}")
        run_data.status = RunStatus.FAILED
        try:
            run_ks = get_keyspace("runs", bucket_name="main")
            await asyncio.to_thread(
                run_ks.get_collection().upsert,
                run_data.document_key(),
                run_data.model_dump(mode="json"),
            )
        except Exception:
            pass


@router.post("", response_model=RunResponse)
async def create_run(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Create and start a new experiment run.
    """
    run_id = str(uuid.uuid4())
    
    # Load prompt and compute hash
    try:
        prompt_text = load_prompt(request.phenomenon.value, request.task_type.value)
        prompt_hash = compute_prompt_hash(prompt_text)
    except Exception as e:
        logger.error(f"Failed to load prompt for hash: {e}")
        prompt_hash = "error"

    run_data = RunData(
        run_id=run_id,
        dataset=request.dataset,
        phenomenon=request.phenomenon,
        task_type=request.task_type,
        model_name=request.model_name,
        temperature=request.temperature,
        top_p=request.top_p,
        prompt_version=request.prompt_version,
        prompt_hash=prompt_hash,
        prompt_text=prompt_text if prompt_hash != "error" else "",
    )
    
    # Save initial run document
    run_ks = get_keyspace("runs", bucket_name="main")
    run_ks.get_collection().upsert(run_data.document_key(), run_data.model_dump(mode="json"))
    
    # Start background execution
    background_tasks.add_task(_execute_run, run_data, request.limit)
    
    return RunResponse(
        run_id=run_id,
        status=RunStatus.RUNNING,
        message="Run initiated successfully"
    )


@router.get("", response_model=List[RunData])
async def list_runs(limit: int = 50, offset: int = 0):
    """
    List all experiment runs.
    """
    ks = get_keyspace("runs", bucket_name="main")
    query = f"""
        SELECT VALUE t FROM ${{keyspace}} t
        ORDER BY t.created_at DESC
        LIMIT {limit} OFFSET {offset}
    """
    
    rows = ks.query(query)
    return [RunData(**row) for row in rows]


@router.get("/{run_id}", response_model=RunData)
async def get_run(run_id: str):
    """
    Get a specific run by ID.
    """
    ks = get_keyspace("runs", bucket_name="main")
    try:
        result = ks.get_collection().get(f"run::{run_id}")
        return RunData(**result.content_as[dict])
    except Exception:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


@router.get("/{run_id}/predictions")
async def get_run_predictions(run_id: str, include_gold: bool = False):
    """
    Get all predictions for a specific run.
    When include_gold=true, each prediction dict is enriched with
    gold_detection and gold_replacement from the dataset example.
    """
    ks = get_keyspace("predictions", bucket_name="main")
    query = """
        SELECT VALUE t FROM ${keyspace} t
        WHERE t.run_id = $1
        ORDER BY t.example_id
    """

    rows = ks.query(query, positional_parameters=[run_id])
    predictions = [PredictionData(**row) for row in rows]

    if not include_gold or not predictions:
        return predictions

    # Fetch the run to know dataset/phenomenon
    run_ks = get_keyspace("runs", bucket_name="main")
    try:
        run_res = run_ks.get_collection().get(f"run::{run_id}")
        run_data = RunData(**run_res.content_as[dict])
    except Exception:
        return predictions

    # Fetch dataset examples
    ds_ks = DatasetExample.get_keyspace()
    q_examples = "SELECT VALUE t FROM ${keyspace} t WHERE t.`dataset` = $1 AND t.`phenomenon` = $2"
    ex_rows = ds_ks.query(
        q_examples,
        positional_parameters=[run_data.dataset.value, run_data.phenomenon.value]
    )
    examples_map = {row["example_id"]: row for row in ex_rows}

    # Enrich predictions with gold data
    enriched = []
    for pred in predictions:
        pred_dict = pred.model_dump(mode="json")
        example = examples_map.get(pred.example_id)
        if example:
            pred_dict["gold_detection"] = example.get("gold_detection")
            pred_dict["gold_replacement"] = example.get("gold_replacement")
        enriched.append(pred_dict)

    return enriched


def _compute_metrics(
    run_data: RunData,
    predictions: List[PredictionData],
    examples_map: dict[str, DatasetExampleData],
) -> dict[str, float]:
    """
    Compute all applicable metrics for a run given its predictions and gold examples.
    Returns a dict of metric_name -> value.
    """
    all_gold_tokens = []
    all_pred_tokens = []

    span_metrics_sum = {"precision_span": 0.0, "recall_span": 0.0, "f1_span": 0.0}
    sentence_metrics_sum = {"f1_sentence": 0.0}
    bleu_sum = 0.0
    bertscore_sum = {"bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0}

    count_span = 0
    count_sentence = 0
    count_bleu = 0
    count_bertscore = 0

    for pred in predictions:
        example = examples_map.get(pred.example_id)
        if not example:
            continue

        # A. Token Level
        if (example.gold_detection and example.gold_detection.token_labels is not None
                and pred.predicted_detection and pred.predicted_detection.token_labels is not None):
            gl = example.gold_detection.token_labels
            pl = pred.predicted_detection.token_labels
            if len(gl) == len(pl):
                all_gold_tokens.extend(gl)
                all_pred_tokens.extend(pl)

        # B. Span Level (Macro Average)
        if pred.predicted_detection and example.gold_detection:
            res = compute_f1_span(example.gold_detection.spans, pred.predicted_detection.spans)
            for k, v in res.items():
                span_metrics_sum[k] += v
            count_span += 1

        # C. Sentence Level
        if pred.predicted_detection and example.gold_detection:
            res = compute_f1_sentence(example.gold_detection.spans, pred.predicted_detection.spans)
            sentence_metrics_sum["f1_sentence"] += res["f1_sentence"]
            count_sentence += 1

        # D. BLEU (Replacement)
        if example.metadata and example.metadata.get("gold_sentence_replacement") and pred.predicted_replacement:
            res = compute_bleu(example.metadata.get("gold_sentence_replacement"), pred.predicted_replacement)
            bleu_sum += res["bleu"]
            count_bleu += 1

        # E. BERTScore (Replacement)
        if example.metadata and example.metadata.get("gold_sentence_replacement") and pred.predicted_replacement:
            res = compute_bertscore(example.metadata.get("gold_sentence_replacement"), pred.predicted_replacement)
            bertscore_sum["bertscore_precision"] += res["bertscore_precision"]
            bertscore_sum["bertscore_recall"] += res["bertscore_recall"]
            bertscore_sum["bertscore_f1"] += res["bertscore_f1"]
            count_bertscore += 1

    metrics = {}

    if all_gold_tokens:
        token_res = compute_f1_token(all_gold_tokens, all_pred_tokens)
        metrics.update(token_res)

    if count_span > 0:
        for k, v in span_metrics_sum.items():
            metrics[k] = v / count_span

    if count_sentence > 0:
        metrics["f1_sentence"] = sentence_metrics_sum["f1_sentence"] / count_sentence

    if count_bleu > 0:
        metrics["bleu"] = bleu_sum / count_bleu

    if count_bertscore > 0:
        for k, v in bertscore_sum.items():
            metrics[k] = v / count_bertscore

    return metrics


def _fetch_run_predictions_examples(run_id: str):
    """
    Fetch run, predictions, and dataset examples for a given run_id.
    Returns (run_data, predictions, examples_map).
    Raises HTTPException if run not found.
    """
    # Fetch Run
    run_ks = get_keyspace("runs", bucket_name="main")
    try:
        run_res = run_ks.get_collection().get(f"run::{run_id}")
        run_data = RunData(**run_res.content_as[dict])
    except Exception:
        raise HTTPException(status_code=404, detail="Run not found")

    # Fetch Predictions
    pred_ks = get_keyspace("predictions", bucket_name="main")
    q_preds = "SELECT VALUE t FROM ${keyspace} t WHERE t.run_id = $1"
    preds_rows = pred_ks.query(q_preds, positional_parameters=[run_id])
    predictions = [PredictionData(**row) for row in preds_rows]

    # Fetch Dataset Examples
    ds_ks = DatasetExample.get_keyspace()
    q_examples = "SELECT VALUE t FROM ${keyspace} t WHERE t.`dataset` = $1 AND t.`phenomenon` = $2"
    ex_rows = ds_ks.query(
        q_examples,
        positional_parameters=[run_data.dataset.value, run_data.phenomenon.value]
    )
    examples_map = {row["example_id"]: DatasetExampleData(**row) for row in ex_rows}

    return run_data, predictions, examples_map


@router.post("/{run_id}/evaluate", response_model=RunMetricsResponse)
async def evaluate_run(run_id: str):
    """
    Compute evaluation metrics for a run and persist them as EvaluationData documents.
    Re-runnable: overwrites previous evaluation documents for the same run.
    """
    run_data, predictions, examples_map = _fetch_run_predictions_examples(run_id)

    if not predictions:
        return RunMetricsResponse(run_id=run_id, metrics={}, examples_evaluated=0)

    metrics = _compute_metrics(run_data, predictions, examples_map)

    # Persist each metric as an EvaluationData document
    eval_ks = get_keyspace("evaluations", bucket_name="main")
    eval_collection = eval_ks.get_collection()

    for metric_key, value in metrics.items():
        try:
            metric_name = MetricName(metric_key)
        except ValueError:
            logger.warning(f"Skipping unknown metric name: {metric_key}")
            continue

        eval_doc = EvaluationData(
            run_id=run_id,
            metric_name=metric_name,
            value=value,
            metadata={
                "dataset": run_data.dataset.value,
                "phenomenon": run_data.phenomenon.value,
                "examples_evaluated": len(predictions),
            },
        )
        eval_collection.upsert(eval_doc.document_key(), eval_doc.model_dump(mode="json"))

    logger.info(f"Evaluation for run {run_id}: {len(metrics)} metrics stored")

    return RunMetricsResponse(
        run_id=run_id,
        metrics=metrics,
        examples_evaluated=len(predictions),
    )


@router.get("/{run_id}/metrics", response_model=RunMetricsResponse)
async def get_run_metrics(run_id: str):
    """
    Return evaluation metrics for a run.
    Reads from stored EvaluationData documents if available, otherwise computes on-the-fly.
    """
    # Try stored evaluations first
    eval_ks = get_keyspace("evaluations", bucket_name="main")
    q_evals = "SELECT VALUE t FROM ${keyspace} t WHERE t.run_id = $1"
    eval_rows = eval_ks.query(q_evals, positional_parameters=[run_id])
    stored_evals = [EvaluationData(**row) for row in eval_rows]

    if stored_evals:
        metrics = {e.metric_name.value: e.value for e in stored_evals}
        examples_evaluated = stored_evals[0].metadata.get("examples_evaluated", 0)
        return RunMetricsResponse(
            run_id=run_id,
            metrics=metrics,
            examples_evaluated=examples_evaluated,
        )

    # Fallback: compute on-the-fly
    run_data, predictions, examples_map = _fetch_run_predictions_examples(run_id)

    if not predictions:
        return RunMetricsResponse(run_id=run_id, metrics={}, examples_evaluated=0)

    metrics = _compute_metrics(run_data, predictions, examples_map)

    return RunMetricsResponse(
        run_id=run_id,
        metrics=metrics,
        examples_evaluated=len(predictions),
    )


@router.get("/{run_id}/export")
async def export_run_predictions(run_id: str):
    """
    Export predictions for a run as a CSV file for human evaluation.
    Columns: example_id, text, figurative_expression, predicted_replacement, gold_replacement.
    """
    run_data, predictions, examples_map = _fetch_run_predictions_examples(run_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["example_id", "text", "figurative_expression", "predicted_replacement", "gold_replacement"])

    for pred in predictions:
        det = pred.predicted_detection
        figurative = "; ".join(det.figurative_expressions) if det and det.figurative_expressions else ""
        replacement = pred.predicted_replacement or ""
        example = examples_map.get(pred.example_id)
        gold_replacement = ""
        if example and example.metadata:
            gold_replacement = example.metadata.get("gold_sentence_replacement", "")

        writer.writerow([
            pred.example_id,
            pred.input_text,
            figurative,
            replacement,
            gold_replacement,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=run_{run_id[:8]}_predictions.csv"},
    )
