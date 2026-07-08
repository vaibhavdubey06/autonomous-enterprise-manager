# Deployment
## Purpose
Guidelines for deploying AEM into production Kubernetes environments.

## Architecture
Containerized services orchestrated via Docker Compose (local) or Helm (Production).

## Flow
Build Docker image -> Push to Registry -> Apply ConfigMaps/Secrets -> Apply Deployment & HPA -> Serve traffic.

## Extension Points
Extend `docker-compose.production.yml` to include your specific monitoring stack (Prometheus, Grafana).
