# API Reference
## Purpose
To document the public REST interface for clients communicating with AEM.

## Architecture
FastAPI OpenAPI spec auto-generated at `/docs`.

## Flow
Clients interact primarily via `/api/v1/agent/chat` which initiates a streaming or synchronous graph session.

## Extension Points
Add new routers in `app/api/v1/` and register them in `app/main.py`.
