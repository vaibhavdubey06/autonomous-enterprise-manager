# Design Decisions

## 1. Supervisor Orchestration
**Options**: Centralized LLM vs Orchestrator Graph.
**Decision**: Supervisor Graph routing to specialist agents.
**Why**: Limits token context overload and enables domain isolation.