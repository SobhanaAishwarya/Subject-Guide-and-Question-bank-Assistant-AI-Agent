import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import logger

class TextProcessor:
    """
    Production-grade text processing layer designed to extract text contents from PDFs 
    using PyMuPDF and perform sliding-window structural chunking using LangChain.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        """
        Initializes the text processor with specified split dimensions.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )
        logger.info(f"TextProcessor initialized with chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")

    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a PDF file page by page using PyMuPDF (fitz) and captures content
        along side granular structural metadata signatures.
        """
        if not os.path.exists(file_path):
            logger.error(f"Extraction failed: File path does not exist at {file_path}")
            raise FileNotFoundError(f"Target PDF file not found at: {file_path}")

        pages_data: List[Dict[str, Any]] = []
        try:
            logger.info(f"Opening PDF document for text extraction: {file_path}")
            with fitz.open(file_path) as doc:
                filename = os.path.basename(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    # Track page text context along side clear citation metadata boundaries
                    pages_data.append({
                        "text": text,
                        "metadata": {
                            "source": filename,
                            "page": page_num + 1,
                            "filepath": file_path
                        }
                    })
            logger.info(f"Successfully extracted {len(pages_data)} pages from {file_path}")
            return pages_data
        except Exception as e:
            logger.error(f"Critical error occurred while parsing PDF file {file_path}: {str(e)}", exc_info=True)
            raise e

    def process_pdf_into_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """
        High-level orchestrator that extracts text out of a file target and shards
        it into optimized chunk segments while cleanly retaining citation attributes.
        """
        try:
            pages = self.extract_text_from_pdf(file_path)
            all_chunks: List[Dict[str, Any]] = []
            
            for page in pages:
                page_text = page["text"]
                page_meta = page["metadata"]
                
                # Skip empty pages to optimize indexing space
                if not page_text.strip():
                    continue
                
                # Split single page content while propagating original parent metadata signatures
                chunks = self.text_splitter.split_text(page_text)
                for chunk in chunks:
                    all_chunks.append({
                        "page_content": chunk,
                        "metadata": page_meta.copy()
                    })
                    
            logger.info(f"Transformed document {file_path} into {len(all_chunks)} semantic embedding chunks.")
            return all_chunks
        except Exception as e:
            logger.error(f"Failed processing flow inside process_pdf_into_chunks for {file_path}: {str(e)}", exc_info=True)
            raise e