import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import AgentState
from utils.logger import logger

class ProgressTrackerAgent:
    """
    Production-grade Progress Tracker Agent responsible for synthesizing 
    performance diagnostics, diagnostic summaries, and study optimization insights.
    """

    def __init__(self) -> None:
        """
        Initializes the Progress Tracker LLM engine with configuration details.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing ProgressTrackerAgent LLM with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.2
            )
        except Exception as e:
            logger.error(f"Failed to initialize ProgressTrackerAgent LLM engine: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Processes structural metric properties to generate study efficiency analyses.
        """
        user_input = state.get("user_input", "")
        metadata = state.get("metadata", {})
        
        completed_topics = metadata.get("completed_topics", "None logged yet")
        weak_topics = metadata.get("weak_topics", "None flagged yet")
        study_time = metadata.get("study_time", 0.0)
        quiz_scores = metadata.get("quiz_scores", [])

        logger.info(f"ProgressTrackerAgent analyzing structural diagnostic parameters.")

        system_prompt = (
            "You are an expert Performance Analytics Consultant and Academic Data Analyst for agentic_ai_clean.\n"
            "Your task is to analyze raw operational profile metrics and generate an executive efficiency summary report.\n\n"
            "RAW STUDENT PROFILE METRICS DATA:\n"
            "- Cumulative Calculated Study Hours: {study_time} hours\n"
            "- Mastered Concepts/Topics: {completed_topics}\n"
            "- Flagged Weak Target Domains: {weak_topics}\n"
            "- Historical Quiz Scores Dataset: {quiz_scores}\n\n"
            "REPORT CONTENT EXPECTATIONS CONTRACT:\n"
            "- Build an explicit SWOT analysis breakdown or diagnostic insight report layout context.\n"
            "- Highlight critical dynamic calibration ideas, tactical retention tips, and exact time-allocation advice.\n"
            "- Ensure the output is visually striking, using markdown headers (`##`), explicit data tables, and horizontal page breaks (`---`)."
        )

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate my personal study performance report profile for request loop target: '{user_input}'")
            ]
            
            response = self.llm.invoke(messages)
            
            logger.info("ProgressTrackerAgent successfully compiled analytical diagnostic report details.")
            return {
                "agent_output": {
                    "content": response.content,
                    "metrics_analyzed": {
                        "study_time": study_time,
                        "quiz_count": len(quiz_scores)
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error hit inside ProgressTrackerAgent processing thread execution: {str(e)}", exc_info=True)
            return {
                "agent_output": {"content": "I encountered an error trying to process performance analytics tracking information data models."},
                "errors": state.get("errors", []) + [f"ProgressTracker Agent Error: {str(e)}"]
            }