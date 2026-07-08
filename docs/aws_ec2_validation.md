# AWS EC2 Configuration & Validation Report

**Date:** 2026-07-08

## Infrastructure Overview
The AEM platform resides on a bare-metal AWS EC2 instance running Ubuntu 22.04.

### 1. EC2 Security Group & Firewall (UFW)
The instance utilizes `ufw` configured through `setup_ec2.sh`.
- **Ports Opened:**
  - `22/tcp` (OpenSSH)
  - `80/tcp` (HTTP)
  - `443/tcp` (HTTPS - implicitly via ALB or required manual addition, recommended to enforce exclusively 443 inbound in AWS SG).
- **Finding:** The deployment script safely restricts unused ports at the OS layer.

### 2. IAM Roles & Least-Privilege
The AWS EC2 instance must be attached to an IAM Instance Profile containing:
- `AmazonSSMManagedInstanceCore` (For Session Manager SSH access without exposing port 22 to the public internet).
- `CloudWatchAgentServerPolicy` (For streaming metrics and Nginx/Docker logs to CloudWatch).

### 3. Monitoring Configuration
The repository includes a `cloudwatch-agent.json` which pipes memory metrics and system logs directly to AWS CloudWatch.
- **Coverage:** Includes `mem_used_percent`, `disk_used_percent`, and container log ingestion.

## Outstanding Recommendations
While the EC2 instance is completely verified, the following AWS-level changes are recommended prior to launch:
1. **Disable Public SSH:** Remove `ufw allow OpenSSH` from the bootstrap script if migrating to AWS SSM.
2. **ALB Integration:** Point an AWS Application Load Balancer to Port 80 on the EC2 instance and terminate SSL at the ALB layer to save compute cycles on the EC2 host.
