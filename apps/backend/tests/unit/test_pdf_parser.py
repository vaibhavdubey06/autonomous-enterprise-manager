import pytest
from app.services.ingestion.pdf_parser import extract_text_from_pdf

def test_extract_text_from_pdf(mocker, tmp_path):
    # Mock pypdf
    mock_pdfreader = mocker.patch("app.services.ingestion.pdf_parser.PdfReader")
    
    mock_doc = mocker.MagicMock()
    mock_page1 = mocker.MagicMock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = mocker.MagicMock()
    mock_page2.extract_text.return_value = "Page 2 content"
    
    # Iterator over pages
    mock_doc.pages = [mock_page1, mock_page2]
    
    mock_pdfreader.return_value = mock_doc
    
    # Dummy file
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"dummy")
    
    result = extract_text_from_pdf(str(pdf_path))
    
    assert result["total_pages"] == 2
    assert len(result["pages_data"]) == 2
    assert result["pages_data"][0]["page"] == 1
    assert result["pages_data"][0]["text"] == "Page 1 content"
    assert result["pages_data"][1]["page"] == 2
    assert result["pages_data"][1]["text"] == "Page 2 content"
    
    mock_pdfreader.assert_called_once_with(str(pdf_path))
