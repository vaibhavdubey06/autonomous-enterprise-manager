def test_upload_document(client, mocker):
    mocker.patch(
        "app.api.v1.upload.extract_text_from_pdf",
        return_value={
            "pages_data": [{"page": 1, "text": "dummy text"}],
            "total_pages": 1,
        },
    )
    mocker.patch(
        "app.api.v1.upload.chunk_text", return_value=[{"page": 1, "text": "dummy text"}]
    )
    # Create a dummy PDF content
    pdf_content = b"%PDF-1.4 dummy pdf content"

    files = {"file": ("test_doc.pdf", pdf_content, "application/pdf")}

    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert data["filename"] == "test_doc.pdf"
    assert data["pages"] == 1
    assert data["stored"] is True
