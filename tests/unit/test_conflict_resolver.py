"""Tests for the conflict resolver."""

from __future__ import annotations

from src.conflict.resolver import detect_conflict
from src.models.documents import DocType
from src.models.verdicts import ConflictStatus


class TestNoConflict:
    """Test cases where no conflict exists."""

    def test_single_value(self) -> None:
        result = detect_conflict([("chunk1", 60000000, DocType.CA_CERTIFICATE)])
        assert result.conflict_status == ConflictStatus.NONE

    def test_values_agree(self) -> None:
        result = detect_conflict([
            ("chunk1", 60000000, DocType.CA_CERTIFICATE),
            ("chunk2", 60500000, DocType.AUDITED_FINANCIAL_STATEMENT),
        ])
        # 0.5M / 60.5M ≈ 0.8% < 5%
        assert result.conflict_status == ConflictStatus.NONE


class TestAutoResolved:
    """Test cases where doc-type hierarchy resolves the conflict."""

    def test_ca_cert_wins_over_cover_letter(self) -> None:
        result = detect_conflict([
            ("chunk1", 60000000, DocType.CA_CERTIFICATE),
            ("chunk2", 45000000, DocType.COVER_LETTER),
        ])
        assert result.conflict_status == ConflictStatus.AUTO_RESOLVED
        assert result.winning_doc_type == DocType.CA_CERTIFICATE
        assert result.winning_chunk_id == "chunk1"

    def test_audited_fs_wins_over_self_declaration(self) -> None:
        result = detect_conflict([
            ("chunk1", 70000000, DocType.AUDITED_FINANCIAL_STATEMENT),
            ("chunk2", 50000000, DocType.SELF_DECLARATION),
        ])
        assert result.conflict_status == ConflictStatus.AUTO_RESOLVED
        assert result.winning_doc_type == DocType.AUDITED_FINANCIAL_STATEMENT


class TestUnresolvedConflict:
    """Test cases where conflict cannot be auto-resolved."""

    def test_two_ca_certs_disagree(self) -> None:
        """Same-rank docs disagree → routes to HITL."""
        result = detect_conflict([
            ("chunk1", 60000000, DocType.CA_CERTIFICATE),
            ("chunk2", 40000000, DocType.CA_CERTIFICATE),
        ])
        assert result.conflict_status == ConflictStatus.CONFLICT_UNRESOLVED
        # Conservative (lower) value wins
        assert result.winning_chunk_id == "chunk2"

    def test_same_rank_agree(self) -> None:
        """Same-rank docs with values within threshold → auto-resolved."""
        result = detect_conflict([
            ("chunk1", 60000000, DocType.CA_CERTIFICATE),
            ("chunk2", 61000000, DocType.CA_CERTIFICATE),
        ])
        # 1M/61M ≈ 1.6% < 5%
        assert result.conflict_status in (ConflictStatus.NONE, ConflictStatus.AUTO_RESOLVED)
