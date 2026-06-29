# AWS Deployment Report

Date: 2026-06-29

## Infrastructure Topology

- EC2 Ubuntu 22.04 LTS
- Docker Engine
- Docker Compose production stack
- Nginx reverse proxy
- FastAPI backend
- Streamlit frontend
- PostgreSQL
- Redis
- Qdrant
- CloudWatch agent

## Deployment Architecture

The application remains containerized and modular so the platform can later migrate to ECS, EKS, or managed AWS services without application changes.

## Validation Targets

| Metric | Status | Notes |
| --- | --- | --- |
| P50 / P95 / P99 | Pending AWS run | To be collected from the evaluation framework after EC2 deployment |
| Startup time | Validated locally | The full compose stack reached healthy state after a clean rebuild and migration run |
| CloudWatch metrics | Configured | CloudWatch agent configuration is included for AWS rollout |
| Resource utilization | Pending AWS run | CPU, memory, disk, and network should be collected on host and container levels |
| Rollback validation | Scripted | Rollback script is included in `deployment/aws/rollback.sh` |

## Cloud Costs

- Free Tier compatible design intent: yes.
- Actual AWS cost: pending live deployment and measurement.

## Known Limitations

- This report documents AWS deployment readiness rather than a completed EC2 launch in this workspace.
- Secrets must be sourced from GitHub Actions or AWS runtime configuration for production use.
- Local validation confirmed the production stack, migration flow, and health checks before AWS rollout.
