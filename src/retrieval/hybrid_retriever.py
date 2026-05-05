"""Hybrid retriever with Reciprocal Rank Fusion (RRF).

Dense (ChromaDB BGE-M3) + Sparse (Whoosh BM25) → RRF fusion → top-K results.
Score floor of 0.35 → NOT_FOUND → AMBIGUOUS (never INELIGIBLE).
"""

from __future__ import annotations

import json
from pathlib import Path

from src.config.settings import get_settings
from src.retrieval.bm25_index import search_bm25
from src.retrieval.embedder import query_chunks


def _load_synonym_map() -> dict[str, list[str]]:
    """Load the static synonym dictionary."""
    path = Path("src/config/synonym_map.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _expand_query(criterion_name: str, synonym_map: dict[str, list[str]]) -> str:
    """Expand a criterion name with top-3 synonyms."""
    for _key, synonyms in synonym_map.items():
        for syn in synonyms:
            if syn.lower() == criterion_name.lower():
                top_3 = synonyms[:3]
                return f"{criterion_name} {' '.join(top_3)}"
    return criterion_name


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    k: int = 60,
) -> list[dict]:
    """Combine multiple ranked result lists using RRF.

    RRF score = sum(1 / (k + rank)) across all lists.
    Single hyperparameter k, published robust default of 60.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list):
            chunk_id = item["chunk_id"]
            rrf_score = 1.0 / (k + rank + 1)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_score
            items[chunk_id] = item

    # Sort by RRF score descending
    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    results = []
    for chunk_id in sorted_ids:
        item = items[chunk_id].copy()
        item["rrf_score"] = scores[chunk_id]
        results.append(item)

    return results


def hybrid_retrieve(
    criterion_name: str,
    bid_id: str,
    top_k: int = 3,
    dense_top_k: int = 10,
    sparse_top_k: int = 10,
) -> list[dict]:
    """Hybrid retrieval: dense + sparse + RRF fusion.

    For each criterion × bid:
    1. Expand query with synonyms.
    2. Dense top-K from ChromaDB.
    3. Sparse top-K from Whoosh BM25.
    4. RRF fusion.
    5. Return top-K fused results.

    If top RRF score < 0.35 → results marked as NOT_FOUND.
    """
    settings = get_settings()
    synonym_map = _load_synonym_map()
    expanded_query = _expand_query(criterion_name, synonym_map)

    # Parallel retrieval (sequential in Tier-1)
    dense_results = query_chunks(expanded_query, bid_id, top_k=dense_top_k)
    sparse_results = search_bm25(expanded_query, bid_id, top_k=sparse_top_k)

    # RRF fusion
    fused = reciprocal_rank_fusion([dense_results, sparse_results])

    # Take top-K
    top_results = fused[:top_k]

    # Check score floor
    for result in top_results:
        if result.get("rrf_score", 0) < settings.retrieval_score_floor:
            result["not_found"] = True

    return top_results
