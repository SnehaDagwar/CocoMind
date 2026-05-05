# Your complete execution plan — CRPF Tender

## Eval Hackathon

Master timeline (14 days)
Days Phase What you're building
1–2 Research GFR 2017, real NITs, synonym dictionary
2–3 Environment APIs working, DB scaffold, Pydantic models
3–7 Core build OCR pipeline + rule engine + audit log
7–10 Intelligence LLM extraction, RAG, conflict detection
10–12 UI + HITL Streamlit dashboard + RTI export
13–14 Demo prep Synthetic dataset + 3 rehearsals
Critical path checkpoints — nothing else matters if these slip:
- C1 (Day 3): Azure OCR returns bounding boxes from a PDF
- C2 (Day 5): LLM extracts a normalised INR value from hardcoded text
- C3 (Day 7): Rule engine evaluates one criterion end-to-end → verdict + expression
- C4 (Day 10): Full VTM generated for one complete synthetic bid
- C5 (Day 13): Full demo runs clean in under 5 minutes, no errors

## Phase 01 — Research (Day 1–2, ~10 hrs)

## Task A — Read GFR
2017. Download from doe.gov.in. Read Chapter 6, Chapter 7, Annexure III.
This tells you the standard structure of every Indian government NIT — essential for writing good
extraction prompts. Budget 2 hours.

## Task B — Download 5 real NITs. Go to eprocure.gov.in or gem.gov.in. Search "CRPF" or "MHA".
Download 5 complete NIT PDFs (vehicles, IT equipment, uniforms, services, construction).
Manually highlight and annotate Section 3 (Eligibility Criteria) in each one — criterion name,
mandatory/optional, threshold value. These are your few-shot examples.

## Task C — Read RTI Act Sections 6–7. At rtionline.gov.in. Understand what a rejected bidder can
legally demand, and what the PIO must provide within 30 days. Also read CVC Circular No.
03/01/12 on e-procurement. Your VTM design must satisfy these requirements exactly.

## Task D — Build synonym_map.json. Collect every different phrasing of each criterion type
from your NITs. "Annual Turnover" / "Gross Revenue" / "Annual Sales" / "Net Receipts" / "वार्षिक
कारोबार". At minimum 6–8 variants per criterion type, ~50 entries total. This is a static expert
dictionary — not AI — and it's worth its weight in accuracy.

Your complete execution plan — CRPF Tender

## Eval Hackathon

## Task E — Design your 3 demo bids. Plan before you build. Bid A: clear PASS — all criteria met,
clean typed PDFs. Bid B: clear FAIL — one mandatory criterion (years in operation) fails cleanly.
Bid C: HITL trigger — one photographed handwritten CA certificate with ambiguous turnover +
one conflicting turnover figure across two documents. Write the ground truth table (bids ×
criteria × expected verdict) before creating any documents.

## Resources:
- eprocure.gov.in — real NITs
- gem.gov.in — GeM tender portal
- doe.gov.in — GFR 2017 PDF
- rtionline.gov.in — RTI Act and guidelines
- cvc.gov.in/circulars — CVC procurement circulars
- mca.gov.in — Company registration for cross-verification

## Phase 02 — Environment (Day 2–3, ~6 hrs)

## Task A — Repo + dependencies. Create project with /ingestion, /ocr, /extraction, /engine,
/audit, /api, /ui, /tests, /data/synthetic folders.
pip install fastapi uvicorn celery redis pydantic python-dotenv
pip install pymupdf python-docx pillow pdf2image
pip install anthropic azure-ai-formrecognizer chromadb
pip install sqlalchemy psycopg2-binary reportlab sentence-transformers

## Task B — Validate Azure Document Intelligence first. Sign up at portal.azure.com, create a
"Document Intelligence" resource (free tier: 500 pages/month). Write test_ocr.py that sends a
sample PDF page and prints every word with its bounding box. Do not proceed to Phase 3 until
you see bounding box coordinates in your terminal. This is the hardest external dependency.

