from pypdf import PdfReader


def extract_text_from_pdf(file_path: str):
    reader = PdfReader(file_path)

    pages_data = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()

        if page_text:
            pages_data.append({
                "page": i + 1,
                "text": page_text
            })

    return {
        "pages_data": pages_data,
        "total_pages": len(reader.pages)
    }