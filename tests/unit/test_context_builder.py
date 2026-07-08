from app.graph.context_builder import build_merged_context


def test_build_merged_context():
    memory_context = "user: hello\nassistant: hi"
    reranked_chunks = [
        {
            "source": "document",
            "document": "test.pdf",
            "page": 1,
            "text": "doc content",
        },
        {
            "source": "github",
            "repository": "test/repo",
            "path": "file.py",
            "text": "code content",
        },
        {"source": "conversation", "role": "user", "text": "conv content"},
    ]
    tool_results = [
        {"status": "executed", "name": "mock_tool", "result": "mock result"}
    ]

    merged_context, context_texts, sources = build_merged_context(
        memory_context, reranked_chunks, tool_results
    )

    assert "--- WORKING MEMORY ---" in merged_context
    assert "user: hello" in merged_context
    assert "--- RETRIEVED CONTEXT ---" in merged_context
    assert "doc content" in merged_context
    assert "code content" in merged_context
    assert "--- TOOL RESULTS ---" in merged_context
    assert "mock result" in merged_context

    assert len(context_texts) == 3
    assert len(sources) == 3
    assert sources[0]["document"] == "test.pdf"
    assert sources[1]["repository"] == "test/repo"
    assert sources[2]["role"] == "user"
