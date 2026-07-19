import os
from typing import List, Optional
from sqlalchemy.orm import Session
from database.schemas import UploadedPDF
from rag.text_processor import TextProcessor
from rag.vector_store import VectorStoreFactory
from utils.logger import logger

class PDFService:
    """
    Production-grade Service layer orchestrating storage file interactions, 
    relational database auditing tracks, and vector matrix sharding operations.
    """

    def __init__(self) -> None:
        """
        Initializes processing systems and structural embedding store factories.
        """
        self.processor = TextProcessor()
        self.vector_factory = VectorStoreFactory()
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        self.kb_dir = os.getenv("BUILT_IN_KB_DIR", "knowledge_base")
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.kb_dir, exist_ok=True)

    def process_and_index_user_pdf(self, session: Session, user_id: int, filename: str, file_bytes: bytes) -> Optional[UploadedPDF]:
        """
        Saves a newly uploaded raw file byte cluster locally, writes systemic 
        auditing tables records, and chunks the contents into user-isolated FAISS blocks.
        """
        try:
            # Enforce strict spatial multi-tenant directory segmentation structure
            user_folder = os.path.join(self.upload_dir, f"user_{user_id}")
            os.makedirs(user_folder, exist_ok=True)
            
            target_path = os.path.join(user_folder, filename)
            logger.info(f"Writing incoming PDF payload stream locally to: {target_path}")
            
            with open(target_path, "wb") as f:
                f.write(file_bytes)
            
            # Append track data profile inside persistence layer engine
            pdf_record = UploadedPDF(
                user_id=user_id,
                filename=filename,
                filepath=target_path
            )
            session.add(pdf_record)
            session.flush()  # Generate transaction identity contexts safely
            
            # Execute embedding extraction and build vector matrix mapping structures
            logger.info(f"Extracting semantic nodes for document chunk execution: {filename}")
            chunks = self.processor.process_pdf_into_chunks(target_path)
            
            # Define private multi-tenant index signature key mapping
            user_index_key = f"user_{user_id}_store"
            self.vector_factory.create_or_update_index(user_index_key, chunks)
            
            logger.info(f"Successfully committed and isolated vector sets for user {user_id}: {filename}")
            return pdf_record
            
        except Exception as e:
            logger.error(f"Failed transaction flow execution inside process_and_index_user_pdf: {str(e)}", exc_info=True)
            return None

    def initialize_global_knowledge_base(self) -> None:
        """
        Scans global structural knowledge directories once and indexes built-in core textbooks 
        (e.g., OS.pdf, DBMS.pdf) into a shared systemic vector layout map space.
        """
        try:
            logger.info(f"Scanning built-in library directories targets for core assets updates: {self.kb_dir}")
            if not os.path.exists(self.kb_dir):
                logger.warning(f"Knowledge directory '{self.kb_dir}' missing; aborting baseline setup.")
                return

            core_files = [f for f in os.listdir(self.kb_dir) if f.endswith(".pdf")]
            if not core_files:
                logger.info("No base systemic textbooks detected inside the global knowledge folder layout path.")
                return

            for filename in core_files:
                target_path = os.path.join(self.kb_dir, filename)
                logger.info(f"Checking baseline vector map allocation updates for: {filename}")
                
                # Dynamic multi-tenant system handles global indexes uniquely
                global_index_key = f"global_kb_{filename.split('.')[0].lower()}"
                
                # Prevent running extraction maps if vector targets exist locally already
                store_check_path = os.path.join(os.getenv("VECTOR_STORE_DIR", "vectorstores"), global_index_key)
                if os.path.exists(os.path.join(store_check_path, "index.faiss")):
                    logger.debug(f"Vector matrix already compiled down securely for target: {global_index_key}")
                    continue
                    
                logger.info(f"Compiling baseline structural indices for core knowledge node: {filename}")
                chunks = self.processor.process_pdf_into_chunks(target_path)
                self.vector_factory.create_or_update_index(global_index_key, chunks)
                
            logger.info("Global textbook core knowledge base synchronized perfectly.")
        except Exception as e:
            logger.error(f"Failed parsing process metrics during initialize_global_knowledge_base execution: {str(e)}", exc_info=True)

    def get_user_uploaded_pdfs(self, session: Session, user_id: int) -> List[UploadedPDF]:
        """
        Retrieves structural persistence tracking records for files matching user keys.
        """
        try:
            return session.query(UploadedPDF).filter(UploadedPDF.user_id == user_id).all()
        except Exception as e:
            logger.error(f"Error fetching document metadata list details for user {user_id}: {str(e)}")
            return []