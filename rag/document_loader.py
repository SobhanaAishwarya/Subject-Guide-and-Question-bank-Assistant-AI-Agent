from pypdf import PdfReader
from docx import Document


def load_pdf(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def load_docx(file_path):

    doc = Document(file_path)

    text = "\n".join(
        para.text
        for para in doc.paragraphs
    )

    return text


def load_document(file_path):

    if file_path.endswith(".pdf"):
        return load_pdf(file_path)

    elif file_path.endswith(".docx"):
        return load_docx(file_path)

    else:
        raise ValueError(
            "Unsupported File Format"
        )