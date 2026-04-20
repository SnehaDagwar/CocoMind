"""Whoosh BM25 sparse index for lexical retrieval.

Government docs have strong lexical patterns (Section 3.2(a), clause IDs)
where BM25 crushes dense retrieval. Combined with dense via RRF.
"""

from __future__ import annotations

from pathlib import Path

from whoosh import index as whoosh_index
from whoosh.fields import ID, NUMERIC, TEXT, Schema
from whoosh.qparser import MultifieldParser

from src.config.settings import get_settings
from src.models.documents import OCRChunk

_SCHEMA = Schema(
    chunk_id=ID(stored=True, unique=True),
    text=TEXT(stored=True),
    bid_id=ID(stored=True),
    doc_id=ID(stored=True),
    doc_type=ID(stored=True),
    page_num=NUMERIC(stored=True),
)


def _get_index_dir() -> Path:
    settings = get_settings()
    path = Path(settings.whoosh_index_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_or_create_index() -> whoosh_index.Index:
    """Get or create the Whoosh BM25 index."""
    idx_dir = _get_index_dir()
    if whoosh_index.exists_in(str(idx_dir)):
        return whoosh_index.open_dir(str(idx_dir))
    return whoosh_index.create_in(str(idx_dir), _SCHEMA)


def index_chunks(chunks: list[OCRChunk], bid_id: str) -> None:
    """Add chunks to the BM25 index."""
    ix = get_or_create_index()
    writer = ix.writer()

    for chunk in chunks:
        writer.update_document(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            bid_id=bid_id,
            doc_id=chunk.source_doc_id,
            doc_type=chunk.source_doc_type.value,
            page_num=chunk.page_num,
        )

    writer.commit()


def search_bm25(
    query_text: str,
    bid_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Search the BM25 index for a query scoped to a specific bid.

    Returns list of dicts with keys: chunk_id, text, score, metadata.
    """
    ix = get_or_create_index()

    with ix.searcher() as searcher:
        parser = MultifieldParser(["text"], schema=ix.schema)
        query = parser.parse(query_text)

        # Filter by bid_id
        from whoosh.query import Term
        bid_filter = Term("bid_id", bid_id)

        results = searcher.search(query, filter=bid_filter, limit=top_k)

        output = []
        for hit in results:
            output.append({
                "chunk_id": hit["chunk_id"],
                "text": hit["text"],
                "score": hit.score,
                "metadata": {
                    "bid_id": hit.get("bid_id", ""),
                    "doc_id": hit.get("doc_id", ""),
                    "doc_type": hit.get("doc_type", ""),
                    "page_num": hit.get("page_num", 0),
                },
            })

        return output
