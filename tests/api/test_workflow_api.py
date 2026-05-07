from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from src.api.routes import app


client = TestClient(app)

PO_HEADERS = {
    "X-User-ID": "demo-po",
    "X-User-Name": "Procurement Officer",
    "X-User-Role": "ProcurementOfficer",
}
HITL_HEADERS = {
    "X-User-ID": "demo-hitl",
    "X-User-Name": "HITL Reviewer",
    "X-User-Role": "HITLReviewer",
}
AUDITOR_HEADERS = {
    "X-User-ID": "demo-auditor",
    "X-User-Name": "Auditor",
    "X-User-Role": "Auditor",
}


def test_procurement_officer_can_complete_fixture_backed_workflow() -> None:
    tender_id = _create_tender()

    upload = client.post(
        f"/api/tenders/{tender_id}/nit",
        files={"file": ("nit.pdf", b"synthetic nit", "application/pdf")},
        headers=PO_HEADERS,
    )
    assert upload.status_code == 200
    assert upload.json()["document"]["doc_hash"]

    criteria = client.post(f"/api/tenders/{tender_id}/criteria/extract", headers=PO_HEADERS)
    assert criteria.status_code == 200
    assert len(criteria.json()["criteria"]) == 6

    for bid_id, bid_name in [
        ("BID-A", "M/s Sharma Industrial Pvt Ltd"),
        ("BID-B", "M/s Verma Tech Solutions"),
        ("BID-C", "M/s Gupta Equipment Co"),
    ]:
        response = client.post(
            f"/api/tenders/{tender_id}/bids",
            json={"bid_id": bid_id, "bid_name": bid_name},
            headers=PO_HEADERS,
        )
        assert response.status_code == 200

    job = client.post(f"/api/tenders/{tender_id}/evaluation-jobs", headers=PO_HEADERS)
    assert job.status_code == 200
    job_id = job.json()["job"]["job_id"]
    assert client.get(f"/api/jobs/{job_id}", headers=PO_HEADERS).json()["job"]["status"] == "COMPLETED"

    vtm = client.get(f"/api/tenders/{tender_id}/vtm", headers=PO_HEADERS)
    assert vtm.status_code == 200
    summary = vtm.json()["summary"]
    assert summary["BID-A"]["overall"] == "ELIGIBLE"
    assert summary["BID-B"]["overall"] == "INELIGIBLE"
    assert summary["BID-C"]["overall"] == "PENDING HITL"

    hitl = client.get(f"/api/tenders/{tender_id}/hitl", headers=HITL_HEADERS)
    assert hitl.status_code == 200
    items = hitl.json()["items"]
    assert len(items) == 2

    blocked_report = client.post(f"/api/tenders/{tender_id}/reports", headers=PO_HEADERS)
    assert blocked_report.status_code == 409

    for item in items:
        decision = client.post(
            f"/api/hitl/{item['item_id']}/decision",
            json={"decision": "CONFIRM", "justification": "Demo reviewer confirmed the evidence."},
            headers=HITL_HEADERS,
        )
        assert decision.status_code == 200

    report = client.post(f"/api/tenders/{tender_id}/reports", headers=PO_HEADERS)
    assert report.status_code == 200
    assert report.json()["report"]["chain_verified"] is True

    audit = client.get("/api/audit/verify", headers=AUDITOR_HEADERS)
    assert audit.status_code == 200
    assert audit.json()["status"] == "INTACT"


def test_hitl_reviewer_cannot_create_tender() -> None:
    response = client.post(
        "/api/tenders",
        json={
            "name": "Forbidden Tender",
            "reference_number": f"REF-{uuid.uuid4().hex[:6]}",
        },
        headers=HITL_HEADERS,
    )
    assert response.status_code == 403


def _create_tender() -> str:
    response = client.post(
        "/api/tenders",
        json={
            "name": "API Workflow Test Tender",
            "department": "CRPF Procurement",
            "procurement_circle": "PHQ New Delhi",
            "reference_number": f"REF-{uuid.uuid4().hex[:8]}",
            "opening_date": "2026-05-10",
        },
        headers=PO_HEADERS,
    )
    assert response.status_code == 200
    return response.json()["tender"]["tender_id"]
