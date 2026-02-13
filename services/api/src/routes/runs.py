import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from models.entities.dataset_example import DatasetExample
from models.entities.prediction import PredictionData
from models.entities.run import RunData, RunStatus
from models.types.shared import DatasetType, PhenomenonType, TaskType
from workflows.graph import get_graph
from workflows.state import GraphState
from models.operations.evaluation import (
    compute_f1_token,
    compute_f1_span,
    compute_f1_sentence,
    compute_bleu
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


def _execute_run(run_data: RunData, limit: Optional[int] = None):
    logger.info(f"Starting run execution: {run_data.run_id}")
    
    try:
        # 1. Load dataset examples
        ks: Keyspace = DatasetExample.get_keyspace()
        
        # Use ${keyspace} placeholder which is supported by our Keyspace wrapper
        query = """
            SELECT VALUE t FROM ${keyspace} t
            WHERE t.`dataset` = $1 AND t.`phenomenon` = $2
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        rows = ks.query(
            query,
            positional_parameters=[run_data.dataset.value, run_data.phenomenon.value]
        )
             
        run_data.stats.total_examples = 0
        run_idx = 0
        
        # Get the appropriate graph
        graph = get_graph(run_data.phenomenon.value, run_data.task_type.value)
        
        # Retrieve prediction keyspace
        pred_ks = get_keyspace("predictions", bucket_name="main")
        pred_collection = pred_ks.get_collection()
        
        # Retrieve runs keyspace/collection for updates
        run_ks = get_keyspace("runs", bucket_name="main")
        run_collection = run_ks.get_collection()

        # Iterate examples
        for example_data in rows:
            run_idx += 1
            example_id = example_data.get("example_id")
            input_text = example_data.get("text", "")
            
            # Construct initial state
            state_input: GraphState = {
                "input_text": input_text,
                "dataset": run_data.dataset.value,
                "phenomenon": run_data.phenomenon.value,
                "model_name": run_data.model_name,
                "temperature": run_data.temperature,
                "detection_result": None, # Will be populated by graph
                "replacement_result": None,
                "latency_ms": 0,
                "token_usage": {},
                "errors": []
            }
            
            try:
                # Invoke graph
                result_state = graph.invoke(state_input)
                
                # Check for errors
                has_errors = len(result_state.get("errors", [])) > 0
                
                # Create Prediction document
                pred = PredictionData(
                    run_id=run_data.run_id,
                    example_id=example_id,
                    dataset=run_data.dataset,
                    phenomenon=run_data.phenomenon,
                    task_type=run_data.task_type,
                    input_text=input_text,
                    predicted_detection=result_state.get("detection_result"),
                    predicted_replacement=result_state.get("replacement_result"),
                    latency_ms=result_state.get("latency_ms"),
                    token_usage=result_state.get("token_usage"),
                    # Propagate errors in raw output? Or handle separately?
                    raw_model_output=str(result_state.get("errors")) if has_errors else None,
                    confidence=0.0 # Placeholder
                )
                
                if has_errors:
                    logger.warning(f"Errors in run {run_data.run_id} example {example_id}: {result_state['errors']}")
                    run_data.stats.failed += 1
                else:
                    run_data.stats.completed += 1
                
                # Upsert prediction
                pred_collection.upsert(pred.document_key(), pred.model_dump(mode="json"))
                
                # Update run stats periodically in DB? For now only at end to save writes
                
            except Exception as e:
                logger.error(f"Exception processing example {example_id}: {e}")
                run_data.stats.failed += 1
                
        # Update final run status
        run_data.stats.total_examples = run_idx
        
        if run_data.stats.completed == 0 and run_data.stats.failed > 0:
             run_data.status = RunStatus.FAILED
        else:
             run_data.status = RunStatus.COMPLETED
        
        # Upsert final run document
        run_collection.upsert(run_data.document_key(), run_data.model_dump(mode="json"))
        
        logger.info(f"Run {run_data.run_id} completed. Stats: {run_data.stats}")

    except Exception as e:
        logger.error(f"Run execution failed: {e}")
        run_data.status = RunStatus.FAILED
        try:
            run_ks = get_keyspace("runs", bucket_name="main")
            run_ks.get_collection().upsert(run_data.document_key(), run_data.model_dump(mode="json"))
        except:
            pass


@router.post("", response_model=RunResponse)
async def create_run(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Create and start a new experiment run.
    """
    run_id = str(uuid.uuid4())
    
    run_data = RunData(
        run_id=run_id,
        dataset=request.dataset,
        phenomenon=request.phenomenon,
        task_type=request.task_type,
        model_name=request.model_name,
        temperature=request.temperature,
        top_p=request.top_p,
        prompt_version=request.prompt_version,
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


@router.get("/{run_id}/predictions", response_model=List[PredictionData])
async def get_run_predictions(run_id: str):
    """
    Get all predictions for a specific run.
    """
    ks = get_keyspace("predictions", bucket_name="main")
    query = """
        SELECT VALUE t FROM ${keyspace} t
        WHERE t.run_id = $1
        ORDER BY t.example_id
    """
    
    rows = ks.query(query, positional_parameters=[run_id])
    return [PredictionData(**row) for row in rows]


@router.get("/{run_id}/metrics", response_model=RunMetricsResponse)
async def get_run_metrics(run_id: str):
    """
    Compute and return evaluation metrics for a run.
    """
    # 1. Fetch Run
    run_ks = get_keyspace("runs", bucket_name="main")
    try:
        run_res = run_ks.get_collection().get(f"run::{run_id}")
        run_data = RunData(**run_res.content_as[dict])
    except Exception:
        raise HTTPException(status_code=404, detail="Run not found")

    # 2. Fetch Predictions
    pred_ks = get_keyspace("predictions", bucket_name="main")
    q_preds = "SELECT VALUE t FROM ${keyspace} t WHERE t.run_id = $1"
    preds_rows = pred_ks.query(q_preds, positional_parameters=[run_id])
    predictions = [PredictionData(**row) for row in preds_rows]

    if not predictions:
         return RunMetricsResponse(run_id=run_id, metrics={}, examples_evaluated=0)

    # 3. Fetch Dataset Examples
    ds_ks = DatasetExample.get_keyspace()
    q_examples = "SELECT VALUE t FROM ${keyspace} t WHERE t.dataset = $1 AND t.phenomenon = $2"
    ex_rows = ds_ks.query(
        q_examples,
        positional_parameters=[run_data.dataset.value, run_data.phenomenon.value]
    )
    # Map example_id -> example
    examples_map = {row["example_id"]: DatasetExample(**row) for row in ex_rows}

    # 4. Compute Metrics
    # Aggregators
    all_gold_tokens = []
    all_pred_tokens = []
    
    span_metrics_sum = {"precision_span": 0.0, "recall_span": 0.0, "f1_span": 0.0}
    sentence_metrics_sum = {"f1_sentence": 0.0}
    bleu_sum = 0.0
    
    count_span = 0
    count_sentence = 0
    count_bleu = 0

    for pred in predictions:
        example = examples_map.get(pred.example_id)
        if not example:
            continue

        # A. Token Level
        # Note: We need token_labels. If not present (e.g. manual dataset might miss them), skip
        if example.token_labels is not None and pred.predicted_detection and pred.predicted_detection.token_labels is not None:
             # Ensure lengths match logic? 
             # Ideally they should map 1:1. If lengths differ, we truncate or skip?
             # For now assume they match or sklearn will complain/handle.
             # Actually, if lengths differ, sklearn throws error.
             # Let's simple append and hope for consistency, or skip if mismatch.
             gl = example.token_labels
             pl = pred.predicted_detection.token_labels
             if len(gl) == len(pl):
                 all_gold_tokens.extend(gl)
                 all_pred_tokens.extend(pl)

        # B. Span Level (Macro Average)
        if pred.predicted_detection:
            # Gold spans from example
            res = compute_f1_span(example.spans, pred.predicted_detection.spans)
            for k, v in res.items():
                span_metrics_sum[k] += v
            count_span += 1

        # C. Sentence Level
        if pred.predicted_detection:
             res = compute_f1_sentence(example.spans, pred.predicted_detection.spans)
             sentence_metrics_sum["f1_sentence"] += res["f1_sentence"]
             count_sentence += 1

        # D. BLEU (Replacement)
        if example.metadata and example.metadata.gold_sentence_replacement and pred.predicted_replacement:
             res = compute_bleu(example.metadata.gold_sentence_replacement, pred.predicted_replacement)
             bleu_sum += res["bleu"]
             count_bleu += 1

    # Finalize
    metrics = {}
    
    # Token
    if all_gold_tokens:
        token_res = compute_f1_token(all_gold_tokens, all_pred_tokens)
        metrics.update(token_res)

    # Span (Macro)
    if count_span > 0:
        for k, v in span_metrics_sum.items():
            metrics[k] = v / count_span

    # Sentence (Macro)
    if count_sentence > 0:
        metrics["f1_sentence"] = sentence_metrics_sum["f1_sentence"] / count_sentence
        
    # BLEU
    if count_bleu > 0:
         metrics["bleu"] = bleu_sum / count_bleu

    return RunMetricsResponse(
        run_id=run_id,
        metrics=metrics,
        examples_evaluated=len(predictions)
    )
