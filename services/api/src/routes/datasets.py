"""
Dataset ingestion API routes.
Handles loading raw datasets into Couchbase.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from clients.vuamc import VUAMCClient
from clients.semeval2022.client import SemEval2022Client
from models.entities.dataset_example import DatasetExample
from models.operations.ingestion import (
    parse_vu_sentence,
    parse_semeval_sample,
    build_semeval_replacement_map,
)
from clients.couchbase.couchbase import get_keyspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["datasets"])

# Dataset file paths inside the container
VU_DATASET_PATH = "/datasets/vu-amsterdam-metaphor-corpus/VUAMC.xml"
SEMEVAL_DATASET_PATH = "/datasets/SemEval2022_Task2"


class IngestRequest(BaseModel):
    dataset: str  # "vu_amsterdam" or "semeval"
    language: Optional[str] = "EN"  # Language filter (SemEval only)


class IngestResponse(BaseModel):
    ingested: int
    errors: int
    message: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_dataset(request: IngestRequest):
    """
    Ingest a dataset into Couchbase.
    Reads raw files, converts to DatasetExampleData, and upserts into the datasets collection.
    """
    if request.dataset == "vu_amsterdam":
        return _ingest_vu_amsterdam()
    elif request.dataset == "semeval":
        return _ingest_semeval(language=request.language)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dataset: {request.dataset}. Must be 'vu_amsterdam' or 'semeval'.",
        )


def _ingest_vu_amsterdam() -> IngestResponse:
    """Ingest all VU Amsterdam sentences into Couchbase."""
    logger.info("Starting VU Amsterdam ingestion")

    try:
        client = VUAMCClient(VU_DATASET_PATH)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Dataset file not found: {e}")

    ingested = 0
    errors = 0

    for doc in client.documents():
        for sentence in doc.sentences:
            try:
                data = parse_vu_sentence(doc.id, sentence)
                DatasetExample.create_with_key(data)
                ingested += 1
            except Exception as e:
                errors += 1
                if errors <= 10:
                    logger.warning(f"Error ingesting VU sentence {doc.id}_s{sentence.id}: {e}")

        if ingested % 500 == 0 and ingested > 0:
            logger.info(f"VU Amsterdam: ingested {ingested} sentences so far...")

    logger.info(f"VU Amsterdam ingestion complete: {ingested} ingested, {errors} errors")
    return IngestResponse(
        ingested=ingested,
        errors=errors,
        message=f"VU Amsterdam: {ingested} sentences ingested, {errors} errors",
    )


def _ingest_semeval(language: Optional[str] = "EN") -> IngestResponse:
    """Ingest SemEval Task A samples into Couchbase, enriched with Task B data."""
    logger.info(f"Starting SemEval ingestion (language={language})")

    try:
        client = SemEval2022Client(SEMEVAL_DATASET_PATH)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Dataset file not found: {e}")

    # Build replacement map from SubTask B
    replacement_map = build_semeval_replacement_map(client)

    ingested = 0
    errors = 0

    for sample in client.list_samples(task='A', language=language):
        try:
            data = parse_semeval_sample(sample, replacement_map)
            if data is not None:
                DatasetExample.create_with_key(data)
                ingested += 1
        except Exception as e:
            errors += 1
            if errors <= 10:
                logger.warning(f"Error ingesting SemEval sample {sample.id}: {e}")

        if ingested % 500 == 0 and ingested > 0:
            logger.info(f"SemEval: ingested {ingested} samples so far...")

    logger.info(f"SemEval ingestion complete: {ingested} ingested, {errors} errors")
    return IngestResponse(
        ingested=ingested,
        errors=errors,
        message=f"SemEval: {ingested} samples ingested, {errors} errors",
    )


class DatasetStats(BaseModel):
    total: int
    vu_amsterdam: int
    semeval: int
    manual: int


@router.get("/stats", response_model=DatasetStats)
async def get_dataset_stats():
    """Return counts of dataset examples per dataset type."""
    keyspace = get_keyspace("datasets", bucket_name="main")

    try:
        total_rows = keyspace.query(f"SELECT COUNT(*) as cnt FROM {keyspace}")
        total = total_rows[0]["cnt"] if total_rows else 0

        vu_rows = keyspace.query(
            f"SELECT COUNT(*) as cnt FROM {keyspace} WHERE `dataset` = 'vu_amsterdam'"
        )
        vu_count = vu_rows[0]["cnt"] if vu_rows else 0

        se_rows = keyspace.query(
            f"SELECT COUNT(*) as cnt FROM {keyspace} WHERE `dataset` = 'semeval'"
        )
        se_count = se_rows[0]["cnt"] if se_rows else 0

        manual_rows = keyspace.query(
            f"SELECT COUNT(*) as cnt FROM {keyspace} WHERE `dataset` = 'manual'"
        )
        manual_count = manual_rows[0]["cnt"] if manual_rows else 0

        return DatasetStats(
            total=total,
            vu_amsterdam=vu_count,
            semeval=se_count,
            manual=manual_count,
        )
    except Exception as e:
        logger.error(f"Error querying dataset stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying stats: {e}")
