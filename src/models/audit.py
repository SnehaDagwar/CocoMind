"""Audit record and signature models for the hash-chained audit store."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    """A single append-only, hash-chained audit record.

    Matches the SQLite schema in IMPLEMENTATION_PLAN §3.11.
    """

    record_id: str
    ts_utc: datetime
    event_type: str = Field(
        description=(
            "e.g. 'VERDICT_COMPUTED', 'HITL_DECISION', 'RTI_EXPORT', "
            "'PIPELINE_START', 'PIPELINE_COMPLETE'"
        )
    )
    payload_json: str
    prev_hash: str
    record_hash: str = Field(
        description="sha256(payload_json || prev_hash)"
    )
    signature: bytes | None = None


class Signature(BaseModel):
    """A cryptographic signature on a record or export."""

    signer_id: str
    signer_name: str = ""
    signature_bytes: bytes = b""
    certificate_thumbprint: str = ""
    timestamp_utc: datetime | None = None
    tsa_response: bytes | None = None
    method: str = Field(
        default="dev_self_signed",
        description="'dsc_pkcs11' | 'aadhaar_esign' | 'dev_self_signed'"
    )
