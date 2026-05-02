from __future__ import annotations

import logging
from fastapi import UploadFile

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None
    logger.warning("PyMuPDF (fitz) not found. PDF support disabled.")

try:
    from docx import Document
except ImportError:
    Document = None
    logger.warning("python-docx not found. DOCX support disabled.")


async def extract_text_from_upload(file: UploadFile) -> str:
    filename = file.filename.lower() if file.filename else "unknown"
    logger.info(f"Extracting text from: {filename}")
    data = await file.read()

    if filename.endswith(".pdf"):
        if fitz is None:
            logger.error("PDF extraction failed: PyMuPDF not installed.")
            raise RuntimeError("PDF support requires PyMuPDF. Install backend requirements first.")
        try:
            with fitz.open(stream=data, filetype="pdf") as document:
                text = "\n".join(page.get_text("text") for page in document)
                logger.debug(f"PDF extraction successful: {len(text)} characters.")
                return text
        except Exception as e:
            logger.exception(f"Error parsing PDF {filename}")
            raise

    if filename.endswith(".docx"):
        if Document is None:
            logger.error("DOCX extraction failed: python-docx not installed.")
            raise RuntimeError("DOCX support requires python-docx. Install backend requirements first.")
        try:
            from io import BytesIO
            document = Document(BytesIO(data))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            logger.debug(f"DOCX extraction successful: {len(text)} characters.")
            return text
        except Exception as e:
            logger.exception(f"Error parsing DOCX {filename}")
            raise

    try:
        text = data.decode("utf-8", errors="ignore")
        logger.debug(f"Raw text extraction successful: {len(text)} characters.")
        return text
    except Exception:
        logger.exception(f"Error decoding text from {filename}")
        return ""

