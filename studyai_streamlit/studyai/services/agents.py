"""
AI agents.

Every agent in the original Next.js app is reimplemented here as a method on
:class:`AgentService`. All of them are grounded: they retrieve context from the
FAISS index first and pass ONLY that context to OpenRouter.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from config import NO_ANSWER_MESSAGE
from models.schemas import Flashcard, QuizQuestion, RetrievedChunk
from services.openrouter_client import OpenRouterClient
from services.rag_engine import RAGEngine
from utils.logger import get_logger

logger = get_logger(__name__)

_GROUNDED_SYSTEM = (
    "You are StudyAI, an expert academic assistant. Use ONLY the study material "
    "provided by the user. Do not add outside knowledge. If the material is "
    f'insufficient, say exactly: "{NO_ANSWER_MESSAGE}"'
)

_JSON_SYSTEM = (
    "You output ONLY valid JSON — no prose, no explanations, no Markdown code "
    "fences. Use ONLY the study material provided."
)


class AgentService:
    """Grounded generation helpers backing each agent page."""

    def __init__(self, rag: RAGEngine, llm: Optional[OpenRouterClient] = None) -> None:
        self.rag = rag
        self.llm = llm or rag.llm

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _context(
        self,
        topic: str,
        top_k: int = 8,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        return self.rag.context_for_topic(topic, top_k=top_k, sources=sources)

    def _generate(self, instruction: str, context: str, max_tokens: int = 2000) -> str:
        return self.llm.chat(
            [
                {"role": "system", "content": _GROUNDED_SYSTEM},
                {
                    "role": "user",
                    "content": f"STUDY MATERIAL:\n{context}\n\nTASK:\n{instruction}",
                },
            ],
            max_tokens=max_tokens,
        )

    def _generate_json(self, instruction: str, context: str, max_tokens: int = 2500) -> Any:
        return self.llm.chat_json(
            [
                {"role": "system", "content": _JSON_SYSTEM},
                {
                    "role": "user",
                    "content": f"STUDY MATERIAL:\n{context}\n\nTASK:\n{instruction}",
                },
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )

    # ------------------------------------------------------------------ #
    # Notes Agent
    # ------------------------------------------------------------------ #
    def generate_notes(
        self,
        topic: str,
        style: str = "Detailed",
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Produce structured study notes for a topic."""
        context, results = self._context(topic, top_k=10, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        style_hint = {
            "Concise": "Keep it tight: bullet points only, maximum one page.",
            "Detailed": "Be thorough: full explanations with worked examples.",
            "Exam-focused": "Prioritise definitions, formulas and likely exam answers.",
            "Bullet points": "Use only nested bullet points, no paragraphs.",
        }.get(style, "Be thorough and clear.")

        instruction = (
            f"Write study notes on \"{topic}\".\n{style_hint}\n\n"
            "Structure:\n"
            "## Overview\n## Key Definitions\n## Core Concepts\n"
            "## Examples\n## Exam Tips\n## Summary\n\n"
            "Cite sources inline as [1], [2] matching the material labels."
        )
        return self._generate(instruction, context, max_tokens=2500), results

    # ------------------------------------------------------------------ #
    # Quiz Agent
    # ------------------------------------------------------------------ #
    def generate_quiz(
        self,
        topic: str,
        count: int = 5,
        difficulty: str = "Medium",
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[List[QuizQuestion], List[RetrievedChunk]]:
        """Generate multiple-choice questions grounded in the documents."""
        context, results = self._context(topic, top_k=10, sources=sources)
        if not results:
            return [], []

        instruction = (
            f"Create {count} {difficulty.lower()}-difficulty multiple-choice questions "
            f'on "{topic}", answerable purely from the material.\n\n'
            "Return a JSON array where each object has:\n"
            '{"question": str, "options": [4 strings], "answer_index": int (0-3), '
            '"explanation": str, "source": str}'
        )
        payload = self._generate_json(instruction, context)

        questions: List[QuizQuestion] = []
        for item in payload if isinstance(payload, list) else []:
            try:
                options = [str(o) for o in item["options"]][:4]
                if len(options) < 2:
                    continue
                questions.append(
                    QuizQuestion(
                        question=str(item["question"]),
                        options=options,
                        answer_index=max(0, min(int(item.get("answer_index", 0)),
                                                len(options) - 1)),
                        explanation=str(item.get("explanation", "")),
                        source=str(item.get("source", "")),
                        difficulty=difficulty,
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Skipping malformed quiz item: %s", exc)
        return questions, results

    # ------------------------------------------------------------------ #
    # Flashcard Agent
    # ------------------------------------------------------------------ #
    def generate_flashcards(
        self,
        topic: str,
        count: int = 10,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[List[Flashcard], List[RetrievedChunk]]:
        """Generate spaced-repetition flashcards."""
        context, results = self._context(topic, top_k=10, sources=sources)
        if not results:
            return [], []

        instruction = (
            f'Create {count} flashcards on "{topic}" from the material.\n'
            "Fronts should be short prompts (a term, or a one-line question). "
            "Backs should be crisp, complete answers of 1-3 sentences.\n\n"
            'Return a JSON array of {"front": str, "back": str, "topic": str, '
            '"source": str}'
        )
        payload = self._generate_json(instruction, context)

        cards: List[Flashcard] = []
        for item in payload if isinstance(payload, list) else []:
            try:
                cards.append(
                    Flashcard(
                        front=str(item["front"]),
                        back=str(item["back"]),
                        topic=str(item.get("topic", topic)),
                        source=str(item.get("source", "")),
                    )
                )
            except (KeyError, TypeError) as exc:
                logger.warning("Skipping malformed flashcard: %s", exc)
        return cards, results

    # ------------------------------------------------------------------ #
    # Planner Agent
    # ------------------------------------------------------------------ #
    def generate_study_plan(
        self,
        subject: str,
        days: int,
        hours_per_day: float,
        exam_date: str = "",
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Build a day-by-day study schedule from the document's actual topics."""
        context, results = self._context(
            f"{subject} syllabus topics chapters units", top_k=12, sources=sources
        )
        if not results:
            return NO_ANSWER_MESSAGE, []

        instruction = (
            f"Build a {days}-day study plan for \"{subject}\" at "
            f"{hours_per_day} hours per day"
            + (f", with the exam on {exam_date}" if exam_date else "")
            + ".\n\nCover ONLY topics that actually appear in the material. "
            "For each day give: the topics, a time breakdown, the revision "
            "activity, and a checkpoint. Add a final revision day. "
            "Use a Markdown table per day."
        )
        return self._generate(instruction, context, max_tokens=2800), results

    # ------------------------------------------------------------------ #
    # Revision Agent
    # ------------------------------------------------------------------ #
    def generate_revision(
        self,
        topic: str,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Produce a rapid-revision sheet."""
        context, results = self._context(topic, top_k=10, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        instruction = (
            f'Create a rapid revision sheet for "{topic}".\n\n'
            "## 5-Minute Recap\n## Must-Know Definitions\n"
            "## Formulas & Algorithms\n## Memory Hooks (mnemonics)\n"
            "## Common Mistakes\n## Self-Check Questions\n\n"
            "Keep it dense and scannable."
        )
        return self._generate(instruction, context, max_tokens=2000), results

    # ------------------------------------------------------------------ #
    # Weak Topics Agent
    # ------------------------------------------------------------------ #
    def analyse_weak_topics(
        self,
        subject: str,
        wrong_answers: Sequence[str] = (),
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[List[Dict[str, Any]], List[RetrievedChunk]]:
        """Identify likely weak areas and score them out of 100."""
        context, results = self._context(
            f"{subject} difficult concepts", top_k=10, sources=sources
        )
        if not results:
            return [], []

        missed = "\n".join(f"- {item}" for item in wrong_answers) or "None recorded yet."
        instruction = (
            f"The student is studying \"{subject}\". Questions answered "
            f"incorrectly:\n{missed}\n\n"
            "Identify the 4-6 hardest topics in the material that need attention.\n"
            'Return a JSON array of {"name": str, "score": int (0-100 mastery '
            'estimate), "reason": str, "action": str}'
        )
        payload = self._generate_json(instruction, context, max_tokens=1500)

        topics: List[Dict[str, Any]] = []
        for item in payload if isinstance(payload, list) else []:
            try:
                topics.append(
                    {
                        "name": str(item["name"]),
                        "score": max(0, min(int(item.get("score", 50)), 100)),
                        "reason": str(item.get("reason", "")),
                        "action": str(item.get("action", "")),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        return topics, results

    # ------------------------------------------------------------------ #
    # Interview Mode
    # ------------------------------------------------------------------ #
    def interview_question(
        self,
        topic: str,
        asked: Sequence[str] = (),
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Ask the next mock-interview question."""
        context, results = self._context(topic, top_k=8, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        previous = "\n".join(f"- {q}" for q in asked) or "None yet."
        instruction = (
            f'You are a technical interviewer for "{topic}".\n'
            f"Already asked:\n{previous}\n\n"
            "Ask ONE new interview question drawn from the material. "
            "Output only the question — no preamble, no answer."
        )
        return self._generate(instruction, context, max_tokens=250), results

    def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Grade an interview answer against the source material."""
        context, results = self._context(question, top_k=8, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        instruction = (
            f"INTERVIEW QUESTION: {question}\n"
            f"STUDENT'S ANSWER: {student_answer}\n\n"
            "Evaluate strictly against the material:\n"
            "**Score:** X/10\n**What was correct:**\n**What was missing:**\n"
            "**Model answer:**\n**One improvement tip:**"
        )
        return self._generate(instruction, context, max_tokens=1200), results

    # ------------------------------------------------------------------ #
    # Cross-Subject Agent
    # ------------------------------------------------------------------ #
    def cross_subject_analysis(
        self,
        query: str,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Reason across multiple uploaded documents at once."""
        context, results = self._context(query, top_k=14, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        instruction = (
            f'Analyse "{query}" across the documents.\n\n'
            "## Connections Across Documents\n## Contrasts & Differences\n"
            "## Unified Explanation\n## Exam Angle\n\n"
            "Name the specific document behind each point and cite as [n]."
        )
        return self._generate(instruction, context, max_tokens=2500), results

    # ------------------------------------------------------------------ #
    # Summarisation, question bank, previous papers, important questions
    # ------------------------------------------------------------------ #
    def summarise(
        self,
        topic: str,
        length: str = "Medium",
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Summarise a topic or a whole document."""
        context, results = self._context(topic, top_k=14, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        hint = {
            "Short": "3-5 sentences.",
            "Medium": "Around 300 words with headings.",
            "Long": "A detailed structured summary of 700+ words.",
        }.get(length, "Around 300 words.")
        instruction = f'Summarise "{topic}". Length: {hint} Cite sources as [n].'
        return self._generate(instruction, context, max_tokens=2500), results

    def explain_topic(
        self,
        topic: str,
        level: str = "Undergraduate",
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Explain a topic or chapter at a chosen difficulty level."""
        context, results = self._context(topic, top_k=10, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        instruction = (
            f'Explain "{topic}" at a {level} level, using only the material.\n'
            "Start with an intuition, then the formal explanation, then a worked "
            "example, then where it shows up in exams. Cite as [n]."
        )
        return self._generate(instruction, context, max_tokens=2500), results

    def question_bank(
        self,
        topic: str,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Build a graded question bank."""
        context, results = self._context(topic, top_k=12, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        instruction = (
            f'Build a question bank for "{topic}" from the material:\n\n'
            "## 2-Mark Questions (8 items)\n## 5-Mark Questions (6 items)\n"
            "## 10-Mark Questions (4 items)\n\n"
            "Add the source citation [n] after each question."
        )
        return self._generate(instruction, context, max_tokens=2500), results

    def important_questions(
        self,
        topic: str,
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """List the most exam-likely questions."""
        context, results = self._context(topic, top_k=12, sources=sources)
        if not results:
            return NO_ANSWER_MESSAGE, []

        instruction = (
            f'List the 10 most important exam questions for "{topic}" based on how '
            "much emphasis the material gives each concept.\n"
            "For each: the question, why it matters, the marks it likely carries, "
            "and a 2-line answer skeleton. Cite as [n]."
        )
        return self._generate(instruction, context, max_tokens=2500), results

    def analyse_previous_paper(
        self,
        subject: str,
        paper_text: str = "",
        sources: Optional[Sequence[str]] = None,
    ) -> tuple[str, List[RetrievedChunk]]:
        """Analyse previous question papers for recurring patterns."""
        query = f"{subject} previous question paper exam questions"
        context, results = self._context(query, top_k=14, sources=sources)
        if not results and not paper_text:
            return NO_ANSWER_MESSAGE, []

        extra = f"\n\nPASTED PAPER:\n{paper_text[:6000]}" if paper_text else ""
        instruction = (
            f'Analyse previous papers for "{subject}".{extra}\n\n'
            "## Repeated Topics\n## Mark Distribution\n"
            "## Likely Questions This Time\n## Preparation Priority\n\n"
            "Base every claim on the material and cite as [n]."
        )
        return self._generate(instruction, context, max_tokens=2500), results
