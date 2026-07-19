"""
Retrieval-Augmented Generation engine.

Pipeline
--------
question → embed → FAISS semantic search → threshold filter → build context
        → send ONLY the retrieved context to OpenRouter → grounded answer
        → citations + related questions

If retrieval returns nothing above the similarity floor, the LLM is never
called and the configured refusal message is returned instead. That is the
single most important anti-hallucination guarantee in this project.
"""

from __future__ import annotations

from typing import Dict, Generator, List, Optional, Sequence

from config import settings, NO_ANSWER_MESSAGE
from models.schemas import Answer, Message, RetrievedChunk
from services.openrouter_client import OpenRouterClient
from services.vectorstore import VectorStore
from utils.logger import get_logger

logger = get_logger(__name__)


SYSTEM_PROMPT = """You are StudyAI, an academic assistant for university students.

STRICT RULES:
1. Answer ONLY using the CONTEXT provided below. The context is the sole source \
of truth.
2. If the context does not contain the answer, reply with exactly this sentence \
and nothing else: "{no_answer}"
3. Never use outside knowledge. Never guess. Never invent facts, numbers, \
definitions or examples.
4. Cite your sources inline using the bracket labels shown in the context, \
for example [1] or [2]. Every factual claim needs a citation.
5. Structure longer answers with short headings and bullet points.
6. Be precise and exam-oriented. Define terms the way the document defines them.
""".format(no_answer=NO_ANSWER_MESSAGE)


class RAGEngine:
    """Coordinates retrieval and grounded generation."""

    def __init__(
        self,
        vector_store: VectorStore,
        llm: Optional[OpenRouterClient] = None,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
    ) -> None:
        self.store = vector_store
        self.llm = llm or OpenRouterClient()
        self.top_k: int = top_k or settings.top_k
        self.min_similarity: float = (
            settings.min_similarity if min_similarity is None else min_similarity
        )

    # ------------------------------------------------------------------ #
    # Context assembly
    # ------------------------------------------------------------------ #
    @staticmethod
    def build_context(results: Sequence[RetrievedChunk]) -> str:
        """Render retrieved chunks into a numbered, citable context block."""
        blocks: List[str] = []
        for position, item in enumerate(results, start=1):
            chunk = item.chunk
            blocks.append(
                f"[{position}] Source: {chunk.citation} "
                f"(relevance {item.score:.2f})\n{chunk.text}"
            )
        return "\n\n---\n\n".join(blocks)

    def retrieve(
        self,
        question: str,
        top_k: Optional[int] = None,
        sources: Optional[Sequence[str]] = None,
    ) -> List[RetrievedChunk]:
        """Run semantic search for a question."""
        return self.store.search(
            question,
            top_k=top_k or self.top_k,
            min_score=self.min_similarity,
            sources=sources,
        )

    def _messages(
        self,
        question: str,
        context: str,
        history: Optional[Sequence[Message]] = None,
    ) -> List[Dict[str, str]]:
        """Assemble the chat payload: system + recent history + context turn."""
        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Session memory: last few turns give the model conversational continuity
        # without letting old context leak in as a source of truth.
        for message in list(history or [])[-6:]:
            messages.append({"role": message.role, "content": message.content})

        messages.append(
            {
                "role": "user",
                "content": (
                    f"CONTEXT FROM UPLOADED DOCUMENTS:\n"
                    f"====================\n{context}\n====================\n\n"
                    f"QUESTION: {question}\n\n"
                    f"Answer using ONLY the context above, with inline [n] citations."
                ),
            }
        )
        return messages

    # ------------------------------------------------------------------ #
    # Answering
    # ------------------------------------------------------------------ #
    def answer(
        self,
        question: str,
        history: Optional[Sequence[Message]] = None,
        top_k: Optional[int] = None,
        sources: Optional[Sequence[str]] = None,
        with_related: bool = True,
    ) -> Answer:
        """Answer a question against the indexed documents."""
        if self.store.is_empty:
            return Answer(
                text="No documents indexed yet. Upload a PDF, DOCX, PPTX or TXT "
                     "file in the **Upload Center** to get started.",
                grounded=False,
            )

        results = self.retrieve(question, top_k=top_k, sources=sources)
        if not results:
            logger.info("No chunks above threshold for: %s", question[:80])
            return Answer(text=NO_ANSWER_MESSAGE, sources=[], grounded=False)

        context = self.build_context(results)
        text = self.llm.chat(self._messages(question, context, history))

        grounded = NO_ANSWER_MESSAGE.lower() not in text.lower()
        related = (
            self.related_questions(question, context)
            if (with_related and grounded)
            else []
        )
        return Answer(
            text=text,
            sources=results if grounded else [],
            related_questions=related,
            grounded=grounded,
        )

    def answer_stream(
        self,
        question: str,
        history: Optional[Sequence[Message]] = None,
        top_k: Optional[int] = None,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[Generator[str, None, None], List[RetrievedChunk]]:
        """
        Streaming variant for the ChatGPT-style typing animation.

        Returns ``(token_generator, retrieved_chunks)`` so the caller can render
        the sources panel as soon as retrieval finishes.
        """
        if self.store.is_empty:
            def _empty() -> Generator[str, None, None]:
                yield ("No documents indexed yet. Upload a file in the "
                       "**Upload Center** to get started.")
            return _empty(), []

        results = self.retrieve(question, top_k=top_k, sources=sources)
        if not results:
            def _refuse() -> Generator[str, None, None]:
                yield NO_ANSWER_MESSAGE
            return _refuse(), []

        context = self.build_context(results)
        generator = self.llm.stream(self._messages(question, context, history))
        return generator, results

    # ------------------------------------------------------------------ #
    # Related questions
    # ------------------------------------------------------------------ #
    def related_questions(self, question: str, context: str, count: int = 3) -> List[str]:
        """Suggest follow-up questions answerable from the same context."""
        try:
            payload = self.llm.chat_json(
                [
                    {
                        "role": "system",
                        "content": "You return ONLY a JSON array of strings. No prose, "
                                   "no code fences.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Based on this study material:\n{context[:3000]}\n\n"
                            f"The student just asked: \"{question}\"\n\n"
                            f"Return exactly {count} short follow-up questions that "
                            f"CAN be answered from this material. "
                            f'Format: ["question 1", "question 2", "question 3"]'
                        ),
                    },
                ],
                temperature=0.4,
                max_tokens=250,
            )
            if isinstance(payload, list):
                return [str(item) for item in payload[:count]]
        except Exception as exc:  # noqa: BLE001 - suggestions are non-critical
            logger.warning("Related-question generation failed: %s", exc)
        return []

    # ------------------------------------------------------------------ #
    # Shared helper for the agent layer
    # ------------------------------------------------------------------ #
    def context_for_topic(
        self,
        topic: str,
        top_k: int = 8,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Retrieve a broader context block used by the agent pages."""
        results = self.store.search(
            topic, top_k=top_k, min_score=self.min_similarity, sources=sources
        )
        return self.build_context(results), results
