# Local Deployment Report

Date: 2026-06-29

## Scope

This report captures local production-stack validation for Release 1.0.

## Validation Status

| Check | Status | Notes |
| --- | --- | --- |
| Backend image build | Passed | Rebuilt successfully with the CPU Torch wheel and production dependency set |
| Migrate image build | Passed | Rebuilt successfully after the Alembic migration fix |
| Frontend image build | Passed | Dockerfile updated to a hardened multi-stage build |
| Production compose parse | Passed | `docker compose -f docker-compose.production.yml config` succeeded |
| Full compose bring-up | Passed | `docker compose -f docker-compose.production.yml up -d` completed with all services healthy |
| Migration execution | Passed | Alembic ran to completion on a fresh Postgres volume |
| Smoke tests | Passed | Nginx, backend, and Streamlit health endpoints returned successful responses |
| AWS shell script syntax | Passed | `bash -n` succeeded for deployment scripts |
| Runtime localhost cleanup | Passed | Remaining runtime URL references were removed or env-driven |

## Notes

- The production stack now includes backend, frontend, postgres, redis, qdrant, and nginx.
- The migration blocker was caused by an incomplete initial Alembic revision; the migration graph now includes the missing conversation/session tables before `memory_objects`.
- Qdrant health checks were updated to avoid `wget`, which is not present in the upstream image.
- This report reflects local production-stack validation only; live AWS execution remains a separate deployment step.
