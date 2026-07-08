# Security Policy

## Supported Versions

Currently, the following versions are supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| v1.0.x  | :white_check_mark: |
| < v1.0  | :x:                |

## Reporting a Vulnerability

Security is a top priority for the Autonomous Enterprise Manager. If you discover a vulnerability, please do NOT open a public issue.

Instead, please email your findings to **security@example.com**. 
We aim to respond to all reports within 48 hours.

When reporting, please provide:
* A description of the vulnerability.
* Steps to reproduce the issue.
* Potential impact.

## Best Practices
* **Secrets Management**: Never commit `.env` files. Ensure you use strict RBAC on your deployment infrastructure.
* **Network Isolation**: When deploying A2A or MCP platforms, ensure they are placed within an internal VPC.
* **Rate Limiting**: Always place a WAF/Rate-limiting proxy (e.g., NGINX, Cloudflare) in front of the FastAPI backend to protect against abuse.
