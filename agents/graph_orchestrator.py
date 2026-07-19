import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from models.state import AgentState
from agents.supervisor import SupervisorAgent
from agents.teacher import TeacherAgent
from agents.pdf_worker import PDFWorkerAgent
from agents.quiz_master import QuizMasterAgent
from agents.notes_generator import NotesGeneratorAgent
from agents.flashcard_worker import FlashcardWorkerAgent
from agents.planner import StudyPlannerAgent
from agents.progress_tracker import ProgressTrackerAgent
from utils.logger import logger

class GraphOrchestrator:
    """
    Production-grade LangGraph Orchestrator compiling the supervisor multi-agent 
    state graph topology network.
    """

    def __init__(self) -> None:
        """
        Instantiates every specialized domain agent node worker inside the system runtime map.
        """
        logger.info("Initializing multi-agent structural graph component objects...")
        self.supervisor = SupervisorAgent()
        self.teacher = TeacherAgent()
        self.pdf_worker = PDFWorkerAgent()
        self.quiz_master = QuizMasterAgent()
        self.notes_generator = NotesGeneratorAgent()
        self.flashcard_worker = FlashcardWorkerAgent()
        self.planner = StudyPlannerAgent()
        self.progress_tracker = ProgressTrackerAgent()
        
        # Compile operational graph structure layout
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self) -> Any:
        """
        Constructs structural graph state mapping channels, links processing execution nodes, 
        and validates edge routing keys.
        """
        workflow = StateGraph(AgentState)

        # 1. Register Core Structural Nodes
        workflow.add_node("supervisor_node", self.supervisor.process)
        workflow.add_node("teacher_node", self.teacher.process)
        workflow.add_node("pdf_worker_node", self.pdf_worker.process)
        workflow.add_node("quiz_master_node", self.quiz_master.process)
        workflow.add_node("notes_generator_node", self.notes_generator.process)
        workflow.add_node("flashcard_worker_node", self.flashcard_worker.process)
        workflow.add_node("planner_node", self.planner.process)
        workflow.add_node("progress_tracker_node", self.progress_tracker.process)

        # 2. Wire Entry Points
        workflow.set_entry_point("supervisor_node")

        # 3. Define Conditional Routing Rules Contract
        routing_map = {
            "teacher": "teacher_node",
            "pdf_worker": "pdf_worker_node",
            "quiz_master": "quiz_master_node",
            "notes_generator": "notes_generator_node",
            "flashcard_worker": "flashcard_worker_node",
            "planner": "planner_node",
            "progress_tracker": "progress_tracker_node",
            "end": END
        }

        def router_edge_logic(state: AgentState) -> str:
            """
            Extracts supervisor evaluation keys out of state graph payload to direct next hop.
            """
            next_agent_key = state.get("next_agent", "teacher")
            logger.info(f"Graph Router processing conditional transition edge target to: {next_agent_key}")
            return next_agent_key

        # Link supervisor branching routes conditionally
        workflow.add_conditional_edges(
            "supervisor_node",
            router_edge_logic,
            routing_map
        )

        # 4. Connect Operational Workers directly back to terminal execution bounds safely
        workflow.add_edge("teacher_node", END)
        workflow.add_edge("pdf_worker_node", END)
        workflow.add_edge("quiz_master_node", END)
        workflow.add_edge("notes_generator_node", END)
        workflow.add_edge("flashcard_worker_node", END)
        workflow.add_edge("planner_node", END)
        workflow.add_edge("progress_tracker_node", END)

        logger.info("LangGraph workflow state structure successfully wired and compiled.")
        return workflow.compile()

    def run_workflow(self, initial_state: AgentState) -> Dict[str, Any]:
        """
        Invokes execution of the state graph engine loop.
        """
        try:
            logger.info(f"Graph engine processing run loop execution for user_id={initial_state.get('user_id')}")
            result_state = self.graph.invoke(initial_state)
            return result_state
        except Exception as e:
            logger.error(f"Fatal crash encountered during graph execution flow turn: {str(e)}", exc_info=True)
            return {
                "agent_output": {"content": "The underlying multi-agent routing loop encountered a structural execution processing timeout."},
                "errors": [f"Graph Error: {str(e)}"]
            }