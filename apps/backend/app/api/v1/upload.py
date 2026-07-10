from pathlib import Path
import tempfile

from fastapi import APIRouter, UploadFile, File

from app.services.ingestion.pdf_parser import extract_text_from_pdf
from app.services.ingestion.text_chunker import chunk_text
from app.services.embeddings.embedding_service import embed_batch
from app.services.vectorstore.qdrant_service import (
    create_collection,
    store_chunks,
)

router = APIRouter()


@router.post("")
async def upload_document(file: UploadFile = File(...)):
    # Validate PDF
    if file.content_type != "application/pdf":
        return {"error": "Only PDF files are supported"}

    # Save uploaded file temporarily
    filename = file.filename or "unknown"
    suffix = Path(filename).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()

        temp_file.write(content)

        temp_path = temp_file.name

    # Extract text
    result = extract_text_from_pdf(temp_path)

    pages_data = result["pages_data"]
    total_pages = result["total_pages"]

    # Chunk text
    chunks = chunk_text(pages_data)

    # Ensure vector store collection exists
    create_collection()

    # Generate embeddings (we only need the text part)
    chunk_texts = [c["text"] for c in chunks]
    embeddings = embed_batch(chunk_texts)

    # Store vectors
    store_chunks(
        chunks=chunks,
        embeddings=embeddings,
        document_name=filename,
    )

    # Calculate total characters from pages_data
    total_characters = sum(len(p["text"]) for p in pages_data)

    return {
        "filename": filename,
        "pages": total_pages,
        "characters": total_characters,
        "chunks": len(chunks),
        "stored": True,
    }
