# User Notes

- Use MCP tools (`mcp_polytope_exec`, `mcp_polytope_get-container-logs`, `mcp_polytope_list-containers`) to inspect containers and run commands inside them.
- **Do NOT use `docker exec` directly** — use `mcp_polytope_exec` instead.

## Coding Patterns

- **Endpoint-First Testing**: When debugging backend logic (especially DB connections), create a temporary API endpoint (e.g., `GET /debug-cb`) to run the code in the actual service environment. This is often more reliable than `python -c` via exec, as it guarantees the correct import paths and environment variables are present.

- **Couchbase Bucket Override**: The project uses a `main` bucket for collections, but the `COUCHBASE_BUCKET` env var might default to `default`. If `BaseModelCouchbase` fails to find a collection, ensure the model class explicitly overrides `_bucket_name = "main"` and `get_keyspace()`.
