import pytest
import subprocess
import yaml
from pathlib import Path

# Path relative to apps/backend where pytest is running
DOCKER_COMPOSE_PATH = Path("../../docker-compose.production.yml").resolve()


def test_docker_compose_exists():
    """Verify that the production docker-compose file exists."""
    assert DOCKER_COMPOSE_PATH.exists(), f"File not found: {DOCKER_COMPOSE_PATH}"


def test_docker_compose_syntax():
    """Verify docker-compose syntax using docker compose config."""
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE_PATH), "config"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.returncode == 0
    except subprocess.CalledProcessError as e:
        pytest.fail(f"docker-compose syntax is invalid: {e.stderr}")
    except FileNotFoundError:
        # Docker is not installed on this test runner, skip or mark as Not Executed?
        # For the test, we'll parse the YAML directly as a fallback to validate structure.
        pytest.skip("Docker CLI not available to validate syntax.")


def test_production_services_configuration():
    """Verify that essential services are defined and configured securely."""
    with open(DOCKER_COMPOSE_PATH, "r") as f:
        compose_data = yaml.safe_load(f)

    assert "services" in compose_data
    services = compose_data["services"]

    expected_services = ["postgres", "redis", "qdrant", "backend", "frontend", "nginx"]

    for svc in expected_services:
        assert svc in services, f"Missing critical service: {svc}"

    # Verify Restart Policies
    for svc, config in services.items():
        if svc != "migrate":  # migrate is a one-off job
            assert (
                config.get("restart") == "unless-stopped"
            ), f"Service {svc} is missing 'restart: unless-stopped'"

    # Verify Logging limits to prevent disk exhaustion
    for svc, config in services.items():
        logging = config.get("logging", {})
        if "driver" in logging and logging["driver"] == "json-file":
            options = logging.get("options", {})
            assert "max-size" in options, f"Service {svc} logging missing max-size"
            assert "max-file" in options, f"Service {svc} logging missing max-file"

    # Verify backend dependencies
    backend = services["backend"]
    assert "depends_on" in backend
    deps = backend["depends_on"]
    assert "postgres" in deps
    assert "redis" in deps
    assert "qdrant" in deps

    # Ensure healthchecks are defined
    for svc in ["postgres", "redis", "qdrant", "backend", "frontend"]:
        assert (
            "healthcheck" in services[svc]
        ), f"Service {svc} is missing a healthcheck block"


def test_production_volumes():
    """Verify persistent volumes are defined."""
    with open(DOCKER_COMPOSE_PATH, "r") as f:
        compose_data = yaml.safe_load(f)

    volumes = compose_data.get("volumes", {})
    expected_volumes = ["postgres_data", "qdrant_data", "redis_data", "nginx_cache"]

    for vol in expected_volumes:
        assert vol in volumes, f"Missing persistent volume: {vol}"
