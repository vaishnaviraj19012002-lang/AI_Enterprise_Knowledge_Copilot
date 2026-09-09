import re
from pathlib import Path

from pypdf import PdfReader
from docx import Document


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


def extract_pdf(file):

    reader = PdfReader(file)

    text = ""

    for page_number, page in enumerate(reader.pages, start=1):

        page_text = page.extract_text()

        if page_text:

            text += (
                f"\n[Page {page_number}]\n"
                f"{page_text}\n"
            )

    return text


def extract_docx(file):

    document = Document(file)

    text = ""

    for paragraph in document.paragraphs:

        if paragraph.text.strip():

            text += paragraph.text + "\n"

    return text


def extract_txt(file):

    return file.read().decode(
        "utf-8",
        errors="ignore"
    )


def extract_text(file):

    extension = Path(file.name).suffix.lower()

    if extension == ".pdf":

        return extract_pdf(file)

    elif extension == ".docx":

        return extract_docx(file)

    elif extension == ".txt":

        return extract_txt(file)

    else:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )


def clean_text(text):

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def create_chunks(
    text,
    chunk_size=1200,
    overlap=200
):

    text = clean_text(text)

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():

            chunks.append(
                chunk.strip()
            )

        start += (
            chunk_size - overlap
        )

    return chunks