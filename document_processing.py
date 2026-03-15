import fitz
import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_pdf(file):

    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")

    for page in pdf:
        text += page.get_text()

    return text


def load_docx(file):

    doc = docx.Document(file)
    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text


def split_text(text):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_text(text)

    return chunks