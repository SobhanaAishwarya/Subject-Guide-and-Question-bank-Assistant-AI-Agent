from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Represents the complete, centralized state graph context for the StudyPilot AI 
    multi-agent supervisor routing topology.
    """
    # The primary input or current instruction provided by the user
    user_input: str
    
    # Structural identity context of the authenticated user
    user_id: int
    
    # Active configuration profiles (e.g., {"teacher_mode": "beginner", "quiz_type": "MCQ"})
    metadata: Dict[str, Any]
    
    # The next routing target determined by the Supervisor Agent
    next_agent: str
    
    # Complete, raw contextual chunks extracted via the RAG retrieval tier
    retrieved_context: Optional[str]
    
    # Citations mapping source documents back to responses for verification
    citations: List[Dict[str, Any]]
    
    # The running, chronological history of conversation messages within the workflow execution
    messages: List[BaseMessage]
    
    # Consolidated structural workspace payloads updated by specialized processing nodes
    # (e.g., compiled quizzes, generated notes objects, study schedules)
    agent_output: Dict[str, Any]
    
    # Error state tracker to gracefully capture, isolate, and debug failures within graph pipelines
    errors: List[str]