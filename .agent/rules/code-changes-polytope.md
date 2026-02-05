---
trigger: always_on
---

## Core Architecture
- Container-First Environment: All services in this project are containerized and managed via Polytope. Polytope acts as the primary orchestrator for all Docker containers.

- No Host Execution: NEVER attempt to execute code, scripts, or binaries directly on the local machine's command line. The host environment lacks the necessary dependencies and will result in failure.

## Interaction & Execution
- Access Method: To inspect the environment, get information, or execute logic, you must use either:

   1. MCP (Model Context Protocol) tools if available.

   2.`docker exec` commands targeting the specific Polytope-managed container.

- Shell Context: Always verify the active container name via Polytope before running execution commands.

- Active Container Environment: if no containers can be listed either through mcp or `docker ps`, you can ask the user to execute `pt run stack --mcp` to run the stack + mcp server. 

## Testing & Verification Workflow
- The "Endpoint-First" Rule: The easiest and most reliable way to test back-end logic is to:

   1. Draft a temporary API endpoint or trigger.

   2. Deploy/Sync the change to the container. If your changes do not involve package installs, they are hot-reloaded.

   3. Test the logic using curl from the terminal (which communicates with the containerized service).

- Cleanup: Immediately remove temporary testing endpoints and debugging code once the logic is verified.