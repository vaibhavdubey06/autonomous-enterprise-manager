def chunk_text(
    pages_data: list[dict],
    chunk_size: int = 500,
    overlap: int = 50,
):
    chunks = []

    for page_info in pages_data:
        text = page_info["text"]
        page_num = page_info["page"]
        
        start = 0

        while start < len(text):
            end = start + chunk_size

            chunks.append({
                "page": page_num,
                "text": text[start:end]
            })

            start += chunk_size - overlap

    return chunks