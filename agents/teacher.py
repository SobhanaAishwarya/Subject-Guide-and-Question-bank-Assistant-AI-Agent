import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import AgentState
from utils.logger import logger

class TeacherAgent:
    """
    Production-grade Teacher Agent capable of breaking down complex domains 
    (OS, DBMS, DSA, CN, OOPS) by dynamically shifting instruction styles between
    Beginner, Advanced, and Technical Interview simulation profiles.
    """

    def __init__(self) -> None:
        """
        Initializes the Teacher LLM processing module with OpenRouter infrastructure base keys.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing TeacherAgent LLM with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.4  # Slightly balanced temperature for rich analogies and detailed breakdowns
            )
        except Exception as e:
            logger.error(f"Failed to initialize TeacherAgent LLM engine: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes explanation loops, adapting tone and depth based on active metadata profiles.
        """
        user_input = state.get("user_input", "")
        metadata = state.get("metadata", {})
        
        # Extract operational learning mode profile (Default to standard baseline explanation)
        mode = metadata.get("teacher_mode", "beginner").lower()
        logger.info(f"TeacherAgent processing concept generation in mode profile: '{mode}'")

        # Compile behavioral identity prompts matching targeted pedagogical execution styles
        if mode == "advanced":
            instruction_set = (
                "You are an elite, senior-level Computer Science Professor and Python Software Architect.\n"
                "Explain the user's requested topic with deep technical rigor, architectural schematics, edge cases, "
                "low-level hardware or filesystem mechanics, and production-grade software engineering patterns. Avoid shallow analogies."
            )
        elif mode == "interview":
            instruction_set = (
                "You are an expert Technical Interviewer assessing candidates for high-tier tech firms.\n"
                "Structure your breakdown like a standard interview challenge. Detail the question context, ask logical "
                "probing follow-up variants, outline the absolute most optimal algorithmic bounds using Big-O time/space complexities "
                "where applicable, and present classic trick scenarios or architectural trade-offs."
            )
        else:  # 'beginner' mode fallback standard
            instruction_set = (
                "You are a highly patient, encouraging, and clear Technical Instructor.\n"
                "Break down the topic using intuitive, real-world visual analogies, clear foundational descriptions, "
                "and digestible summaries. Avoid overwhelming technical jargon without explaining it immediately first."
            )

        # Incorporate vector context maps if pre-loaded by the Supervisor/RAG worker loop tier
        context_payload = state.get("retrieved_context", "")
        context_addition = ""
        if context_payload:
            context_addition = f"\n\nUse the following verified document context to enrich your explanation:\n{context_payload}"

        system_prompt = (
            f"{instruction_set}{context_addition}\n\n"
            "Formatting Rules:\n"
            "- Ensure top-tier markdown visual hierarchy: use sharp titles (`##`, `###`), horizontal dividers (`---`), and selective bolding.\n"
            "- For any formal mathematical expressions, use standard inline or block LaTeX ($...$ or $$...$$).\n"
            "- For programming or database segments, wrap your syntax in fully executable Markdown language code blocks."
        )

        try:
            # Construct execution messages chain payload array
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Explain this concept thoroughly: {user_input}")
            ]
            
            # Execute inference turn execution
            response = self.llm.invoke(messages)
            
            logger.info("TeacherAgent successfully generated conceptual response payload.")
            return {
                "agent_output": {
                    "content": response.content,
                    "mode_executed": mode
                }
            }
            
        except Exception as e:
            logger.error(f"Error encountered during TeacherAgent execution workflow: {str(e)}", exc_info=True)
            return {
                "agent_output": {"content": "I encountered a minor error while trying to process this explanation loop. Let's try adjusting the query or learning mode style."},
                "errors": state.get("errors", []) + [f"Teacher Agent Error: {str(e)}"]
            }