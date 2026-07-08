def test_search_endpoint(client, mocker):

    # Mock qdrant search
    mocker.patch(
        "app.api.v1.search.search",
        return_value=[
            {
                "text": "mocked search result",
                "score": 0.95,
                "metadata": {"source": "test.pdf", "page": 1},
            }
        ],
    )

    payload = {"query": "test query"}

    response = client.post("/api/v1/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["text"] == "mocked search result"
