# User Notes

- Use MCP tools (`mcp_polytope_exec`, `mcp_polytope_get-container-logs`, `mcp_polytope_list-containers`) to inspect containers and run commands inside them.
- **Do NOT use `docker exec` directly** — use `mcp_polytope_exec` instead.

## Coding Patterns

- **Endpoint-First Testing**: When debugging backend logic (especially DB connections), create a temporary API endpoint (e.g., `GET /debug-cb`) to run the code in the actual service environment. This is often more reliable than `python -c` via exec, as it guarantees the correct import paths and environment variables are present.

- **Couchbase Bucket Override**: The project uses a `main` bucket for collections, but the `COUCHBASE_BUCKET` env var might default to `default`. If `BaseModelCouchbase` fails to find a collection, ensure the model class explicitly overrides `_bucket_name = "main"` and `get_keyspace()`.

## OpenRouter Free Models (Feb 2026)

The project currently relies on free-tier models on OpenRouter. Recommended models:

| Provider | Model Name | ID (Approx) | Context | Notes |
|----------|------------|-------------|---------|-------|
| Mistral | Mistral Small 3.1 24B | `mistralai/mistral-small-24b-instruct-2501:free` | 128k | 24B params, strong reasoning/coding. |
| Google | Gemma 3 12B | `google/gemma-3-12b-it:free` | 128k (or 33k?) | Multimodal, 140+ languages. |
| Google | Gemma 3 4B | `google/gemma-3-4b-it:free` | 128k (or 33k?) | Efficient, multimodal. |
| Google | Gemma 3n 2B | `google/gemma-3n-2b-it:free` | 32k | Low resource, fast. |
| Nous | Hermes 3 405B Instruct | `nousresearch/hermes-3-llama-3.1-405b:free` | 131k | Frontier-level, 405B params. |
| Qwen | Qwen3 4B | `qwen/qwen-3-4b-instruct:free` | 41k | Dual-mode thinking/non-thinking. |
| Meta | Llama 3.2 3B Instruct | `meta-llama/llama-3.2-3b-instruct:free` | 131k | Multilingual, fast. |

**Note**: Always verify the exact model ID on OpenRouter as they change frequently.

## Frontend Data Flow & State Management

**Architecture Pattern**:
1. **Page/Component**: Renders UI, uses Custom Hook.
2. **Custom Hook** (`hooks/use-*.ts`): Wraps TanStack Query `useQuery`/`useMutation`.
3. **TanStack Query**: Handles caching, loading states, refetching.
4. **API Client** (`lib/api.ts`): Typed functions making `fetch` calls.
5. **Backend API**: Processes request.

**Rules**:
- Do NOT use `useEffect` for data fetching. Use `useQuery`.
- Do NOT make `fetch` calls directly in components.
- Always type API responses with TypeScript interfaces in `lib/api.ts`.

## Component Architecture & Best Practices

- **Examples**:
  - `View`: Renders UI (JSX).
  - `Presenter`: Custom hook handling logic/data.
  - `Model`: TypeScript interfaces/types.
- **Encapsulation**: Components should be small and focused.
- **MVP Separation**: Separate logic (Presenter) from UI (View).
- **Size Limit**: Files > 300 lines **MUST** be refactored into sub-components.
- **Audit**: If you encounter a file violating these rules, add a TODO to TODOS.md to refactor it.

## Verification
- **Frontend Verification**: Front-end fixes or changes should always be verified in the browser by the agent. The front end is running at http://localhost:51732.
