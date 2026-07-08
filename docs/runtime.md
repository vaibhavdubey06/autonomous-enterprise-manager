# Enterprise Runtime
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
