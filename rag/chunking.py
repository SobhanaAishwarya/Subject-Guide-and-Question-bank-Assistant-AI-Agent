from langchain.text_splitter import (
    RecursiveCharacterTextSplitter
)

from config.settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP
)


def create_chunks(text):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = splitter.split_text(text)

    return chunks