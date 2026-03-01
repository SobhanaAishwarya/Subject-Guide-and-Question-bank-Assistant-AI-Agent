# vector_store.py

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def create_vector_store(chunks):
    # Create embeddings
    embeddings = OpenAIEmbeddings()
    
    # Create FAISS vector store
    vectorstore = FAISS.from_texts(chunks, embeddings)
    
    return vectorstore