"""
FAISS-backed vector store with on-disk persistence.

Uses ``IndexFlatIP`` over L2-normalised vectors, which makes the returned inner
product identical to cosine similarity. That gives us a meaningful, bounded
score (-1..1) to threshold on — the mechanism behind the "not found in your
documents" guardrail.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from config import settings, VECTORSTORE_DIR
from models.schemas import Chunk, RetrievedChunk
from services.embeddings import EmbeddingService, get_embedding_service
from utils.logger import get_logger

logger = get_logger(__name__)

_INDEX_FILE = "index.faiss"
_CHUNKS_FILE = "chunks.pkl"
_META_FILE = "meta.json"


class VectorStore:
    """A persistent FAISS index paired with its chunk metadata."""

    def __init__(
        self,
        store_dir: Optional[Path] = None,
        embedder: Optional[EmbeddingService] = None,
    ) -> None:
        self.store_dir: Path = Path(store_dir or VECTORSTORE_DIR)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.embedder: EmbeddingService = embedder or get_embedding_service()

        self._index = None
        self.chunks: List[Chunk] = []
        self.meta: Dict[str, dict] = {}   # doc_id -> document metadata

    # ------------------------------------------------------------------ #
    # Index lifecycle
    # ------------------------------------------------------------------ #
    def _new_index(self):
        import faiss

        return faiss.IndexFlatIP(self.embedder.dimension)

    @property
    def index(self):
        """The live FAISS index, created on first access."""
        if self._index is None:
            self._index = self._new_index()
        return self._index

    @property
    def size(self) -> int:
        """Number of indexed chunks."""
        return len(self.chunks)

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    @property
    def sources(self) -> List[str]:
        """Distinct document filenames currently indexed."""
        seen: List[str] = []
        for chunk in self.chunks:
            if chunk.source not in seen:
                seen.append(chunk.source)
        return seen

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #
    def add_chunks(self, chunks: Sequence[Chunk], batch_size: int = 32) -> int:
        """Embed and index a batch of chunks. Returns the number added."""
        if not chunks:
            return 0

        vectors = self.embedder.encode([c.text for c in chunks], batch_size=batch_size)
        self.index.add(vectors)
        self.chunks.extend(chunks)
        logger.info("Indexed %s chunks (total=%s)", len(chunks), self.size)
        return len(chunks)

    def register_document(self, doc_id: str, metadata: dict) -> None:
        """Record document-level metadata for the Upload Center table."""
        self.meta[doc_id] = metadata

    def remove_source(self, source: str) -> int:
        """
        Delete every chunk belonging to ``source`` and rebuild the index.

        IndexFlatIP has no cheap delete, so a rebuild is the honest approach.
        """
        keep = [c for c in self.chunks if c.source != source]
        removed = self.size - len(keep)
        if removed == 0:
            return 0

        self._index = self._new_index()
        self.chunks = []
        if keep:
            self.add_chunks(keep)

        self.meta = {k: v for k, v in self.meta.items() if v.get("name") != source}
        logger.info("Removed %s chunks for source %s", removed, source)
        return removed

    def clear(self) -> None:
        """Wipe the in-memory index and the persisted files."""
        self._index = self._new_index()
        self.chunks = []
        self.meta = {}
        for filename in (_INDEX_FILE, _CHUNKS_FILE, _META_FILE):
            path = self.store_dir / filename
            if path.exists():
                path.unlink()
        logger.info("Vector store cleared")

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        sources: Optional[Sequence[str]] = None,
    ) -> List[RetrievedChunk]:
        """
        Semantic search over the indexed chunks.

        ``sources`` optionally restricts results to specific filenames, which is
        what the per-subject and per-document filters in the UI use.
        """
        if self.is_empty:
            return []

        k = top_k or settings.top_k
        floor = settings.min_similarity if min_score is None else min_score

        # Over-fetch when filtering so the filter does not starve the result set.
        fetch = min(self.size, k * 4 if sources else k)
        query_vector = self.embedder.encode_one(query)
        scores, indices = self.index.search(query_vector, fetch)

        results: List[RetrievedChunk] = []
        for score, position in zip(scores[0], indices[0]):
            if position < 0 or position >= len(self.chunks):
                continue
            chunk = self.chunks[position]
            if sources and chunk.source not in sources:
                continue
            if float(score) < floor:
                continue
            results.append(RetrievedChunk(chunk=chunk, score=float(score)))
            if len(results) >= k:
                break

        logger.info("Search '%s' → %s hits above %.2f",
                    query[:60], len(results), floor)
        return results

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def save(self) -> None:
        """Persist index, chunks and metadata to disk."""
        import faiss

        try:
            faiss.write_index(self.index, str(self.store_dir / _INDEX_FILE))
            with open(self.store_dir / _CHUNKS_FILE, "wb") as handle:
                pickle.dump([c.to_dict() for c in self.chunks], handle)
            with open(self.store_dir / _META_FILE, "w", encoding="utf-8") as handle:
                json.dump(self.meta, handle, indent=2)
            logger.info("Vector store saved (%s chunks)", self.size)
        except Exception as exc:  # noqa: BLE001 - persistence is best-effort
            logger.error("Failed to save vector store: %s", exc)

    def load(self) -> bool:
        """Restore a previously saved store. Returns True on success."""
        import faiss

        index_path = self.store_dir / _INDEX_FILE
        chunks_path = self.store_dir / _CHUNKS_FILE
        if not (index_path.exists() and chunks_path.exists()):
            return False

        try:
            self._index = faiss.read_index(str(index_path))
            with open(chunks_path, "rb") as handle:
                self.chunks = [Chunk.from_dict(d) for d in pickle.load(handle)]
            meta_path = self.store_dir / _META_FILE
            if meta_path.exists():
                with open(meta_path, encoding="utf-8") as handle:
                    self.meta = json.load(handle)
            logger.info("Vector store loaded (%s chunks)", self.size)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load vector store: %s", exc)
            self._index = self._new_index()
            self.chunks = []
            self.meta = {}
            return False
