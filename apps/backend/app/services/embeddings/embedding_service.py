from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def embed_text(text: str):
    return model.encode(
        text,
        normalize_embeddings=True
    ).tolist()


def embed_batch(texts: list[str]):
    return model.encode(
        texts,
        normalize_embeddings=True
    ).tolist()