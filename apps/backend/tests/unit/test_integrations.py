from app.integrations.base.connector_registry import connector_registry
from app.integrations.schemas.connector_models import ConnectorState
from app.integrations.services.integration_service import integration_service

import unittest.mock as mock


def test_connector_registry():
    connectors = connector_registry.list_connectors()
    names = [c.name for c in connectors]
    assert "github" in names
    assert "jira" in names
    assert "slack" in names
    assert "notion" in names
    assert "gmail" in names
    assert "google_drive" in names


@mock.patch("app.integrations.github.github_connector.Github")
def test_scenario_1_cto_repo_review(mock_github):
    tenant_id = "tenant-1"
    config_data = {"token": "dummy-token"}  # This normally goes via SecretManager

    # Configure mock
    mock_gh_instance = mock.MagicMock()
    mock_github.return_value = mock_gh_instance
    mock_gh_instance.get_user().login = "testuser"
    mock_repo = mock.MagicMock()
    mock_gh_instance.get_repo.return_value = mock_repo
    mock_repo.default_branch = "main"
    mock_tree = mock.MagicMock()
    mock_repo.get_git_tree.return_value = mock_tree
    mock_tree.tree = []

    # Mock SecretManager directly in the test to provide the token
    with mock.patch(
        "app.integrations.authentication.credential_manager.secret_manager.get_secret",
        return_value="dummy-token",
    ):
        # 1. Connect and initialize GitHub
        config = integration_service.connect(tenant_id, "github", "pat", config_data)
        assert config.state == ConnectorState.READY

        resp = integration_service.execute(
            tenant_id,
            config.connector_id,
            "github.index_repository",
            {"repository": "owner/repo"},
        )
        assert resp.success is True


def test_scenario_2_ceo_project_status():
    tenant_id = "tenant-1"
    with mock.patch(
        "app.integrations.authentication.credential_manager.secret_manager.get_secret",
        return_value="api-key",
    ):
        config = integration_service.connect(
            tenant_id, "jira", "api_key", {"token": "x"}
        )
        assert config.state == ConnectorState.READY

        resp = integration_service.execute(
            tenant_id, config.connector_id, "jira.get_project_status", {}
        )
        assert resp.success is True
        assert resp.data["project"] == "AEM"


def test_scenario_3_executive_design_docs():
    tenant_id = "tenant-1"
    with mock.patch(
        "app.integrations.authentication.credential_manager.secret_manager.get_secret",
        return_value="oauth2-token",
    ):
        config = integration_service.connect(
            tenant_id, "google_drive", "oauth2", {"token": "x"}
        )
        assert config.state == ConnectorState.READY

        resp = integration_service.execute(
            tenant_id, config.connector_id, "drive.read_document", {}
        )
        assert resp.success is True
        assert "documents" in resp.data


def test_scenario_4_slack_auth_expires():
    tenant_id = "tenant-1"
    # Provide the magic 'expired' token to simulate expiration
    with mock.patch(
        "app.integrations.authentication.credential_manager.secret_manager.get_secret",
        return_value="expired",
    ):
        config = integration_service.connect(
            tenant_id, "slack", "oauth2", {"token": "expired"}
        )

        # Authenticate will fail
        assert config.state == ConnectorState.ERROR

        # Trying to execute should be blocked
        resp = integration_service.execute(
            tenant_id, config.connector_id, "slack.read_channel", {}
        )
        assert resp.success is False
        assert "not ready" in resp.error_message
