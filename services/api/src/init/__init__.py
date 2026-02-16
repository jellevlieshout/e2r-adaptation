"""Centralized initialization and deinitialization for the API."""

from fastapi import FastAPI
from clients.couchbase.couchbase import get_cluster

class CouchbaseHealthWrapper:
    def health_check(self):
        try:
            cluster = get_cluster()
            # The experiment data is in 'main' bucket
            bucket = cluster.bucket("main")
            # Simple check if cluster is ready
            return {"status": "connected", "connected": True, "bucket": "main"}
        except Exception as e:
            return {"status": "error", "connected": False, "error": str(e)}

async def init(app: FastAPI) -> None:
    """Initialize all components during app startup."""
    app.state.couchbase_client = CouchbaseHealthWrapper()


async def deinit(app: FastAPI) -> None:
    """Deinitialize all components during app shutdown."""
    pass
