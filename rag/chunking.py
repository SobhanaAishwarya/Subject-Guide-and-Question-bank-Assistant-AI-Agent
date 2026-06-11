from langchain_text_splitters import (
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

    return splitter.split_text(text)