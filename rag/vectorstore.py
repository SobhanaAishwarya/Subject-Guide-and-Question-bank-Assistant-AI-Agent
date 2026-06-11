import pickle
import os

from langchain_community.vectorstores import (
    FAISS
)

from langchain.embeddings.base import Embeddings

from rag.embeddings import (
    get_embedding_model
)

from config.settings import (
    VECTORSTORE_DIR
)


class LocalEmbeddings(Embeddings):

    def __init__(self):

        self.model = get_embedding_model()

    def embed_documents(
        self,
        texts
    ):

        return self.model.encode(
            texts
        ).tolist()

    def embed_query(
        self,
        text
    ):

        return self.model.encode(
            text
        ).tolist()


def create_vectorstore(chunks):

    embeddings = LocalEmbeddings()

    vectorstore = FAISS.from_texts(
        chunks,
        embeddings
    )

    return vectorstore


def save_vectorstore(
        vectorstore,
        filename="knowledge_base"
):
    os.makedirs(
        VECTORSTORE_DIR,
        exist_ok=True
    )
    path = os.path.join(
        VECTORSTORE_DIR,
        exist_ok=True
    )
    path=os.path.join(
        VECTORSTORE_DIR,
        filename
    )
    vectorstore.save_local(path)


def load_vectorstore(
        filename="knowledge_base"
):

    embeddings = LocalEmbeddings()

    path = os.path.join(
        VECTORSTORE_DIR,
        filename
    )
    return FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True
    )