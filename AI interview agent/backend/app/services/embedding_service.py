"""Embedding adapter with optional sentence-transformers and deterministic local fallback."""
import hashlib
import re

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FALLBACK_DIMENSION = 256
_model = None


def _fallback_embedding(text):
    vector = np.zeros(FALLBACK_DIMENSION, dtype=np.float32)
    tokens = re.findall(r"[a-z0-9][a-z0-9+#.-]*", text.casefold())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % FALLBACK_DIMENSION
        vector[index] += 1.0
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME)
        except (ImportError, OSError, RuntimeError):
            _model = False
    return _model


def embed_texts(texts):
    model = _get_model()
    if model:
        return np.asarray(model.encode(texts, normalize_embeddings=True), dtype=np.float32)
    return np.vstack([_fallback_embedding(text) for text in texts]).astype(np.float32)


def embedding_dimension():
    model = _get_model()
    return int(model.get_sentence_embedding_dimension()) if model else FALLBACK_DIMENSION
