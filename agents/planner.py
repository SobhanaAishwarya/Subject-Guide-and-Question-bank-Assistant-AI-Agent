import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import AgentState
from utils.logger import logger

class StudyPlannerAgent:
    """
    Production-grade Study Planner Agent responsible for crafting optimized, 
    highly customized, scannable milestone schedules and personalized learning roadmaps.
    """

    def __init__(self) -> None:
        """
        Initializes the Study Planner LLM node infrastructure using explicit configuration settings.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing StudyPlannerAgent LLM with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.3  # Low-variance structured output generation
            )
        except Exception as e:
            logger.error(f"Failed to initialize StudyPlannerAgent LLM engine: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Builds a milestone calendar roadmap schedule tracking time scopes, weak target subjects, and topics.
        """
        user_input = state.get("user_input", "")
        metadata = state.get("metadata", {})
        
        duration_weeks = metadata.get("duration_weeks", 4)
        daily_hours = metadata.get("daily_hours", 2)
        
        logger.info(f"StudyPlannerAgent parsing plan configurations. Timeline scope: {duration_weeks} weeks, {daily_hours} hours daily.")

        system_prompt = (
            "You are an expert Academic Coach and Curriculum Architect for agentic_ai_clean.\n"
            f"Your directive is to generate an absolute complete, day-by-day or milestone-by-milestone personalized study plan map spanning exactly {duration_weeks} weeks, "
            f"assuming a daily allocation commitment threshold of {daily_hours} hours.\n\n"
            "PLAN COMPILATION REQUIREMENTS:\n"
            "- Establish an explicit tactical layout matrix outlining clear structural milestones for each week.\n"
            "- Inject distinct metrics indicating target focal domains, conceptual deep dives, active practice slots (quizzes/flashcards), and system revision cycles.\n"
            "- Maximize scannability using markdown grids, milestone checkmarks, structured bullet blocks, and separating weeks using horizontal bars (`---`)."
        )

        context_payload = state.get("retrieved_context", "")
        context_addition = f"\n\nAlign the weekly timeline items tightly to map against this document reference context payload:\n{context_payload}" if context_payload else ""

        try:
            messages = [
                SystemMessage(content=f"{system_prompt}{context_addition}"),
                HumanMessage(content=f"Create a study blueprint schedule target map for: '{user_input}'")
            ]
            
            response = self.llm.invoke(messages)
            
            logger.info("StudyPlannerAgent successfully compiled calendar study schedule mapping roadmap.")
            return {
                "agent_output": {
                    "content": response.content,
                    "duration_weeks": duration_weeks,
                    "daily_hours": daily_hours,
                    "topic": user_input
                }
            }
        except Exception as e:
            logger.error(f"Error hit inside StudyPlannerAgent execution routine cycle: {str(e)}", exc_info=True)
            return {
                "agent_output": {"content": "I encountered an issue trying to compile the requested personalized calendar plan architecture mapping tracks."},
                "errors": state.get("errors", []) + [f"StudyPlanner Agent Error: {str(e)}"]
            }