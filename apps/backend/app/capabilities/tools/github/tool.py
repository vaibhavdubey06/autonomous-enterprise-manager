import logging
from typing import Dict, Any
from app.capabilities.base.base_capability import BaseCapability
from app.capabilities.base.schemas import Capability, CapabilityType
from app.capabilities.tools.github.actions import GitHubAction

logger = logging.getLogger(__name__)


class GitHubCapability(BaseCapability):
    """
    Capability for interacting with GitHub.
    Wraps the existing GitHubConnector.
    """

    def __init__(self, github_connector=None):
        # We optionally inject the connector to allow mocking, or lazy load it.
        # But for the capability registry, it's better to inject it.
        self.connector = github_connector

    def get_metadata(self) -> Capability:
        return Capability(
            capability_id="github_tool",
            name="GitHub Capability",
            description="Interacts with GitHub repositories, issues, and PRs.",
            type=CapabilityType.TOOL,
            supported_actions=[
                GitHubAction.INDEX_REPOSITORY.value,
                GitHubAction.CREATE_ISSUE.value,
                GitHubAction.UPDATE_ISSUE.value,
                GitHubAction.COMMENT_ISSUE.value,
                GitHubAction.CLOSE_ISSUE.value,
                GitHubAction.LIST_ISSUES.value,
                GitHubAction.GET_PULL_REQUESTS.value,
                GitHubAction.GET_REPOSITORY_SUMMARY.value,
            ],
            required_permissions=["github:read", "github:write"],
            supported_agents=["CTO Agent", "Knowledge Agent"],
            input_schema={
                "repository_name": "str",
                "issue_number": "int (optional)",
                "title": "str (optional)",
                "body": "str (optional)",
            },
            output_schema={"status": "str", "data": "dict or list"},
        )

    def _execute_internal(self, action: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:

        repository_name = kwargs.get("repository_name")
        if not repository_name:
            raise ValueError("repository_name is required for GitHub capabilities.")

        if action == GitHubAction.INDEX_REPOSITORY.value:
            if not self.connector:
                from app.services.connectors.github.connector import GitHubConnector

                try:
                    self.connector = GitHubConnector()
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize GitHubConnector: {e}")

            docs = list(self.connector.fetch_documents(repository_name))
            return {
                "message": f"Successfully fetched {len(docs)} documents.",
                "document_count": len(docs),
                # returning a preview instead of the entire text payload
                "documents": [{"path": d["path"], "url": d["url"]} for d in docs],
            }

        elif action == GitHubAction.GET_REPOSITORY_SUMMARY.value:
            # We can approximate a summary by just returning document counts and top issues
            if not self.connector:
                from app.services.connectors.github.connector import GitHubConnector

                self.connector = GitHubConnector()

            docs = list(self.connector.fetch_documents(repository_name))
            issues = [
                d
                for d in docs
                if "issues/" in d["path"] or "pull_requests/" in d["path"]
            ]
            md_files = [d for d in docs if d["path"].endswith(".md")]

            return {
                "summary": f"Repository {repository_name} contains {len(md_files)} markdown documents and {len(issues)} recent issues/PRs.",
                "total_artifacts": len(docs),
            }

        else:
            # Not Implemented for future phases
            return {
                "status": "Not Implemented",
                "message": f"Action {action} is defined in interface but not yet implemented.",
            }
