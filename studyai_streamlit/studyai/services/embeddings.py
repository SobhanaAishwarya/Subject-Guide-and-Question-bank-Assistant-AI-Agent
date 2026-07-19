"""
Embedding generation using sentence-transformers (all-MiniLM-L6-v2).

The model is cached by Streamlit so it loads exactly once per session/server,
which matters a lot on Streamlit Cloud where cold starts are expensive.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _load_model(model_name: str):
    """Load the SentenceTransformer model (wrapped for caching)."""
    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model: %s", model_name)
    return SentenceTransformer(model_name)


try:  # Use Streamlit's resource cache when running inside Streamlit.
    import streamlit as st

    _cached_load_model = st.cache_resource(show_spinner=False)(_load_model)
except Exception:  # noqa: BLE001 - allows use from plain scripts/tests
    _cached_load_model = _load_model


class EmbeddingService:
    """Encodes text into L2-normalised vectors suitable for cosine search."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name: str = model_name or settings.embedding_model
        self._model = None

    @property
    def model(self):
        """Lazily resolve the underlying model."""
        if self._model is None:
            self._model = _cached_load_model(self.model_name)
        return self._model

    @property
    def dimension(self) -> int:
        """Vector dimensionality (384 for all-MiniLM-L6-v2)."""
        try:
            return int(self.model.get_sentence_embedding_dimension())
        except Exception:  # noqa: BLE001
            return settings.embedding_dimension

    def encode(
        self,
        texts: Sequence[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode a batch of texts.

        Vectors are normalised, so a FAISS inner-product search is equivalent
        to cosine similarity.
        """
        if not texts:
            return np.zeros((0, self.dimension), dtype="float32")

        vectors = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(vectors, dtype="float32")

    def encode_one(self, text: str) -> np.ndarray:
        """Encode a single string into a ``(1, dim)`` array."""
        return self.encode([text])


_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Module-level singleton accessor."""
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service
