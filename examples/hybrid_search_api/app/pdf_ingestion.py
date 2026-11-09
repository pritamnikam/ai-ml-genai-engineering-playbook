"""Extract bounded, page-aware text chunks from uploaded PDF documents."""

import re
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 500
MAX_EXTRACTED_CHARACTERS = 5_000_000
CHUNK_WORDS = 400
CHUNK_OVERLAP_WORDS = 60
MAX_CHUNK_CHARACTERS = 6_000


class PdfIngestionError(ValueError):
    """Raised for PDFs that are invalid, unsupported, or exceed demo limits."""


@dataclass(frozen=True)
class PdfChunk:
    """A searchable text segment with enough metadata to cite its PDF page."""

    content: str
    source_name: str
    page_number: int
    chunk_index: int


def safe_filename(filename: str) -> str:
    """Keep only a short display name; never use an upload name as a path."""
    basename = re.split(r"[/\\]", filename)[-1]
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", basename).strip(" .")
    return (cleaned or "uploaded-document.pdf")[:255]


def chunk_page_text(
    text: str,
    *,
    source_name: str,
    page_number: int,
    first_chunk_index: int,
) -> list[PdfChunk]:
    """Split page text into overlapping word-bounded chunks.

    Overlap preserves phrases that cross chunk boundaries, while word bounds
    keep each request small enough for local embedding model context limits.
    """
    # Splitting exceptionally long runs also puts a hard character bound on a
    # chunk, even for malformed PDFs with a single multi-megabyte "word".
    words = list(re.finditer(r"\S{1,1000}", text))
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start
        while end < len(words) and end - start < CHUNK_WORDS:
            candidate_end = words[end].end()
            if end > start and candidate_end - words[start].start() > MAX_CHUNK_CHARACTERS:
                break
            end += 1
        content = text[words[start].start() : words[end - 1].end()].strip()
        chunks.append(
            PdfChunk(
                content=content,
                source_name=source_name,
                page_number=page_number,
                chunk_index=first_chunk_index + len(chunks),
            )
        )
        if end == len(words):
            break
        overlap = min(CHUNK_OVERLAP_WORDS, max(0, (end - start) // 5))
        start = end - overlap
    return chunks


def extract_pdf_chunks(data: bytes, filename: str) -> list[PdfChunk]:
    """Extract text from a bounded PDF and retain one-based page citations.

    This educational path does not run OCR. Rejecting encrypted, oversized, or
    image-only files explicitly is safer than silently indexing incomplete text.
    """
    if not data or len(data) > MAX_PDF_BYTES:
        raise PdfIngestionError("PDF must be non-empty and no larger than 20 MiB")
    if b"%PDF-" not in data[:1024]:
        raise PdfIngestionError("Uploaded file does not have a PDF header")

    source_name = safe_filename(filename)
    try:
        reader = PdfReader(BytesIO(data), strict=False)
    except PdfReadError as error:
        raise PdfIngestionError("Could not read the uploaded PDF") from error
    if reader.is_encrypted:
        raise PdfIngestionError("Encrypted PDFs are not supported")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise PdfIngestionError("PDF exceeds the 500-page demo limit")

    chunks: list[PdfChunk] = []
    extracted_characters = 0
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        extracted_characters += len(page_text)
        if extracted_characters > MAX_EXTRACTED_CHARACTERS:
            raise PdfIngestionError("PDF extracted text exceeds the demo limit")
        chunks.extend(
            chunk_page_text(
                page_text,
                source_name=source_name,
                page_number=page_number,
                first_chunk_index=len(chunks),
            )
        )

    if not chunks:
        raise PdfIngestionError("PDF contains no extractable text; OCR is not enabled")
    return chunks
