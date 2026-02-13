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
