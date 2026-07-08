# Known Limitations & Technical Debt (v1.0)

**Date:** 2026-07-08

While v1.0 is fully certified for production, the following limitations are documented for engineering transparency.

## 1. Remaining Risks
- **LLM Rate Limits:** At 120 req/s concurrent throughput, enterprise clients hitting the Gemini/OpenAI gateway directly may trigger `429 Too Many Requests` from the provider side before the local infrastructure yields.
- **Postgres Checkpointing Scaling:** Long-running LangGraph sessions serialize their entire state to Postgres. For extreme edge-cases (e.g., 50,000+ token contexts), this can bloat the SQL database significantly.

## 2. Technical Debt
- **Vector Embeddings (Qdrant):** The chunking algorithm currently relies on standard character-based splitting. Semantic/Markdown-aware chunking is mocked or rudimentary.
- **Telemetry Aggregation:** While OpenTelemetry spans are emitted efficiently, there is no built-in dashboard in the Streamlit frontend to visualize them. (Relies on external Grafana/Jaeger).

## 3. Recommended v1.1 Roadmap
1. **Model Router V2:** Implement an adaptive fallback model that rotates API keys dynamically to prevent `429` provider exhaustion.
2. **S3 Checkpointing:** Migrate large LangGraph state objects (blobs/documents) out of Postgres and into an S3 bucket, saving only pointers in SQL.
3. **Admin Dashboard:** Expand the Streamlit frontend to include an "Admin Console" visualizing running worker graphs, Redis queue sizes, and Qdrant cluster health natively.
4. **Markdown Chunking:** Upgrade the Retrieval engine to utilize `unstructured` or `langchain` semantic document loaders for better RAG precision.
