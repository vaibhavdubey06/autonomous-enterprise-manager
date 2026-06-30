# Post-Deployment Checklist (v1.0.0)

Execute these steps immediately following a successful deployment of the v1.0.0 stack.

- [ ] **1. Log Verification**
  - [ ] Check backend logs for startup errors (`docker compose logs backend`).
  - [ ] Check NGINX logs for proxy resolution (`docker compose logs nginx`).
- [ ] **2. Infrastructure Verification**
  - [ ] Verify Database Connectivity (Run `alembic current` or connect via psql).
  - [ ] Verify Qdrant Health (Hit `:6333/readyz`).
  - [ ] Verify Redis Health (Execute `redis-cli ping`).
- [ ] **3. Security & DNS Verification**
  - [ ] Confirm SSL/TLS termination is functioning at the edge/load-balancer.
  - [ ] Confirm Domain DNS resolution points to the new production endpoints.
  - [ ] Verify API endpoints block unauthenticated requests (e.g. `curl -I https://api.domain.com/api/v1/memory/sessions`).
- [ ] **4. Monitoring Setup**
  - [ ] Verify CloudWatch Agent is actively publishing logs.
  - [ ] Verify Prometheus/Grafana (if deployed) is successfully scraping `/metrics`.
- [ ] **5. Backup Validation**
  - [ ] Trigger a manual RDS/Database backup to ensure backup pipelines are active.
  - [ ] Document the Snapshot ARN/ID.
