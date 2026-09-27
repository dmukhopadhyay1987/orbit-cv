import base64
import io
import re
from docx import Document
from pypdf import PdfReader


def clean_and_decode_b64(b64_str: str) -> bytes:
    """Strips headers, whitespace, and padding to decode raw base64 bytes."""
    cleaned = re.sub(r"\s+", "", b64_str.strip().strip("'\""))
    if "," in cleaned:
        cleaned = cleaned.split(",", 1)[1]
    missing_padding = len(cleaned) % 4
    if missing_padding:
        cleaned += "=" * (4 - missing_padding)
    return base64.b64decode(cleaned)


def extract_text_from_bytes(file_bytes: bytes, filename: str = "") -> str:
    """Attempts PDF, DOCX, and plain text extraction from binary stream."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes), strict=False)
        pages_text = [p.extract_text() for p in reader.pages if p.extract_text()]
        if pages_text:
            return "\n".join(pages_text)
    except Exception:
        pass

    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        if paragraphs:
            return "\n".join(paragraphs)
    except Exception:
        pass

    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return f"[Unable to extract readable text from attached file: {filename}]"