## Task C — Validate Anthropic API structured output. Get key at console.anthropic.com. Write
test_llm.py — send the hardcoded string "Annual Turnover of M/s ABC Ltd is Rs. Six Crores" and
ask Claude to return {"normalised_value": 60000000, "unit": "INR", "confidence": 0.99}. Confirm
the JSON structure before building around it.

## Task D — PostgreSQL + ChromaDB. Docker for Postgres locally. Create tables: documents,
criteria, extracted_values, verdicts, audit_records. ChromaDB runs in-process — use
PersistentClient pointing to a local directory. Confirm a test embedding stores to disk and is
retrievable by semantic query.

## Task E — Pydantic models before business logic. Define your data contracts in models.py
before writing any pipeline code. You need: Criterion, OCRChunk, ExtractionResult,

Your complete execution plan — CRPF Tender

## Eval Hackathon

VerdictRecord, AuditRecord, HITLItem. This forces you to think through data flow and prevents
type mismatches when connecting layers.

## Phase 03 — Core Build (Day 3–7, ~20 hrs) — HIGHEST RISK

## Task A — ingestion.py. Accept PDF/JPEG/PNG/DOCX. Convert to list of DocumentPage objects
(page_num, PIL image, source_path, doc_type). Doc type detection: keyword heuristics —
"NOTICE INVITING TENDER" → NIT, "CERTIFICATE" → certificate, default → bid_submission.

## Task B — ocr_service.py. Send each page to Azure. Parse AnalyzeResult.pages[].words for text
+ bounding box. Compute page-level average confidence. If average < 0.72 → set
route_to_google = True or HITL flag. Return OCRPage with words + bboxes + confidence +
handwriting flag.

## Task C — chunker.py. Group OCR words into semantic chunks by spatial proximity (words in
the same region = same chunk). Each chunk stores: text, page_num, bbox, source_doc_id,
avg_confidence. Embed with sentence-transformers all-MiniLM-L6-v2 (free, local, no API cost).
Upsert to ChromaDB with metadata. Must be queryable by doc_id filter + semantic similarity.

## Task D — rule_engine.py — your most important file. Zero LLM involvement. Input: Criterion +
normalised float. Output: verdict + expression string. Handle all operators (gte/lte/eq/between).
Null input → AMBIGUOUS. Low confidence (< 0.70) → AMBIGUOUS. Write test_rule_engine.py
with 20+ test cases. This file must have no bugs — it's your legal defensibility core.

## Task E — audit_log.py — append-only, SHA-256 chained. No UPDATE or DELETE ever. Each
record hashes: full trace JSON + previous record's hash. Build write_record(), verify_chain() (re-
computes all hashes), export_for_rti(bid_id). Tampering any record must break the chain — test
this explicitly.

## Phase 04 — Intelligence Layer (Day 7–10, ~16 hrs)

## Task A — criterion_extractor.py. Use Claude with tool use (structured JSON output mode).
System prompt includes 3 few-shot examples from your annotated NITs. Output schema
matches Criterion model exactly. The two fields most teams miss: mandatory (bool) and
threshold_operator (gte/lte/eq/between/contains). Include examples of both mandatory and
optional criteria in your few-shots.

## Task B — rag_retriever.py. For each criterion: construct query = criterion name + top-3
synonyms from synonym_map.json. Query ChromaDB with where={"doc_id": bid_id} filter.
Return top-3 chunks with similarity scores. If top score < 0.35 → flag as NOT_FOUND. Store
similarity scores for conflict detection.

## Task C — value_extractor.py. This is where most of your prompt engineering effort goes. Must
handle: lakh/crore notation, written numbers ("Six Crores"), Hindi numerals, percentage values,
year counts, boolean values. At minimum 5 few-shot examples per data_type (currency_INR,
percentage, years, boolean). Return ExtractionResult with raw_text, normalised_value,
confidence, source_chunk_id.

