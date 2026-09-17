"""Real text extraction for uploaded resume/JD files. Before this, the
"Uploaded" source label had no real server-side file-upload path at all —
the frontend read a file's text client-side via `file.text()` and submitted
it through the same paste endpoint, which works for .txt but produces
garbage for binary formats like .docx/.pdf. This module extracts genuine
text server-side for .txt/.md/.docx/.pdf, raising a clean AppError (never a
raw crash) for anything unsupported, corrupt, or unreadable."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from app.core.errors import AppError

if TYPE_CHECKING:
    from fastapi import UploadFile

SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # a resume/JD is always small text
_READ_CHUNK_BYTES = 1024 * 1024


async def read_upload_bounded(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    """Reads an UploadFile in bounded chunks, rejecting it the moment the
    total exceeds `max_bytes` — never buffering an oversized file fully into
    memory first. A plain `await file.read()` reads the WHOLE upload before
    any size check could run, so a multi-GB upload would be fully read into
    memory regardless of the (otherwise correct) limit `extract_text` checks
    afterward."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise AppError(f"File is too large (max {max_bytes // (1024 * 1024)}MB).")
        chunks.append(chunk)
    return b"".join(chunks)


def extract_text(filename: str, content: bytes) -> str:
    if len(content) > MAX_UPLOAD_BYTES:
        raise AppError(f"File is too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)}MB).")

    suffix = _suffix(filename)
    if suffix in (".txt", ".md"):
        text = _decode_text(content)
    elif suffix == ".docx":
        text = _extract_docx(content)
    elif suffix == ".pdf":
        text = _extract_pdf(content)
    else:
        raise AppError(
            f'Unsupported file type "{suffix or filename}". Supported: '
            f"{', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    # Postgres text columns reject a literal NUL byte outright — strip it
    # defensively on every path (not just binary formats) rather than let an
    # otherwise-valid save 500 with no user-facing explanation.
    text = text.replace("\x00", "").strip()
    if not text:
        raise AppError("No readable text was found in this file.")
    return text


def _suffix(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


def _decode_text(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise AppError("Could not decode this file as text.") from exc


def _extract_docx(content: bytes) -> str:
    import docx

    try:
        document = docx.Document(io.BytesIO(content))
    except Exception as exc:
        raise AppError("Could not read this .docx file — it may be corrupt.") from exc

    paragraphs = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            paragraphs.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(p for p in paragraphs if p.strip())


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise AppError("This PDF is password-protected and can't be read.")
    except AppError:
        raise
    except PdfReadError as exc:
        raise AppError("Could not read this .pdf file — it may be corrupt.") from exc

    pages_text: list[str] = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(pages_text)
