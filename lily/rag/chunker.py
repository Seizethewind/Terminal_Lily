"""Cuts text into passages small enough to hand to the model."""
import re


def _pieces(text, size):
    """Paragraphs, with any paragraph longer than `size` cut at a space."""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        while len(para) > size:
            cut = para.rfind(" ", 0, size)
            cut = cut if cut > size // 2 else size
            yield para[:cut].strip()
            para = para[cut:].strip()
        if para:
            yield para


def chunk(text, size=800):
    """Group paragraphs into chunks of at most `size` characters."""
    chunks, current = [], ""
    for piece in _pieces(text, size):
        if current and len(current) + len(piece) + 2 > size:
            chunks.append(current)
            current = piece
        else:
            current = f"{current}\n\n{piece}" if current else piece
    if current:
        chunks.append(current)
    return chunks
