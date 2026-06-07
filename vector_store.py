from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FakeEmbeddings

def create_vector_store(chunks):

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=FakeEmbeddings(
            size=384
        )
    )

    return vectorstore