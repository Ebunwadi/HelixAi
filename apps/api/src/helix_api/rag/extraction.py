from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from helix_api.core.errors import AppError

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}


def extract_text(*, filename: str, content: bytes) -> str:
    """Extract plain text from the small baseline document types supported in Sprint 4."""

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise AppError(
            status_code=415,
            code="UNSUPPORTED_DOCUMENT_TYPE",
            message="Sprint 4 supports .txt, .md and .pdf documents",
        )

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AppError(
                status_code=422,
                code="DOCUMENT_DECODE_ERROR",
                message="Text documents must use UTF-8 encoding",
            ) from exc

    if not text.strip():
        raise AppError(
            status_code=422,
            code="DOCUMENT_EMPTY",
            message="No extractable text was found in the document",
        )

    return text
