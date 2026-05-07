"""Workflow models for the integrated MVP tender flow."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(StrEnum):
    DRAFT = "DRAFT"
    TENDER_UPLOADED = "TENDER_UPLOADED"
    CRITERIA_EXTRACTED = "CRITERIA_EXTRACTED"
    BIDS_UPLOADED = "BIDS_UPLOADED"
    EVALUATING = "EVALUATING"
    HITL_PENDING = "HITL_PENDING"
    REPORT_READY = "REPORT_READY"


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    INGESTING_NIT = "INGESTING_NIT"
    EXTRACTING_CRITERIA = "EXTRACTING_CRITERIA"
    INGESTING_BIDS = "INGESTING_BIDS"
    PARSING_DOCUMENTS = "PARSING_DOCUMENTS"
    EVALUATING = "EVALUATING"
    ROUTING_HITL = "ROUTING_HITL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TenderCreate(BaseModel):
    name: str = Field(min_length=1)
    department: str = Field(default="CRPF Procurement")
    procurement_circle: str = Field(default="PHQ New Delhi")
    reference_number: str = Field(min_length=1)
    opening_date: str = ""


class Tender(TenderCreate):
    tender_id: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: str = ""
    created_at: datetime
    updated_at: datetime
    nit_document_id: str | None = None
    latest_job_id: str | None = None
    report_id: str | None = None


class UploadedDocument(BaseModel):
    document_id: str
    tender_id: str
    bid_id: str | None = None
    filename: str
    path: str
    size_bytes: int
    doc_hash: str
    doc_type: str = "unknown"
    uploaded_at: datetime


class BidderCreate(BaseModel):
    bid_id: str = Field(min_length=1)
    bid_name: str = Field(min_length=1)


class Bidder(BidderCreate):
    tender_id: str
    created_at: datetime
    documents: list[UploadedDocument] = []


class EvaluationJob(BaseModel):
    job_id: str
    tender_id: str
    status: JobStatus = JobStatus.QUEUED
    progress: int = Field(default=0, ge=0, le=100)
    message: str = ""
    demo_backed: bool = True
    error: str = ""
    created_at: datetime
    updated_at: datetime


class Report(BaseModel):
    report_id: str
    tender_id: str
    generated_at: datetime
    chain_verified: bool
    summary: dict[str, Any]
    export: dict[str, Any]
