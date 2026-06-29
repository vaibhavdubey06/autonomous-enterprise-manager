from sentence_transformers import SentenceTransformer
from functools import lru_cache


@lru_cache()
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str):
    return get_model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]):
    return get_model().encode(texts, normalize_embeddings=True).tolist()
