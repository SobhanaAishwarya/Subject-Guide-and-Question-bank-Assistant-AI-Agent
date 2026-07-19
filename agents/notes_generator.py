import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import AgentState
from utils.logger import logger

class NotesGeneratorAgent:
    """
    Production-grade Notes Generator Agent responsible for synthesizing structured academic 
    summaries, itemized key takeaways, and comprehensive mathematical/scientific formula sheets.
    """

    def __init__(self) -> None:
        """
        Initializes the Notes Generator LLM engine with OpenRouter configuration details.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing NotesGeneratorAgent LLM with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.3  # Low variance to maintain analytical and precise technical framing
            )
        except Exception as e:
            logger.error(f"Failed to initialize NotesGeneratorAgent LLM engine: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates highly organized study notes, structured summaries, and formula frameworks based on active metadata profiles.
        """
        user_input = state.get("user_input", "")
        metadata = state.get("metadata", {})
        
        notes_style = metadata.get("notes_style", "Summary").lower()
        logger.info(f"NotesGeneratorAgent compiling study sheets with layout strategy: '{notes_style}'")

        if notes_style == "formula":
            format_instruction = (
                "Create a high-density, mathematically rigorous Formula Sheet.\n"
                "List all prominent core equations, state the exact meaning of every variable, "
                "detail foundational derivation proofs briefly where relevant, and map out computational bounds using block LaTeX ($$ ... $$)."
            )
        elif notes_style == "key_points":
            format_instruction = (
                "Create a structured, itemized Key Takeaways and High-Yield Concepts review guide.\n"
                "Use highly scannable bullet points, clear bold phrasing tags, and explicit definitions for structural terminology."
            )
        else:  # 'summary' fallback standard configuration
            format_instruction = (
                "Create a comprehensive Executive Technical Summary.\n"
                "Provide an exhaustive deep dive breaking down overarching system layers, process flows, trade-offs, and design paradigms."
            )

        context_payload = state.get("retrieved_context", "")
        context_addition = f"\n\nIntegrate and summarize the following verified document context assets directly into the notes layout:\n{context_payload}" if context_payload else ""

        system_prompt = (
            "You are an elite Academic Content Architect and Technical Writer for agentic_ai_clean.\n"
            f"Your specific task is to synthesize professional study notes on the topic target requested by the user.\n\n"
            f"FORMAT STRATEGY CONTRACT:\n{format_instruction}{context_addition}\n\n"
            "VISUAL VISUAL LAYOUT & STYLING RULES:\n"
            "- Ensure supreme markdown presentation: employ titles (`##`, `###`), clean layout blocks, horizontal rules (`---`), and organized data charts where applicable.\n"
            "- Wrap equations in standard inline ($...$) or standalone ($$...$$) LaTeX tags.\n"
            "- If code fragments or query structures are included, use markdown language syntax code blocks."
        )

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate detailed study notes for: '{user_input}'")
            ]
            
            response = self.llm.invoke(messages)
            
            logger.info("NotesGeneratorAgent successfully generated comprehensive notes block.")
            return {
                "agent_output": {
                    "content": response.content,
                    "notes_style": notes_style,
                    "topic": user_input
                }
            }
        except Exception as e:
            logger.error(f"Error encountered inside NotesGeneratorAgent execution loop: {str(e)}", exc_info=True)
            return {
                "agent_output": {"content": "I encountered an issue compiling your study notes profile. Let's try re-submitting the request syntax loop."},
                "errors": state.get("errors", []) + [f"NotesGenerator Agent Error: {str(e)}"]
            }