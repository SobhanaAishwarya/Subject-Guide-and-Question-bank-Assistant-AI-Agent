import os
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from utils.logger import logger

class VectorStoreFactory:
    """
    Production-grade Vector Storage Factory handling multi-tenant indexing structures.
    Manages isolated FAISS indexes for global built-in knowledge bases as well as 
    user-specific uploaded files using OpenRouter-compatible OpenAI embeddings.
    """

    def __init__(self) -> None:
        """
        Initializes the Embedding model engine using parameters defined in environmental configurations.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        logger.info(f"Initializing OpenAIEmbeddings with model={self.embedding_model} via base={self.api_base}")
        
        try:
            # Explicit parameters mapping directly to the configured endpoint context
            self.embeddings = OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=self.api_key,
                openai_api_base=self.api_base
            )
        except Exception as e:
            logger.error(f"Failed to instantiate OpenAIEmbeddings client engine: {str(e)}", exc_info=True)
            raise e

        # Persistent storage directories
        self.vector_store_dir = os.getenv("VECTOR_STORE_DIR", "vectorstores")
        os.makedirs(self.vector_store_dir, exist_ok=True)

    def _get_index_path(self, index_name: str) -> str:
        """
        Resolves the local storage folder path directory for a given unique index handle.
        """
        return os.path.join(self.vector_store_dir, index_name)

    def create_or_update_index(self, index_name: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Converts structural dictionary raw fragments into standard LangChain Document instances,
        builds a local FAISS semantic index vector map, and commits it securely to local disk storage.
        """
        if not chunks:
            logger.warning(f"Index creation aborted for '{index_name}': Received empty processing chunks payload.")
            return

        try:
            logger.info(f"Constructing LangChain Document models for index vector map: {index_name}")
            documents = [
                Document(page_content=chunk["page_content"], metadata=chunk["metadata"])
                for chunk in chunks
            ]

            index_path = self._get_index_path(index_name)
            
            if os.path.exists(os.path.join(index_path, "index.faiss")):
                logger.info(f"Loading historic FAISS local file matrix to merge incoming chunks: {index_name}")
                db = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
                db.add_documents(documents)
            else:
                logger.info(f"Generating absolute fresh FAISS structural matrix layout for index: {index_name}")
                db = FAISS.from_documents(documents, self.embeddings)

            db.save_local(index_path)
            logger.info(f"Successfully serialized structural vector matrices to target path context: {index_path}")
        except Exception as e:
            logger.error(f"Critical index write crash hit inside create_or_update_index for '{index_name}': {str(e)}", exc_info=True)
            raise e

    def query_index(self, index_name: str, query: str, top_k: int = 4) -> List[Document]:
        """
        Searches a targeted FAISS local store index using cosine similarity vectors.
        Returns an empty list context smoothly if index mapping files do not exist.
        """
        index_path = self._get_index_path(index_name)
        if not os.path.exists(os.path.join(index_path, "index.faiss")):
            logger.info(f"Query index target '{index_name}' requested but no local filesystem asset index was found.")
            return []

        try:
            logger.debug(f"Querying local index target vector base: '{index_name}' with top_k={top_k}")
            db = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
            results = db.similarity_search(query, k=top_k)
            return results
        except Exception as e:
            logger.error(f"Error executing similarity search parameters on local store index '{index_name}': {str(e)}", exc_info=True)
            return []