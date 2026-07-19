import os
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import AgentState
from utils.logger import logger

class FlashcardWorkerAgent:
    """
    Production-grade Flashcard Worker Agent responsible for generating structured,
    rapid-fire Question & Answer cards. Outputs highly scannable raw JSON arrays 
    for streamlined execution and card-flip rendering inside the web tier.
    """

    def __init__(self) -> None:
        """
        Initializes the Flashcard LLM processing matrix under strict structural criteria.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "[https://api.openai.com/v1](https://api.openai.com/v1)")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing FlashcardWorkerAgent LLM with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.4  # Slightly balanced for creative recall prompts while staying clear
            )
        except Exception as e:
            logger.error(f"Failed to initialize FlashcardWorkerAgent LLM: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates an array of flashcards from text prompts or indexed context frameworks.
        """
        user_input = state.get("user_input", "")
        metadata = state.get("metadata", {})
        num_cards = metadata.get("num_cards", 5)
        
        logger.info(f"FlashcardWorkerAgent parsing deck generation request. Total targets: {num_cards}")

        system_prompt = (
            "You are an expert Educational Engineer and Active Recall Specialist for agentic_ai_clean.\n"
            f"Your objective is to generate exactly {num_cards} memory retention flashcards for the user's targeted study topic.\n\n"
            "CRITICAL STRUCTURAL SCHEMATICS RULES:\n"
            "- You must return output EXCLUSIVELY as a valid JSON array string containing structured card objects. Do not wrap the output in markdown code blocks like ```json ... ```. Return raw plaintext only.\n"
            "- Every object in the array MUST strictly conform to this schema:\n"
            "  {\n"
            "    \"card_id\": 1,\n"
            "    \"front\": \"A concise, high-impact active recall question, term, or formula variant\",\n"
            "    \"back\": \"A clear, structured, itemized or crisp answer response optimizing long-term retention\"\n"
            "  }"
        )

        context_payload = state.get("retrieved_context", "")
        context_addition = f"\n\nExtract core factual components from this reference document context slice to compile the deck:\n{context_payload}" if context_payload else ""

        try:
            messages = [
                SystemMessage(content=f"{system_prompt}{context_addition}"),
                HumanMessage(content=f"Generate flashcards for this topic target: '{user_input}'")
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Clean possible markdown block artifacts
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    response_text = "\n".join(lines[1:-1])

            # Pre-validate parsability bounds
            flashcard_deck = json.loads(response_text)
            
            logger.info("FlashcardWorkerAgent successfully generated flashcards deck matrix.")
            return {
                "agent_output": {
                    "flashcards": flashcard_deck,
                    "topic": user_input
                }
            }
        except Exception as e:
            logger.error(f"Error encountered inside FlashcardWorkerAgent execution: {str(e)}", exc_info=True)
            return {
                "agent_output": {"error_fallback": True, "content": "I encountered an error trying to construct the flashcards array structure. Let's try executing the generation thread again."},
                "errors": state.get("errors", []) + [f"FlashcardWorker Agent Error: {str(e)}"]
            }