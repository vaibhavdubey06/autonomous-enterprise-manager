# Workflow Packs
## Purpose
Pre-packaged, domain-specific LangGraph configurations (e.g., Software Engineering Pack, HR Pack).

## Architecture
Modular graphs that can be dynamically loaded into the main Supervisor Graph.

## Flow
Client specifies `pack_id` -> Runtime loads graph factory -> Executes specialized domain logic.

## Extension Points
Create new packs in `app/workflows/packs/` adhering to the `BaseWorkflowPack` interface.
