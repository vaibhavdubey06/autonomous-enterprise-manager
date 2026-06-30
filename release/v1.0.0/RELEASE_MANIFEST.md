# v1.0.0 Release Manifest

| File | Path | Description |
| :--- | :--- | :--- |
| **Backend Service** | `apps/backend/` | Contains the core FastAPI, SQLAlchemy, and LangGraph definitions. |
| **Production Compose**| `docker-compose.production.yml` | The production orchestrator stack. |
| **Local Compose** | `docker-compose.yml` | Developer environment orchestration stack. |
| **Deployment Assets** | `deployment/` | Contains AWS, NGINX, and Compose configurations. |
| **Database Migrations**| `apps/backend/alembic/` | The state of the database schemas for v1.0.0. |
| **Tests** | `apps/backend/tests/` | Unit, integration, and release certification tests. |
| **Release Documents** | `release/v1.0.0/` | Documents outlining the deployment, rollback, and certification processes for this version. |
