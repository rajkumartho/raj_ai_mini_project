
import pymupdf
import os


def extract_pdf_text(pdf_path):

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    document = pymupdf.open(pdf_path)

    pages_text = []

    for page_number, page in enumerate(
        document,
        start=1
    ):

        text = page.get_text()

        if text.strip():

            pages_text.append(
                f"\n--- PAGE {page_number} ---\n{text}"
            )

    document.close()

    full_text = "\n".join(
        pages_text
    ).strip()

    if not full_text:
        raise ValueError(
            f"No readable text found in {pdf_path}"
        )

    return full_text
