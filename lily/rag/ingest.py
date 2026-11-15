"""Indexes files into the store."""
from lily.rag import loader
from lily.rag.chunker import chunk


def ingest(store, path):
    """Index a file or folder. Returns (files indexed, chunks stored)."""
    files = chunks = 0
    for file in loader.find_files(path):
        text = loader.read(file)
        pieces = chunk(text) if text else []
        if pieces:
            store.replace(str(file.resolve()), pieces)
            files += 1
            chunks += len(pieces)
    return files, chunks
