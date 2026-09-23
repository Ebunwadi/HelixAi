import re

from helix_api.rag.types import TextChunk


def normalize_text(text: str) -> str:
    """Collapse noisy whitespace while preserving paragraph boundaries."""

    paragraphs = [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]
    return "\n\n".join(paragraphs)


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[TextChunk]:
    """Split text into overlapping character windows without cutting most words.

    This is intentionally a simple baseline chunker. Sprint 5 can compare smarter
    token-, sentence-, or structure-aware strategies against retrieval quality.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    normalized = normalize_text(text)
    if not normalized:
        return []

    chunks: list[TextChunk] = []
    start = 0

    while start < len(normalized):
        target_end = min(start + chunk_size, len(normalized))
        end = target_end

        # When possible, finish at a whitespace boundary rather than splitting a word.
        if target_end < len(normalized):
            minimum_break = start + int(chunk_size * 0.7)
            candidate = normalized.rfind(" ", minimum_break, target_end)
            if candidate > start:
                end = candidate

        piece = normalized[start:end].strip()
        if piece:
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    text=piece,
                    start=start,
                    end=end,
                )
            )

        if end >= len(normalized):
            break

        # Repeating a small tail gives neighbouring chunks shared context.
        start = max(end - overlap, start + 1)

    return chunks
