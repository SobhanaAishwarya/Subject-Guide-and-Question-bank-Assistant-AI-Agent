import os
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import AgentState
from utils.logger import logger

class QuizMasterAgent:
    """
    Production-grade Quiz Master Agent responsible for generating structured evaluation materials
    including Multiple Choice Questions (MCQs), Fill-in-the-Blanks, and Programming/Coding Challenges.
    Outputs clean structural JSON payloads for direct Streamlit UI rendering.
    """

    def __init__(self) -> None:
        """
        Initializes the Quiz Master LLM engine with OpenRouter support parameters.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "[https://api.openai.com/v1](https://api.openai.com/v1)")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing QuizMasterAgent LLM with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.5  # Balanced for creative problem generation while maintaining structural integrity
            )
        except Exception as e:
            logger.error(f"Failed to initialize QuizMasterAgent LLM engine: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates an structured array of quiz questions based on the targeted topic and requested question format styles.
        """
        user_input = state.get("user_input", "")
        metadata = state.get("metadata", {})
        
        quiz_type = metadata.get("quiz_type", "MCQ").upper()
        num_questions = metadata.get("num_questions", 3)
        
        logger.info(f"QuizMasterAgent initiating quiz compilation engine. Type: {quiz_type}, Questions Count: {num_questions}")

        system_prompt = (
            "You are an expert Technical Assessment Specialist and Academic Examiner for agentic_ai_clean.\n"
            f"Your objective is to generate exactly {num_questions} high-quality quiz questions covering the user's targeted topic context.\n\n"
            "QUESTION FORMAT REQUIREMENTS BASED ON SELECTION:\n"
            "- 'MCQ': Standard Multiple Choice Question with 4 distinct options (A, B, C, D).\n"
            "- 'FILL': Fill-in-the-Blanks question targeting crucial conceptual terminology or language properties.\n"
            "- 'CODING': A production-oriented programming or engineering problem specifying clean input/output constraints, functional challenges, and clear conceptual hints.\n\n"
            "CRITICAL OUTPUT CONFIGURATION RULES:\n"
            "- You must return output EXCLUSIVELY as a valid JSON array string containing structured question objects. Do not wrap the output in markdown code blocks like ```json ... ```. Return raw JSON plaintext only.\n"
            "- Every object in the array MUST strictly conform to this schema configuration:\n"
            "  {\n"
            "    \"id\": 1,\n"
            "    \"type\": \"MCQ\" | \"FILL\" | \"CODING\",\n"
            "    \"question\": \"The text description of the problem statement here\",\n"
            "    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], // Only include or populate if type is 'MCQ', keep empty list [] for others\n"
            "    \"correct_answer\": \"The absolute exact value of the correct answer string (e.g. choice text or exact keyword text)\",\n"
            "    \"explanation\": \"A comprehensive, highly educational breakdown explaining why this specific selection is correct.\"\n"
            "  }"
        )

        # Incorporate context embeddings layer data if available
        context_payload = state.get("retrieved_context", "")
        context_addition = f"\n\nBase the generated quiz questions on this provided reference material context:\n{context_payload}" if context_payload else ""

        try:
            messages = [
                SystemMessage(content=f"{system_prompt}{context_addition}"),
                HumanMessage(content=f"Generate a quiz of type '{quiz_type}' on this topic target: '{user_input}'")
            ]
            
            # Run LLM execution turn
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Sanitize structural syntax boundaries if wrapped in code blocks
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    response_text = "\n".join(lines[1:-1])

            # Pre-validate structural parsability
            quiz_data = json.loads(response_text)
            
            logger.info("QuizMasterAgent successfully compiled structured quiz array object payload.")
            return {
                "agent_output": {
                    "quiz_questions": quiz_data,
                    "quiz_type": quiz_type,
                    "topic": user_input
                }
            }
        except Exception as e:
            logger.error(f"Error encountered inside QuizMasterAgent execution loop: {str(e)}", exc_info=True)
            return {
                "agent_output": {"error_fallback": True, "content": "I encountered an issue dynamically generating the requested test questions array structure. Let's attempt to run the engine again."},
                "errors": state.get("errors", []) + [f"QuizMaster Agent Error: {str(e)}"]
            }