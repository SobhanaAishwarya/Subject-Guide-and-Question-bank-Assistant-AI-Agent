# document_processing.py

import PyPDF2
import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 1️ Function to load PDF
def load_pdf(file):
    text = ""
    reader = PyPDF2.PdfReader(file)
    
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    
    return text


# 2️ Function to load DOCX
def load_docx(file):
    doc = docx.Document(file)
    text = ""
    
    for para in doc.paragraphs:
        text += para.text + "\n"
    
    return text


# 3️ Function to split text into chunks
def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    
    chunks = splitter.split_text(text)
    
    return chunks