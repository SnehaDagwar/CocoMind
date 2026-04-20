"""Append-only, hash-chained audit store.

SQLite with WAL mode. Every record hashes: payload_json || prev_hash.
No UPDATE or DELETE ever. verify_chain() re-derives from genesis.
Daily Merkle root anchored to TEC email.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.config.settings import get_settings


def _get_db_path() -> str:
    settings = get_settings()
    path = Path(settings.audit_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode enabled."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """Create the audit_records table if it doesn't exist.

    Also creates triggers to prevent UPDATE and DELETE.
    """
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS audit_records (
                record_id    TEXT PRIMARY KEY,
                ts_utc       TEXT NOT NULL,
                event_type   TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                prev_hash    TEXT NOT NULL,
                record_hash  TEXT NOT NULL,
                signature    BLOB
            );

            -- Prevent UPDATE
            CREATE TRIGGER IF NOT EXISTS prevent_update
            BEFORE UPDATE ON audit_records
            BEGIN
                SELECT RAISE(ABORT, 'UPDATE not allowed on audit_records');
            END;

            -- Prevent DELETE
            CREATE TRIGGER IF NOT EXISTS prevent_delete
            BEFORE DELETE ON audit_records
            BEGIN
                SELECT RAISE(ABORT, 'DELETE not allowed on audit_records');
            END;
        """)
        conn.commit()
    finally:
        conn.close()


def _compute_hash(payload_json: str, prev_hash: str) -> str:
    """SHA-256(payload_json || prev_hash)."""
    data = (payload_json + prev_hash).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _get_last_hash() -> str:
    """Get the hash of the last record in the chain (or genesis hash)."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT record_hash FROM audit_records ORDER BY rowid DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else "0" * 64  # Genesis hash
    finally:
        conn.close()


def write_record(
    event_type: str,
    payload: dict,
    signature: bytes | None = None,
) -> str:
    """Append a new record to the audit chain.

    Returns the record_id.
    """
    init_db()

    record_id = uuid.uuid4().hex
    ts_utc = datetime.now(UTC).isoformat()
    payload_json = json.dumps(payload, sort_keys=True, default=str)
    prev_hash = _get_last_hash()
    record_hash = _compute_hash(payload_json, prev_hash)

    conn = _get_connection()
    try:
        conn.execute(
            """INSERT INTO audit_records
               (record_id, ts_utc, event_type, payload_json, prev_hash, record_hash, signature)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (record_id, ts_utc, event_type, payload_json, prev_hash, record_hash, signature),
        )
        conn.commit()
    finally:
        conn.close()

    return record_id


def verify_chain() -> bool:
    """Re-derive every hash from genesis and verify the chain is intact.

    Returns True if the chain is valid, False if any record was tampered with.
    """
    init_db()

    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT record_id, payload_json, prev_hash, record_hash "
            "FROM audit_records ORDER BY rowid ASC"
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return True  # Empty chain is valid

    expected_prev_hash = "0" * 64  # Genesis

    for _record_id, payload_json, prev_hash, record_hash in rows:
        # Check prev_hash linkage
        if prev_hash != expected_prev_hash:
            return False

        # Recompute and check record_hash
        recomputed = _compute_hash(payload_json, prev_hash)
        if recomputed != record_hash:
            return False

        expected_prev_hash = record_hash

    return True


def compute_daily_root(target_date: str | None = None) -> str:
    """Compute a Merkle root from all records for a given date.

    Args:
        target_date: ISO date string (YYYY-MM-DD). Defaults to today.

    Returns:
        Merkle root hash.
    """
    init_db()

    if target_date is None:
        target_date = datetime.now(UTC).strftime("%Y-%m-%d")

    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT record_hash FROM audit_records WHERE ts_utc LIKE ? ORDER BY rowid ASC",
            (f"{target_date}%",),
        )
        hashes = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    if not hashes:
        return "0" * 64

    return _merkle_root(hashes)


def _merkle_root(hashes: list[str]) -> str:
    """Compute a binary Merkle tree root from a list of hashes."""
    if len(hashes) == 1:
        return hashes[0]

    # Pad to even count
    if len(hashes) % 2 != 0:
        hashes.append(hashes[-1])

    parent_hashes = []
    for i in range(0, len(hashes), 2):
        combined = (hashes[i] + hashes[i + 1]).encode("utf-8")
        parent_hashes.append(hashlib.sha256(combined).hexdigest())

    return _merkle_root(parent_hashes)


def get_all_records() -> list[dict]:
    """Get all audit records for inspection/export."""
    init_db()

    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT record_id, ts_utc, event_type, payload_json, prev_hash, record_hash "
            "FROM audit_records ORDER BY rowid ASC"
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "record_id": r[0],
            "ts_utc": r[1],
            "event_type": r[2],
            "payload": json.loads(r[3]),
            "prev_hash": r[4],
            "record_hash": r[5],
        }
        for r in rows
    ]


def export_for_rti(bid_id: str) -> dict:
    """Export all audit records for a specific bid for RTI response.

    Returns a JSON-serialisable dict with the complete audit trail.
    """
    all_records = get_all_records()
    bid_records = [
        r for r in all_records
        if r["payload"].get("bid_id") == bid_id
    ]

    return {
        "bid_id": bid_id,
        "export_timestamp": datetime.now(UTC).isoformat(),
        "chain_verified": verify_chain(),
        "records": bid_records,
        "daily_root": compute_daily_root(),
    }
