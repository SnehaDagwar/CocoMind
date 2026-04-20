"""Tests for the hash-chained audit store.

Verifies append-only property, chain integrity, and Merkle root computation.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC

import pytest

from src.audit import chain as audit_chain


@pytest.fixture(autouse=True)
def _temp_audit_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Use a temporary audit DB for each test."""
    db_path = str(tmp_path / "test_audit.db")
    monkeypatch.setattr(audit_chain, "_get_db_path", lambda: db_path)


class TestWriteAndRead:
    """Test basic write and read operations."""

    def test_write_creates_record(self) -> None:
        record_id = audit_chain.write_record("TEST_EVENT", {"key": "value"})
        assert record_id is not None
        assert len(record_id) == 32

    def test_records_accumulate(self) -> None:
        audit_chain.write_record("EVENT_1", {"n": 1})
        audit_chain.write_record("EVENT_2", {"n": 2})
        audit_chain.write_record("EVENT_3", {"n": 3})

        records = audit_chain.get_all_records()
        assert len(records) == 3

    def test_records_maintain_order(self) -> None:
        audit_chain.write_record("FIRST", {"n": 1})
        audit_chain.write_record("SECOND", {"n": 2})

        records = audit_chain.get_all_records()
        assert records[0]["event_type"] == "FIRST"
        assert records[1]["event_type"] == "SECOND"


class TestChainIntegrity:
    """Test hash chain verification."""

    def test_empty_chain_is_valid(self) -> None:
        assert audit_chain.verify_chain() is True

    def test_single_record_chain_is_valid(self) -> None:
        audit_chain.write_record("EVENT", {"data": "test"})
        assert audit_chain.verify_chain() is True

    def test_multi_record_chain_is_valid(self) -> None:
        for i in range(10):
            audit_chain.write_record(f"EVENT_{i}", {"n": i})
        assert audit_chain.verify_chain() is True

    def test_genesis_hash_is_correct(self) -> None:
        audit_chain.write_record("FIRST", {"data": "a"})
        records = audit_chain.get_all_records()
        assert records[0]["prev_hash"] == "0" * 64

    def test_chain_linkage(self) -> None:
        audit_chain.write_record("A", {"data": 1})
        audit_chain.write_record("B", {"data": 2})

        records = audit_chain.get_all_records()
        assert records[1]["prev_hash"] == records[0]["record_hash"]


class TestAppendOnly:
    """Test that UPDATE and DELETE are prevented."""

    def test_update_is_blocked(self) -> None:
        audit_chain.write_record("EVENT", {"data": "original"})

        # Direct SQL UPDATE should be blocked by trigger
        db_path = audit_chain._get_db_path()
        conn = sqlite3.connect(db_path)
        with pytest.raises(sqlite3.IntegrityError, match="UPDATE not allowed"):
            conn.execute(
                "UPDATE audit_records SET event_type = 'TAMPERED'"
            )
        conn.close()

    def test_delete_is_blocked(self) -> None:
        audit_chain.write_record("EVENT", {"data": "keep_me"})

        db_path = audit_chain._get_db_path()
        conn = sqlite3.connect(db_path)
        with pytest.raises(sqlite3.IntegrityError, match="DELETE not allowed"):
            conn.execute("DELETE FROM audit_records")
        conn.close()


class TestMerkleRoot:
    """Test Merkle root computation."""

    def test_empty_returns_zero_hash(self) -> None:
        root = audit_chain.compute_daily_root("2099-01-01")
        assert root == "0" * 64

    def test_single_record_root_equals_record_hash(self) -> None:
        audit_chain.write_record("EVENT", {"data": 1})
        records = audit_chain.get_all_records()

        # For single item, Merkle root = the item hash
        from datetime import datetime
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        root = audit_chain.compute_daily_root(today)
        assert root == records[0]["record_hash"]

    def test_multiple_records_root_is_deterministic(self) -> None:
        for i in range(5):
            audit_chain.write_record(f"EVENT_{i}", {"n": i})

        from datetime import datetime
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        root1 = audit_chain.compute_daily_root(today)
        root2 = audit_chain.compute_daily_root(today)
        assert root1 == root2


class TestRTIExport:
    """Test RTI export functionality."""

    def test_export_includes_chain_verification(self) -> None:
        audit_chain.write_record("VERDICT", {"bid_id": "BID-1", "criterion": "turnover"})
        export = audit_chain.export_for_rti("BID-1")

        assert export["bid_id"] == "BID-1"
        assert export["chain_verified"] is True
        assert len(export["records"]) == 1