Your complete execution plan — CRPF Tender

## Eval Hackathon

## Task D — conflict_detector.py. If top-3 chunks have two different normalised values
(difference > 5%), apply preference hierarchy: CA_certificate > audited_financial_statement >
ITR > cover_letter > self_declaration. Detect document type from chunk metadata. If hierarchy
resolves it → AUTO_RESOLVED with reason. If not → CONFLICT_UNRESOLVED → HITL queue.
Conservative default: use lower value if unresolved.

## Task E — pipeline.py — the orchestrator (Critical Path C3). Calls all services in sequence.
Input: nit_path + bid_path. Output: list of VerdictRecord. Run on Bid A first — all verdicts must
match your ground truth before touching the UI.

## Phase 05 — UI & HITL (Day 10–12, ~12 hrs)
Use Streamlit — not React. You can ship a clean, impressive dashboard in 3–4 hours. The jury
cares about information, not framework choice.

## Task A — Verdict dashboard (dashboard.py). Bid selector (st.selectbox), per-bid criterion table
with coloured verdict badges (st.dataframe with styling), expandable rows showing the full
trace: source doc → page → OCR text → extracted value → rule expression → verdict (st.expander).

## Task B — HITL review page (hitl_review.py). This is your demo star moment. Left side: render
the flagged PDF page as an image with the ambiguous bounding box highlighted in amber (use
pdf2image + PIL ImageDraw.rectangle()). Right side: the OCR'd text, the criterion + rule, radio
buttons (Confirm/Override/Not Provided) + justification text field. On submit: write to audit log
with officer_id + timestamp.

## Task C — RTI export (rti_export.py). Use ReportLab to generate a formatted PDF. Must include:
tender reference, bid name, evaluation date, officer name, each criterion as a section with its
full trace, overall ELIGIBLE/INELIGIBLE determination. Also export JSON. Add
st.download_button to dashboard.
If short on time: Skip the FastAPI REST layer — Streamlit can call pipeline.py directly. The demo
needs the UI working.

## Phase 06 — Demo Prep (Day 13–14, ~8 hrs)

## Task A — Build the 3 synthetic bid packages. Use Canva or Google Docs to create realistic-
looking CA certificates, company registration certs, GST certs. For Bid C, literally photograph a
handwritten certificate with your phone at a slight angle — this makes the OCR challenge
tangible and real to the jury. Use fictional companies: M/s Sharma Industrial Pvt Ltd, M/s Verma

## Tech Solutions, M/s Gupta Equipment Co.

## Task B — Rehearse the 4-minute demo script 3 times minimum:
- Upload photographed certificate → OCR bboxes appear [45s]
- Show NIT criterion tree [30s]
- Run evaluation → verdict table populates [60s]

Your complete execution plan — CRPF Tender

## Eval Hackathon

- Click FAIL verdict → read the audit trace aloud [45s]
- Trigger HITL for Bid C → make human decision [45s]
- Download RTI export PDF → show full trace inside [30s]

## Task C — Prepare for hard questions:
- "What if LLM hallucinates?" → LLM only normalises text to numbers. Python evaluates
the rule. Show the 5-line rule engine code.
- "Data security?" → Documents stay in your infrastructure. LLM only sees extracted text
snippets, not raw documents for verdict decisions.
- "Scale to 500 bids?" → Celery task queue. Each bid is an independent async task.
- "Accuracy?" → OCR confidence is logged per word. LLM confidence is logged per
extraction. Ambiguous cases go to HITL — the system never silently fails.
The single most important rule for Day 13: do not add features. Fix bugs, rehearse, polish. A
system that demos one thing perfectly beats a feature-rich system that crashes mid-demo.

Want me to write out the actual code for any specific file — rule_engine.py, the LLM extraction
prompt with few-shots, audit_log.py with the hash chain, or the Streamlit dashboard? I can go
deep on any of these right now.

