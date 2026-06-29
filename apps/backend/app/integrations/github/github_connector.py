from app.integrations.base.connector_registry import connector_registry
from typing import Dict, Any, List, Optional
import github
from github import Github, GithubException
from app.integrations.base.base_connector import BaseConnector
from app.integrations.schemas.connector_models import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    ExecutionRequest,
    ExecutionResponse,
    AuthType,
)


class GitHubConnector(BaseConnector):
    @classmethod
    def get_metadata(cls) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="github",
            version="1.0.0",
            description="Integration for GitHub Repositories and Issues",
            supported_auth_types=[AuthType.PAT],
            capabilities=["github.index_repository"],
        )

    def connect(self) -> None:
        self.gh: Optional[Github] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        token = credentials.get("token")
        if not token:
            return False
        try:
            self.gh = Github(auth=github.Auth.Token(token))
            return True
        except Exception:
            return False

    def health_check(self) -> ConnectorHealthStatus:
        if not self.gh:
            return ConnectorHealthStatus.DISCONNECTED
        try:
            # A simple lightweight call to check validity
            user = self.gh.get_user().login
            if user:
                return ConnectorHealthStatus.HEALTHY
            return ConnectorHealthStatus.WARNING
        except GithubException as e:
            if e.status in [401, 403]:
                return ConnectorHealthStatus.AUTH_FAILED
            return ConnectorHealthStatus.ERROR
        except Exception:
            return ConnectorHealthStatus.ERROR

    def discover_capabilities(self) -> List[str]:
        return self.get_metadata().capabilities

    def validate_permissions(self, capability: str) -> bool:
        # Check if the user has this permission on GitHub side if needed
        # Or if the Identity in context has permission.
        # For this exercise, simple logic:
        return capability in self.discover_capabilities()

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        if request.capability == "github.index_repository":
            repo_name = request.parameters.get("repository")
            if not repo_name:
                return ExecutionResponse(
                    success=False, data=None, error_message="Repository name required"
                )

            try:
                repo = self.gh.get_repo(repo_name)
                # Instead of indexing to Qdrant directly here, we return the docs
                # so the caller (or integration service) can pipeline it.
                # However, the previous impl indexed them. We'll simulate yielding the documents
                # and in a real pipeline they'd be sent to the ingestion service.

                # Fetching default branch and a few markdown files for demonstration
                default_branch = repo.default_branch
                tree = repo.get_git_tree(default_branch, recursive=True)
                docs = []
                count = 0
                for file in tree.tree:
                    if count > 5:  # limit for speed during mock tests
                        break
                    if file.type == "blob" and file.path.endswith(".md"):
                        content_file = repo.get_contents(file.path, ref=default_branch)
                        text = content_file.decoded_content.decode("utf-8")
                        docs.append(
                            {
                                "source": "github",
                                "repository": repo_name,
                                "path": file.path,
                                "url": content_file.html_url,
                                "text": text,
                            }
                        )
                        count += 1

                return ExecutionResponse(success=True, data={"documents": docs})

            except GithubException as e:
                return ExecutionResponse(success=False, data=None, error_message=str(e))

        return ExecutionResponse(
            success=False, data=None, error_message="Capability not found"
        )

    def disconnect(self) -> None:
        if self.gh:
            self.gh.close()
            self.gh = None

    def cleanup(self) -> None:
        self.disconnect()


# Auto register


connector_registry.register(GitHubConnector)
