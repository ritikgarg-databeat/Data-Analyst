"""Real server-side text extraction for uploaded resume/JD files — a
follow-up to Phase 12's frontend file-upload fix, which only ever read a
file's text client-side (fine for .txt, garbage for .docx/.pdf). Covers the
extraction utility directly and the two new upload endpoints end to end."""

from __future__ import annotations

import asyncio
import io

import docx
import pytest
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.core.file_extraction import extract_text, read_upload_bounded


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# pypdf's writer has no text-drawing API of its own, so a real, minimal,
# handwritten single-page PDF (one Helvetica text-showing stream) is used to
# exercise genuine text extraction rather than a library-generated blank page.
MINIMAL_TEXT_PDF = b"""%PDF-1.1
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >>
/MediaBox [0 0 200 200] /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length 58 >>
stream
BT /F1 12 Tf 20 100 Td (Data Analyst Resume) Tj ET
endstream
endobj
xref
0 6
trailer << /Size 6 /Root 1 0 R >>
startxref
0
%%EOF"""


class TestExtractTextUtility:
    def test_plain_text_file_decodes_as_utf8(self) -> None:
        assert extract_text("resume.txt", b"Led a team of 5 analysts.") == "Led a team of 5 analysts."

    def test_markdown_file_is_treated_as_text(self) -> None:
        assert extract_text("resume.md", b"# Resume\n\nBuilt dashboards.") == "# Resume\n\nBuilt dashboards."

    def test_docx_paragraphs_are_extracted_in_order(self) -> None:
        content = _make_docx_bytes(["Jane Analyst", "Built a churn model reducing churn by 12%."])
        text = extract_text("resume.docx", content)
        assert "Jane Analyst" in text
        assert "Built a churn model reducing churn by 12%." in text

    def test_docx_table_cells_are_extracted(self) -> None:
        document = docx.Document()
        table = document.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "SQL"
        table.rows[0].cells[1].text = "Advanced"
        buffer = io.BytesIO()
        document.save(buffer)
        text = extract_text("resume.docx", buffer.getvalue())
        assert "SQL" in text
        assert "Advanced" in text

    def test_real_pdf_text_is_extracted(self) -> None:
        text = extract_text("resume.pdf", MINIMAL_TEXT_PDF)
        assert "Data Analyst Resume" in text

    def test_unsupported_extension_raises_app_error(self) -> None:
        with pytest.raises(AppError):
            extract_text("resume.exe", b"binary garbage")

    def test_corrupt_docx_raises_app_error_not_a_crash(self) -> None:
        with pytest.raises(AppError):
            extract_text("resume.docx", b"not actually a docx file")

    def test_corrupt_pdf_raises_app_error_not_a_crash(self) -> None:
        with pytest.raises(AppError):
            extract_text("resume.pdf", b"not actually a pdf file")

    def test_empty_extracted_text_raises_app_error(self) -> None:
        content = _make_docx_bytes(["   ", ""])
        with pytest.raises(AppError):
            extract_text("resume.docx", content)

    def test_oversized_file_raises_app_error(self) -> None:
        huge = b"a" * (11 * 1024 * 1024)
        with pytest.raises(AppError):
            extract_text("resume.txt", huge)

    def test_non_utf8_bytes_fall_back_to_latin1(self) -> None:
        content = "Café analyst résumé".encode("latin-1")
        assert extract_text("resume.txt", content) == "Café analyst résumé"


class _CountingFakeUploadFile:
    """A minimal async-`.read(size)` duck-type of `fastapi.UploadFile` that
    counts how many chunked reads it served — enough to prove
    `read_upload_bounded` never buffers a whole oversized file before its
    size check can trip, unlike a single unbounded `await file.read()`."""

    def __init__(self, content: bytes) -> None:
        self._buf = io.BytesIO(content)
        self.read_calls = 0

    async def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        return self._buf.read(size)


class TestReadUploadBounded:
    """Regression tests — the resume/JD upload routers used to call a plain
    `await file.read()`, buffering the ENTIRE upload into memory before
    `extract_text`'s own size check could ever run. `read_upload_bounded`
    reads in fixed-size chunks and rejects the upload the moment the running
    total exceeds the limit."""

    def test_rejects_an_oversized_upload_without_reading_it_in_one_shot(self) -> None:
        oversized = b"a" * (50 * 1024 * 1024)
        fake_file = _CountingFakeUploadFile(oversized)

        async def _run() -> None:
            with pytest.raises(AppError):
                await read_upload_bounded(fake_file, max_bytes=5 * 1024 * 1024)

        asyncio.run(_run())
        # A handful of chunked reads, not one read call that would have
        # consumed the full 50MB before the limit could ever be checked.
        assert fake_file.read_calls < 10

    def test_accepts_and_returns_content_within_the_limit(self) -> None:
        content = b"hello world " * 100
        fake_file = _CountingFakeUploadFile(content)

        async def _run() -> bytes:
            return await read_upload_bounded(fake_file, max_bytes=10 * 1024 * 1024)

        assert asyncio.run(_run()) == content


class TestResumeUploadEndpoint:
    def test_upload_txt_creates_a_real_version(self, client: TestClient) -> None:
        resume = client.post("/api/v1/resume", json={"title": "My Resume", "is_primary": True}).json()
        response = client.post(
            f"/api/v1/resume/{resume['id']}/versions/upload",
            files={"file": ("resume.txt", b"Increased revenue by 20% via a pricing analysis.", "text/plain")},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["source"] == "UPLOADED"
        assert body["file_name"] == "resume.txt"
        assert "Increased revenue by 20%" in body["raw_text"]

    def test_upload_docx_extracts_real_text(self, client: TestClient) -> None:
        resume = client.post("/api/v1/resume", json={"title": "My Resume", "is_primary": True}).json()
        content = _make_docx_bytes(["Reduced churn by 8 points using a cohort analysis."])
        response = client.post(
            f"/api/v1/resume/{resume['id']}/versions/upload",
            files={
                "file": (
                    "resume.docx",
                    content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert response.status_code == 201
        assert "Reduced churn by 8 points" in response.json()["raw_text"]

    def test_upload_unsupported_type_returns_a_clean_error(self, client: TestClient) -> None:
        resume = client.post("/api/v1/resume", json={"title": "My Resume", "is_primary": True}).json()
        response = client.post(
            f"/api/v1/resume/{resume['id']}/versions/upload",
            files={"file": ("resume.exe", b"garbage", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert response.json()["error"]["request_id"]


class TestJobDescriptionUploadEndpoint:
    def test_upload_txt_creates_a_real_job_description(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/jobs/descriptions/upload",
            data={"title": "Data Analyst", "company": "Acme Corp"},
            files={"file": ("jd.txt", b"Requires strong SQL and dashboarding experience.", "text/plain")},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["source"] == "UPLOADED"
        assert body["title"] == "Data Analyst"
        assert body["company"] == "Acme Corp"
        assert "SQL" in body["raw_text"]
