"""FastAPI routes for the CocoMind API.

Every route declares required_role via RBAC dependency.
"""

from __future__ import annotations

from fastapi import FastAPI, File, UploadFile

from src.audit.chain import export_for_rti, get_all_records, verify_chain
from src.models.auth import Role
from src.rbac.middleware import require_role

app = FastAPI(
    title="CocoMind — CRPF Tender Evaluation Platform",
    description="AI-assisted tender evaluation with formal verification",
    version="0.1.0",
)


@app.get("/api/health")
async def health_check() -> dict:
    return {"status": "healthy", "version": "0.1.0"}


@app.post(
    "/api/nit/upload",
    dependencies=[require_role(Role.PROCUREMENT_OFFICER)],
)
async def upload_nit(file: UploadFile = File(...)) -> dict:
    """Upload a NIT document for criterion extraction."""
    from src.ingestion.service import ingest_file

    content = await file.read()
    pages = ingest_file(content, file.filename or "uploaded_nit")

    return {
        "status": "ingested",
        "filename": file.filename,
        "pages": len(pages),
        "doc_hash": pages[0].doc_hash if pages else "",
        "doc_type": pages[0].doc_type.value if pages else "unknown",
    }


@app.post(
    "/api/bid/upload",
    dependencies=[require_role(Role.PROCUREMENT_OFFICER)],
)
async def upload_bid(
    bid_id: str,
    bid_name: str = "",
    file: UploadFile = File(...),
) -> dict:
    """Upload a bid document."""
    from src.ingestion.service import ingest_file

    content = await file.read()
    pages = ingest_file(content, file.filename or "uploaded_bid")

    return {
        "status": "ingested",
        "bid_id": bid_id,
        "bid_name": bid_name,
        "pages": len(pages),
        "doc_hash": pages[0].doc_hash if pages else "",
    }


@app.post(
    "/api/evaluate",
    dependencies=[require_role(Role.PROCUREMENT_OFFICER, Role.EVALUATOR)],
)
async def trigger_evaluation(
    nit_path: str,
    bid_paths: list[dict],
) -> dict:
    """Trigger full pipeline evaluation."""
    from src.pipeline.orchestrator import run_pipeline

    vtms = run_pipeline(nit_path, bid_paths)

    return {
        "status": "completed",
        "results": {
            bid_id: [row.model_dump(mode="json") for row in rows]
            for bid_id, rows in vtms.items()
        },
    }


@app.get(
    "/api/audit/verify",
    dependencies=[require_role(Role.AUDITOR)],
)
async def verify_audit_chain() -> dict:
    """Verify the integrity of the audit chain."""
    is_valid = verify_chain()
    return {
        "chain_valid": is_valid,
        "status": "INTACT" if is_valid else "TAMPERED",
    }


@app.get(
    "/api/audit/records",
    dependencies=[require_role(Role.AUDITOR)],
)
async def list_audit_records() -> dict:
    """List all audit records."""
    records = get_all_records()
    return {"count": len(records), "records": records}


@app.get(
    "/api/rti/export/{bid_id}",
    dependencies=[require_role(Role.AUDITOR)],
)
async def rti_export(bid_id: str) -> dict:
    """Export audit trail for a specific bid (RTI response)."""
    return export_for_rti(bid_id)
