# v1.0.0 Deployment Guide

## Prerequisites
- Docker (v24+)
- Docker Compose (v2+)
- AWS CLI configured (if pulling images from ECR)
- Target Server Instance (e.g. AWS EC2, t3.large or greater recommended)

## 1. Prepare the Environment
1. Clone the release branch: `git clone -b v1.0.0 https://github.com/your-org/autonomous-enterprise-manager.git`
2. Enter the target environment configuration: `cp .env.example .env`
3. Fill out the `.env` file with production secrets, database URIs, and LLM API keys.

## 2. Startup Dependencies
First, spin up persistent backing services to ensure they initialize properly:
```bash
docker compose -f docker-compose.production.yml up -d postgres redis qdrant
```
Wait for services to reach a healthy state. Verify via `docker compose -f docker-compose.production.yml ps`.

## 3. Run Database Migrations
Run the Alembic migrations against the production database to apply the latest schemas:
```bash
docker compose -f docker-compose.production.yml up migrate
```

## 4. Spin up the Application Stack
Launch the frontend, backend, and reverse proxy layers:
```bash
docker compose -f docker-compose.production.yml up -d backend frontend nginx
```

## 5. Validate the Deployment
Verify the deployment by requesting the health endpoints:
```bash
curl -f http://localhost/health/ready
curl -f http://localhost/health/live
```
If both return `200 OK`, the deployment was successful. proceed to `POST_DEPLOYMENT_CHECKLIST.md`.
