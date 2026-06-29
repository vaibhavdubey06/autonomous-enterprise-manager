def test_github_indexing(client, mock_github, mocker):

    # Configure mock GitHub repository
    mock_repo = mocker.Mock()
    mock_repo.full_name = "test/repo"

    # Mock tree
    mock_tree_element = mocker.Mock()
    mock_tree_element.path = "README.md"
    mock_tree_element.type = "blob"
    mock_tree = mocker.Mock()
    mock_tree.tree = [mock_tree_element]
    mock_repo.get_git_tree.return_value = mock_tree

    # Mock file content
    mock_file = mocker.Mock()
    mock_file.decoded_content = b"# Test Repo README\nThis is a test."
    mock_repo.get_contents.return_value = mock_file

    # Mock issues
    mock_issue = mocker.Mock()
    mock_issue.pull_request = None
    mock_issue.title = "Test Issue"
    mock_issue.body = "Issue description"
    mock_issue.html_url = "http://github.com/test/repo/issues/1"
    mock_repo.get_issues.return_value = [mock_issue]

    mock_github.return_value.get_repo.return_value = mock_repo

    payload = {"repository": "test/repo"}

    response = client.post("/github/index", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "success"
    assert "repository" in data
    assert data["repository"] == "test/repo"
    assert "chunks_stored" in data
    assert data["chunks_stored"] > 0
