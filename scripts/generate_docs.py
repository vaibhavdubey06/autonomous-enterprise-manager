import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

docs = {
    "architecture.md": """# Architecture Overview
## Purpose
The Autonomous Enterprise Manager (AEM) architecture is designed to host and execute complex multi-agent workflows at scale with enterprise-grade observability and control.

## Architecture
- **API Tier:** FastAPI exposing REST endpoints.
- **Runtime Tier:** Session management and checkpoint persistence.
- **Graph Execution:** LangGraph executing State Graphs.
- **Nodes:** Planners, Reflectors, Tool Executors.
- **Data Layer:** PostgreSQL (State), Redis (Queue), Qdrant (Vectors).

## Flow
Request -> Gateway -> Runtime (Create Session) -> LangGraph (Execution) -> Subsystems -> Response.

## Extension Points
Add custom LangGraph nodes, register new APIs in the gateway, or implement custom telemetry exporters.
""",
    "runtime.md": """# Enterprise Runtime
## Purpose
To manage the lifecycle of long-running agent workflows independent of the synchronous HTTP layer.

## Architecture
- `RuntimeManager`: Factory and registry of active sessions.
- `EnterpriseRuntime`: Concrete instance managing a single session.
- `StateStorage`: Persistence adapter.

## Flow
Client POSTs request -> `RuntimeManager` creates Session -> State is `CREATED` -> Background task starts -> State is `RUNNING` -> Wait for input -> State `PAUSED`.

## Extension Points
Implement custom state stores (e.g., RedisStateStore) or add new lifecycle event hooks.
""",
    "decision_engine.md": """# Decision Engine
## Purpose
To dynamically decompose complex user intents into executable sub-tasks (Plans).

## Architecture
Injected as a node inside the LangGraph. Connects to the LLM Gateway with specific prompting for structural decomposition.

## Flow
Receives query -> Fetches contextual tools -> LLM generates JSON plan -> Planner Node parses and queues sub-tasks into Graph State.

## Extension Points
Modify the planner prompt template, or implement alternative Planner nodes (e.g., ReAct vs. Plan-and-Solve).
""",
    "reflection_engine.md": """# Reflection Engine
## Purpose
Self-correcting node that evaluates an Agent's output against the user's goal.

## Architecture
Operates post-execution. Uses a secondary LLM call to grade the output (Pass/Fail) and generate critique.

## Flow
Agent executes task -> State moves to Reflector -> Reflector outputs Pass/Fail -> If Fail, loop back to Agent with Critique -> If Pass, proceed to End.

## Extension Points
Add strict programmatic guardrails (Regex, JSON schema validation) alongside LLM reflection.
""",
    "retrieval.md": """# Retrieval (RAG)
## Purpose
Grounds agent responses in enterprise data securely.

## Architecture
Uses Qdrant as the vector store. Embeddings are generated via standard embedding models and cached.

## Flow
Query -> Generate Embedding -> Query Qdrant (cosine similarity) -> Retrieve chunks -> Inject into context window.

## Extension Points
Add hybrid search (BM25), metadata filtering, or integrate different vector stores.
""",
    "semantic_cache.md": """# Semantic Cache
## Purpose
To intercept redundant LLM requests by identifying semantically similar prior queries, reducing latency and cost.

## Architecture
Implemented as a Middleware in the LLM Gateway. Uses vector embeddings to find distance < threshold.

## Flow
Request -> Hash/Embed -> Check Qdrant Cache Collection -> If hit, return immediately -> Else proceed to LLM -> Store result in Cache.

## Extension Points
Adjust the semantic threshold, configure eviction policies (TTL, LFU).
""",
    "workflow_packs.md": """# Workflow Packs
## Purpose
Pre-packaged, domain-specific LangGraph configurations (e.g., Software Engineering Pack, HR Pack).

## Architecture
Modular graphs that can be dynamically loaded into the main Supervisor Graph.

## Flow
Client specifies `pack_id` -> Runtime loads graph factory -> Executes specialized domain logic.

## Extension Points
Create new packs in `app/workflows/packs/` adhering to the `BaseWorkflowPack` interface.
""",
    "mcp.md": """# Model Context Protocol (MCP)
## Purpose
Standardizes how LLMs consume and interact with arbitrary enterprise data sources and tools.

## Architecture
A unified interface translating internal tool definitions into MCP-compliant JSON schema.

## Flow
Agent requests tool -> MCP Adapter formats request -> Calls external MCP server -> Parses response to agent.

## Extension Points
Register new external MCP servers in the Configuration system.
""",
    "a2a.md": """# Agent-to-Agent (A2A) Platform
## Purpose
Enables autonomous collaboration between distinct agents.

## Architecture
A registry-based service discovery pattern where agents expose capabilities via APIs.

## Flow
Agent A needs specialized task -> Queries A2A Registry -> Discovers Agent B -> Dispatches sub-request -> Awaits result.

## Extension Points
Implement network adapters to call agents across different microservices.
""",
    "connectors.md": """# Connectors
## Purpose
Native, secure wrappers around external Enterprise systems (GitHub, Slack, Jira).

## Architecture
`BaseConnector` interface with concrete implementations handling auth, rate-limiting, and error recovery.

## Flow
Agent decides to use Connector -> Connector fetches Auth token from `CredentialManager` -> Executes API call -> Returns parsed data.

## Extension Points
Subclass `BaseConnector` to add support for new platforms (e.g., Salesforce, ServiceNow).
""",
    "benchmarking.md": """# Benchmarking Framework
## Purpose
To continuously evaluate the platform's AI Quality, Runtime health, and Infrastructure resilience via procedurally generated E2E scenarios.

## Architecture
`ScenarioFactory` -> `E2ERunner` -> Validators (Subsystem Coverage, Playwright TTFT, Resource Load) -> `ReportGenerator`.

## Flow
Run `make benchmark` -> Spin up test clients -> Execute 300+ scenarios -> Output `engineering_report.md`.

## Extension Points
Add new procedural rules in `ScenarioFactory` or integrate new OpenTelemetry validators.
""",
    "deployment.md": """# Deployment
## Purpose
Guidelines for deploying AEM into production Kubernetes environments.

## Architecture
Containerized services orchestrated via Docker Compose (local) or Helm (Production).

## Flow
Build Docker image -> Push to Registry -> Apply ConfigMaps/Secrets -> Apply Deployment & HPA -> Serve traffic.

## Extension Points
Extend `docker-compose.production.yml` to include your specific monitoring stack (Prometheus, Grafana).
""",
    "api.md": """# API Reference
## Purpose
To document the public REST interface for clients communicating with AEM.

## Architecture
FastAPI OpenAPI spec auto-generated at `/docs`.

## Flow
Clients interact primarily via `/api/v1/agent/chat` which initiates a streaming or synchronous graph session.

## Extension Points
Add new routers in `app/api/v1/` and register them in `app/main.py`.
"""
}

for filename, content in docs.items():
    filepath = os.path.join(DOCS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
print("Documentation generated successfully.")
