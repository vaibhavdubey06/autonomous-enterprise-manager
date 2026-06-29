import logging
from typing import Generator, Dict, Any
import github
from github import Github, GithubException

from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubConnector:
    """
    Connects to GitHub to fetch repository documents, issues, and PRs.
    """

    def __init__(self):
        token = settings.GITHUB_TOKEN
        if not token:
            logger.error(
                "GITHUB_TOKEN is not configured. The GitHub connector cannot start."
            )
            raise ValueError("GITHUB_TOKEN is missing in configuration.")
        self.gh = Github(auth=github.Auth.Token(token))

    def fetch_documents(
        self, repository_name: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Yields documents from a GitHub repository.
        """
        try:
            repo = self.gh.get_repo(repository_name)
        except GithubException as e:
            logger.error(f"Failed to fetch repository {repository_name}: {e}")
            raise ValueError(f"Could not access repository: {repository_name}")

        default_branch = repo.default_branch

        # 1. Fetch Markdown files from the tree
        try:
            tree = repo.get_git_tree(default_branch, recursive=True)
            for file in tree.tree:
                if file.type == "blob" and file.path.endswith(".md"):
                    content_file = repo.get_contents(file.path, ref=default_branch)
                    text = content_file.decoded_content.decode("utf-8")

                    yield {
                        "source": "github",
                        "repository": repository_name,
                        "branch": default_branch,
                        "path": file.path,
                        "url": content_file.html_url,
                        "text": text,
                    }
        except GithubException as e:
            logger.warning(f"Error fetching tree for {repository_name}: {e}")

        # 2. Fetch Latest 100 Issues & PRs
        try:
            # state="all" gets both open and closed.
            # PyGithub's get_issues returns both issues and PRs by default.
            issues = repo.get_issues(state="all", sort="updated", direction="desc")

            count = 0
            for issue in issues:
                if count >= 100:
                    break

                # Exclude empty bodies
                if not issue.body:
                    continue

                issue_type = "pull_request" if issue.pull_request else "issue"
                path = f"{issue_type}s/{issue.number}"

                text_content = f"Title: {issue.title}\n\n{issue.body}"

                yield {
                    "source": "github",
                    "repository": repository_name,
                    "branch": default_branch,
                    "path": path,
                    "url": issue.html_url,
                    "text": text_content,
                }
                count += 1

        except GithubException as e:
            logger.warning(f"Error fetching issues/PRs for {repository_name}: {e}")
