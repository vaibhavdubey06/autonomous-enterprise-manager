# v1.0.0 Rollback Guide

In the event of a catastrophic failure during the v1.0.0 deployment, follow this rollback procedure to restore service to the previous stable state.

## 1. Stop Incoming Traffic
Update your load balancer or NGINX edge node to display a maintenance page, or scale the NGINX ingress to 0 to prevent user requests from hitting the faulty backend.

## 2. Revert Docker Stack
Bring down the failing application tier:
```bash
docker compose -f docker-compose.production.yml down
```
If rolling back to a previous major version, check out the previous stable tag (e.g. `v0.9.5`):
```bash
git checkout tags/v0.9.5
```

## 3. Database Downgrade (If Applicable)
If database schemas were changed during the deployment and those changes are incompatible with the rollback version, run alembic downgrade:
```bash
docker compose -f docker-compose.production.yml run --rm backend alembic downgrade base # or specific revision
```
*Note: Always take a database snapshot/backup prior to ANY production deployment so that manual restoration is possible.*

## 4. Restore Previous Stack
Bring the previous application stack back online:
```bash
docker compose -f docker-compose.production.yml up -d backend frontend nginx
```

## 5. Verify Stability
Monitor logs and CloudWatch metrics. Verify that error rates have stabilized.
```bash
docker compose -f docker-compose.production.yml logs -f --tail=100
```
Once stable, restore incoming traffic routing.
