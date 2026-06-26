from pydantic import BaseModel

class GitHubIndexRequest(BaseModel):
    """
    Schema for GitHub indexing request.
    """
    repository: str
