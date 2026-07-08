# Retrieval (RAG)
## Purpose
Grounds agent responses in enterprise data securely.

## Architecture
Uses Qdrant as the vector store. Embeddings are generated via standard embedding models and cached.

## Flow
Query -> Generate Embedding -> Query Qdrant (cosine similarity) -> Retrieve chunks -> Inject into context window.

## Extension Points
Add hybrid search (BM25), metadata filtering, or integrate different vector stores.
