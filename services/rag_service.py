import os
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from config import Config

class SimpleFAISSStore:
    def __init__(self):
        # Using a fast, lightweight sentence transformer model suited for CPU tracking layouts
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index_file = os.path.join(Config.VECTOR_DIR, "faiss_store.pkl")
        self.documents = []
        self.embeddings = []
        self.load()

    def save(self):
        with open(self.index_file, "wb") as f:
            pickle.dump({"documents": self.documents, "embeddings": self.embeddings}, f)

    def load(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, "rb") as f:
                data = pickle.load(f)
                self.documents = data.get("documents", [])
                self.embeddings = data.get("embeddings", [])

    def add_texts(self, texts: list, metadata: dict):
        if not texts:
            return
        new_embs = self.encoder.encode(texts, show_progress_bar=False)
        for text, emb in zip(texts, new_embs):
            self.documents.append({"text": text, "metadata": metadata})
            self.embeddings.append(emb)
        self.save()

    def similarity_search(self, query: str, k: int = 3):
        if not self.embeddings:
            return []
        query_emb = self.encoder.encode([query])[0]
        
        scores = []
        for idx, emb in enumerate(self.embeddings):
            dot_prod = np.dot(query_emb, emb)
            norm_q = np.linalg.norm(query_emb)
            norm_e = np.linalg.norm(emb)
            cosine_sim = dot_prod / (norm_q * norm_e + 1e-9)
            scores.append((cosine_sim, self.documents[idx]))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scores[:k]]