import os
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import AgentState
from utils.logger import logger

class SupervisorAgent:
    """
    Production-grade Supervisor Agent responsible for analyzing user intent,
    evaluating conversational context, and dynamically routing workflows to the 
    appropriate worker node within the LangGraph orchestrator.
    """

    def __init__(self) -> None:
        """
        Initializes the Supervisor LLM engine with OpenRouter support parameters.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "[https://api.openai.com/v1](https://api.openai.com/v1)")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing SupervisorAgent LLM with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.0  # Determinisitc zero-variance routing classification
            )
        except Exception as e:
            logger.error(f"Failed to initialize SupervisorAgent LLM engine: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Analyzes the current AgentState payload, runs an intent classification 
        evaluation cycle against the user query, and determines the routing destination.
        """
        user_input = state.get("user_input", "")
        logger.info(f"Supervisor parsing intent classification loop for input string: '{user_input[:60]}...'")

        system_prompt = (
            "You are the Core Orchestrator and Supervisor Agent for agentic_ai_clean, an advanced Study Assistant.\n"
            "Your explicit goal is to categorize the user's intent based on their prompt and designate the absolute best downstream worker agent.\n\n"
            "AVAILABLE WORKER AGENTS AND TARGET ROLES:\n"
            "1. 'teacher' -> General conceptual questions, requesting detailed explanations of topics (OS, DBMS, DSA, OOPS, CN, or custom subjects), or entering special learning profiles (beginner, advanced, interview mode).\n"
            "2. 'pdf_worker' -> Explicit references to searching or answering questions using files uploaded directly by the user.\n"
            "3. 'quiz_master' -> Requests to generate testing quizzes, evaluate knowledge levels, build multiple-choice questions (MCQs), fill-in-the-blanks, or coding challenges.\n"
            "4. 'notes_generator' -> Creating condensed summaries, itemized bulleted review sheets, key takeaway documents, or math/science formula configurations.\n"
            "5. 'flashcard_worker' -> Creating rapid-fire question/answer study cards or deck blocks.\n"
            "6. 'planner' -> Generating tailored semester schedules, study roadmaps, exam timelines, or calendar plans.\n"
            "7. 'progress_tracker' -> Fetching statistical mastery reports, checking weak learning topics, logging finished chapters, or reading historic performance curves.\n"
            "8. 'end' -> If the user is saying goodbye, closing the session, or completely finished with the learning interaction.\n\n"
            "CRITICAL OUTPUT RULES:\n"
            "- You must return output EXCLUSIVELY as a valid JSON object containing a single key: \"next_agent\".\n"
            "- Do not wrap the output in markdown code blocks like ```json ... ```. Output raw JSON plaintext string text only.\n"
            "- Example valid responses: {\"next_agent\": \"teacher\"} or {\"next_agent\": \"quiz_master\"}"
        )

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Classify the following user request and determine the target worker routing: \n\n'{user_input}'")
            ]
            
            # Execute inference
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Clean potential markdown wrapping artifacts if the LLM defaults to code blocks
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    response_text = "\n".join(lines[1:-1])
            
            # Parse classification token payload
            parsed_json = json.loads(response_text)
            next_target = parsed_json.get("next_agent", "teacher")
            
            # Structural safety fallback validation bounds
            valid_agents = ["teacher", "pdf_worker", "quiz_master", "notes_generator", "flashcard_worker", "planner", "progress_tracker", "end"]
            if next_target not in valid_agents:
                logger.warning(f"Supervisor routed to invalid agent '{next_target}'. Overriding target default to 'teacher'.")
                next_target = "teacher"

            logger.info(f"Supervisor routing execution determined destination target success: '{next_target}'")
            return {"next_agent": next_target}

        except Exception as e:
            logger.error(f"Supervisor routing extraction failure. Defaulting trajectory node structure to 'teacher'. Error: {str(e)}")
            return {"next_agent": "teacher", "errors": state.get("errors", []) + [f"Supervisor Error: {str(e)}"]}