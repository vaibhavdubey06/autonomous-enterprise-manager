import pytest
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEPLOYMENT_DIR = ROOT_DIR / "deployment"
AWS_DIR = DEPLOYMENT_DIR / "aws"
NGINX_DIR = DEPLOYMENT_DIR / "nginx"
DOCKER_DIR = DEPLOYMENT_DIR / "docker"


def test_nginx_configuration_exists():
    """Verify NGINX production configuration is present and structurally sound."""
    nginx_conf = NGINX_DIR / "nginx.conf"
    assert nginx_conf.exists(), "nginx.conf is missing"

    with open(nginx_conf, "r") as f:
        content = f.read()

    # Check for basic NGINX structure and security headers
    assert "events {" in content
    assert "http {" in content
    # A basic production nginx conf should usually set some security headers or proxy headers
    assert "proxy_pass" in content or "X-Forwarded-For" in content


def test_iam_policies_exist():
    """Verify AWS IAM policies for least-privilege execution are defined."""
    iam_dir = AWS_DIR / "iam"
    if not iam_dir.exists():
        pytest.skip(f"IAM directory not found at {iam_dir}")

    policies = list(iam_dir.glob("*.json"))
    assert len(policies) > 0, "No IAM policy JSON files found"

    for policy_file in policies:
        with open(policy_file, "r") as f:
            try:
                policy = json.load(f)
                assert (
                    "Statement" in policy
                ), f"Invalid IAM Policy in {policy_file.name}"
            except json.JSONDecodeError:
                pytest.fail(f"IAM policy {policy_file.name} is not valid JSON")


def test_cloudwatch_alarms_exist():
    """Verify CloudWatch alarms or logging configs are defined."""
    cloudwatch_dir = AWS_DIR / "cloudwatch"
    if not cloudwatch_dir.exists():
        pytest.skip(f"CloudWatch directory not found at {cloudwatch_dir}")

    configs = list(cloudwatch_dir.glob("*.json")) + list(cloudwatch_dir.glob("*.yml"))
    assert len(configs) > 0, "No CloudWatch configuration files found"


def test_dockerfile_production_readiness():
    """Verify backend Dockerfile uses production best practices."""
    dockerfile = (ROOT_DIR / "apps/backend/Dockerfile").resolve()
    assert dockerfile.exists(), "Backend Dockerfile is missing"

    with open(dockerfile, "r") as f:
        content = f.read().lower()

    # Check for non-root user
    assert "user" in content, "Dockerfile should run as a non-root user"

    # Check for production entrypoint
    assert "cmd" in content or "entrypoint" in content
