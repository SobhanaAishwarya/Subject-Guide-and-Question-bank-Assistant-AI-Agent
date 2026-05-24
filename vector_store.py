from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load embedding model
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


class SimpleVectorStore:

    def __init__(self, chunks):

        self.chunks = chunks

        # Create embeddings
        self.embeddings = embedding_model.encode(chunks)

    def similarity_search(self, query, k=5):

        # Query embedding
        query_embedding = embedding_model.encode([query])

        # Compute similarity
        similarities = cosine_similarity(
            query_embedding,
            self.embeddings
        )[0]

        # Top k indices
        top_indices = np.argsort(similarities)[::-1][:k]

        # Return relevant chunks
        docs = []

        for idx in top_indices:

            docs.append(
                type(
                    "Document",
                    (),
                    {"page_content": self.chunks[idx]}
                )
            )

        return docs


def create_vector_store(chunks):

    return SimpleVectorStore(chunks)