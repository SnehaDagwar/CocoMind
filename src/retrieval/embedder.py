"""BGE-M3 embedder + ChromaDB vector store.

Embeds OCR chunks using BAAI/bge-m3 (multilingual, 1024-dim).
Stores in ChromaDB PersistentClient with per-bid namespace via metadata filter.
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config.settings import get_settings
from src.models.documents import OCRChunk

# Lazy-loaded model
_model = None
_chroma_client: chromadb.PersistentClient | None = None


def _get_model():  # type: ignore[no-untyped-def]
    """Lazy-load BGE-M3 embedding model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("BAAI/bge-m3")
    return _model


def _get_chroma_client() -> chromadb.PersistentClient:
    """Lazy-init ChromaDB PersistentClient."""
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        path = Path(settings.chromadb_path)
        path.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=str(path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_collection(collection_name: str = "cocomind_chunks") -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using BGE-M3."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def upsert_chunks(
    chunks: list[OCRChunk],
    bid_id: str,
    collection_name: str = "cocomind_chunks",
) -> None:
    """Embed and upsert chunks into ChromaDB with bid-level metadata."""
    if not chunks:
        return

    collection = get_collection(collection_name)
    texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(texts)

    collection.upsert(
        ids=[chunk.chunk_id for chunk in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {
                "bid_id": bid_id,
                "doc_id": chunk.source_doc_id,
                "doc_type": chunk.source_doc_type.value,
                "page_num": chunk.page_num,
                "avg_confidence": chunk.avg_confidence,
                "bbox_x_min": chunk.bbox.x_min,
                "bbox_y_min": chunk.bbox.y_min,
                "bbox_x_max": chunk.bbox.x_max,
                "bbox_y_max": chunk.bbox.y_max,
            }
            for chunk in chunks
        ],
    )


def query_chunks(
    query_text: str,
    bid_id: str,
    top_k: int = 10,
    collection_name: str = "cocomind_chunks",
) -> list[dict]:
    """Query ChromaDB for similar chunks scoped to a specific bid.

    Returns list of dicts with keys: chunk_id, text, score, metadata.
    """
    collection = get_collection(collection_name)
    query_embedding = embed_texts([query_text])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"bid_id": bid_id},
    )

    output = []
    if results and results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            output.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i] if results["documents"] else "",
                "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0.0),
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })

    return output
