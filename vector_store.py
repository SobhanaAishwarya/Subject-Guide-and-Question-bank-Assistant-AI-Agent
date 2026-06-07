from langchain_core.documents import Document

class SimpleVectorStore:

    def __init__(self, chunks):
        self.docs = [Document(page_content=chunk) for chunk in chunks]

    def similarity_search(self, query, k=5):
        return self.docs[:k]

def create_vector_store(chunks):
    return SimpleVectorStore(chunks)