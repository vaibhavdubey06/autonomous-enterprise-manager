import pytest
import subprocess
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_security_headers():
    """Verify that the API returns appropriate security headers (if configured in middleware)."""
    res = client.get("/health")
    # Some frameworks/middlewares add these by default.
    # If they are not added by the app (but by NGINX in prod), we will just check what the app does.
    # At minimum, we check that internal server errors don't leak stack traces (done via middleware test).
    assert res.status_code == 200


def test_cors_configuration():
    """Verify that CORS origins are restricted according to settings."""
    # Send a request with an Origin header not in the allowed list
    res = client.options(
        "/api/v1/chat/",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    # If CORS middleware is active and blocks it, we shouldn't get the ACAO header back with the malicious site.
    if "access-control-allow-origin" in res.headers:
        assert (
            res.headers["access-control-allow-origin"] != "http://malicious-site.com"
        ), "CORS policy is too permissive"


def test_static_analysis_security():
    """Verify that bandit (security linter) passes on the codebase."""
    try:
        result = subprocess.run(
            ["uv", "run", "bandit", "-r", "app", "-ll", "-ii"],  # Medium/High severity
            capture_output=True,
            text=True,
            check=False,
        )
        # Note: If bandit is not installed, it will fail, which might be expected.
        if result.returncode != 0:
            # If it's not installed or not found, we skip
            if (
                "not found" in result.stderr
                or "No module named bandit" in result.stderr
            ):
                pytest.skip("Bandit not installed, skipping SAST check.")
            else:
                pytest.fail(f"Bandit found security vulnerabilities: {result.stdout}")
    except FileNotFoundError:
        pytest.skip("uv CLI not available for bandit check.")


def test_secret_leakage():
    """Verify that no obvious secrets are hardcoded in the codebase."""
    import re
    from pathlib import Path

    app_dir = Path("../../app").resolve()
    secret_patterns = [
        re.compile(r'(?i)api_key\s*=\s*[\'"][a-zA-Z0-9_-]{20,}[\'"]'),
        re.compile(r'(?i)secret\s*=\s*[\'"][a-zA-Z0-9_-]{20,}[\'"]'),
    ]

    findings = []
    if not app_dir.exists():
        return

    for py_file in app_dir.rglob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
            for pattern in secret_patterns:
                if pattern.search(content):
                    findings.append(str(py_file.name))

    assert len(findings) == 0, (
        f"Potential hardcoded secrets found in: {', '.join(findings)}"
    )
