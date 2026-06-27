from enum import Enum

class GitHubAction(str, Enum):
    INDEX_REPOSITORY = "index_repository"
    CREATE_ISSUE = "create_issue"
    UPDATE_ISSUE = "update_issue"
    COMMENT_ISSUE = "comment_issue"
    CLOSE_ISSUE = "close_issue"
    LIST_ISSUES = "list_issues"
    GET_PULL_REQUESTS = "get_pull_requests"
    GET_REPOSITORY_SUMMARY = "get_repository_summary"
