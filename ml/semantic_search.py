from sentence_transformers import SentenceTransformer
import numpy as np

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def get_embedding(text):
    return _get_model().encode(text).tolist()


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def semantic_search(query_text, candidates):
    query_vec = get_embedding(query_text)
    scored = [
        (cosine_similarity(query_vec, obj.embedding), obj)
        for obj in candidates if obj.embedding
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [obj for _, obj in scored]
