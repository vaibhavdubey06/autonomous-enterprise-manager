# Semantic Cache
## Purpose
To intercept redundant LLM requests by identifying semantically similar prior queries, reducing latency and cost.

## Architecture
Implemented as a Middleware in the LLM Gateway. Uses vector embeddings to find distance < threshold.

## Flow
Request -> Hash/Embed -> Check Qdrant Cache Collection -> If hit, return immediately -> Else proceed to LLM -> Store result in Cache.

## Extension Points
Adjust the semantic threshold, configure eviction policies (TTL, LFU).
