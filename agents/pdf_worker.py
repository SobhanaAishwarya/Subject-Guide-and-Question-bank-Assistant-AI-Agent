import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from models.state import AgentState
from rag.vector_store import VectorStoreFactory
from utils.logger import logger

class PDFWorkerAgent:
    """
    Production-grade PDF Worker Agent managing user-specific and built-in 
    RAG pipelines by querying target indices and returning structured contextual answers.
    """

    def __init__(self) -> None:
        """
        Initializes the Vector Factory and LLM orchestration configurations.
        """
        self.vector_factory = VectorStoreFactory()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
        
        logger.info(f"Initializing PDFWorkerAgent with model={self.model_name}")
        
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                temperature=0.2  # Lower temperature for highly factual answer synthesis
            )
        except Exception as e:
            logger.error(f"Failed to initialize PDFWorkerAgent LLM: {str(e)}", exc_info=True)
            raise e

    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Queries vector maps following a strict priority ladder: User PDFs -> Built-in Knowledge Base,
        synthesizes context chunks, formats detailed visual tables or structural logs, and tracks citations.
        """
        user_input = state.get("user_input", "")
        user_id = state.get("user_id", 0)
        
        logger.info(f"PDFWorkerAgent searching RAG pipeline layers for user_id={user_id}")
        
        retrieved_docs: List[Document] = []
        citations_list: List[Dict[str, Any]] = []

        # Tier 1 Priority: Query user-specific uploaded document indexes
        user_index_key = f"user_{user_id}_store"
        logger.info(f"Querying Tier 1 Priority Index: {user_index_key}")
        user_docs = self.vector_factory.query_index(user_index_key, user_input, top_k=4)
        if user_docs:
            retrieved_docs.extend(user_docs)
            logger.info(f"Tier 1 matched context: Found {len(user_docs)} relevant documentation segments.")

        # Tier 2 Priority: Fallback to global core knowledge bases if context limits are unfilled
        if len(retrieved_docs) < 3:
            logger.info("Tier 1 context metrics insufficient. Querying Tier 2 Global Built-in knowledge matrices.")
            kb_dir = os.getenv("BUILT_IN_KB_DIR", "knowledge_base")
            if os.path.exists(kb_dir):
                core_keys = [f.split(".")[0].lower() for f in os.listdir(kb_dir) if f.endswith(".pdf")]
                for key in core_keys:
                    global_index_key = f"global_kb_{key}"
                    global_docs = self.vector_factory.query_index(global_index_key, user_input, top_k=2)
                    if global_docs:
                        retrieved_docs.extend(global_docs)
                        if len(retrieved_docs) >= 5:
                            break

        # Compile string payload buffers and extract systematic metadata attributes for citations
        context_buffer: List[str] = []
        for i, doc in enumerate(retrieved_docs):
            src_name = doc.metadata.get("source", "Unknown Document")
            pg_num = doc.metadata.get("page", "N/A")
            
            context_buffer.append(f"--- Context Segment [{i+1}] (Source: {src_name}, Page: {pg_num}) ---\n{doc.page_content}")
            
            citations_list.append({
                "citation_index": i + 1,
                "source": src_name,
                "page": pg_num,
                "snippet": doc.page_content[:150] + "..."
            })

        compiled_context = "\n\n".join(context_buffer)

        # Prompt system engineering instructions for factual synthesis grounding
        system_prompt = (
            "You are an expert Document Analysis and RAG Synthesis Agent for agentic_ai_clean.\n"
            "Your objective is to answer the user's questions truthfully based ONLY on the provided context segments below.\n\n"
            "CONTEXT SEGMENTS:\n"
            f"{compiled_context}\n\n"
            "CRITICAL CONSTRAINTS:\n"
            "- If the provided context does not contain sufficient information to satisfy the query, fallback cleanly to your general knowledge while explicitly stating that the answer uses standard model training data rather than document records.\n"
            "- Integrate source numbers directly into sentences where claims are made (e.g., 'As shown in [Source: OS.pdf, Page: 12]...').\n"
            "- Structure your output beautifully with clear headers (`##`), clean bold emphasis, and data tables where helpful."
        )

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Answer the query: {user_input}")
            ]
            
            response = self.llm.invoke(messages)
            
            return {
                "retrieved_context": compiled_context,
                "citations": citations_list,
                "agent_output": {
                    "content": response.content,
                    "has_citations": len(citations_list) > 0
                }
            }
        except Exception as e:
            logger.error(f"Error occurred during execution inside PDFWorkerAgent loop: {str(e)}", exc_info=True)
            return {
                "agent_output": {"content": "I encountered an issue searching the document repositories. Please ensure your files are indexed completely."},
                "errors": state.get("errors", []) + [f"PDF Worker Error: {str(e)}"]
            }