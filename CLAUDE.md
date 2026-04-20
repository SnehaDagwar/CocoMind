# CocoMind — CRPF Tender Evaluation Platform

**One-liner:** An AI-assisted platform that reads a CRPF tender (NIT) + bidder submissions, and produces criterion-by-criterion, source-pinned, RTI-auditable eligibility verdicts — with a hard human-in-the-loop path for ambiguous cases and a legally-signed audit trail.

**Hackathon track:** *AI-Based Tender Evaluation and Eligibility Analysis for Government Procurement by CRPF.*
**Current stage:** Round 1 — written solution. Round 2 ships a **Tier-1 demo** (14-day sandbox build). Tier-2 pilot + Tier-3 production plans live in [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## The problem (short form)

CRPF issues tenders (NITs) whose eligibility criteria — turnover, similar-works experience, certifications, affidavits, EMD, GST/PAN/EPFO status, no-near-relations declaration, no-blacklisting declaration — are buried across hundreds of pages of formal legal text. Bidders reply with heterogeneous evidence: typed PDFs, scanned CA certificates, phone-photographed state-government certificates, DOCX/XLS, multi-language (Hindi/Marathi/English). Manual evaluation is slow, inconsistent, and hard to defend under **RTI Act 2005 / CVC Circular 03/01/12 / CAG audit / GFR 2017 / DPDPA 2023 / IT Act §43A**.

Full problem statement: [`docs/Theme.md`](docs/Theme.md).

## Hard non-negotiables

**Correctness & explainability**
1. **Criterion-level explainability.** Every verdict names: *which criterion, which document, which page, which bounding box, which extracted value, which rule, which threshold*. No black-box scores.
2. **No silent disqualification.** Low-confidence OCR (<0.72), low-similarity retrieval (<0.35), or unresolved conflicts route to **HITL**, never auto-fail.
3. **The LLM never delivers a verdict.** LLMs extract + normalize text → numbers/booleans. A deterministic Python rule engine decides PASS / FAIL / AMBIGUOUS. `src/engine/rule_engine.py` must import nothing from LLM SDKs — enforced in CI.

**Document realism**
4. **Handle scanned + photographed + handwritten documents.** Hindi/Marathi numerals, written-out amounts ("Six Crores"), mixed-script PDFs must normalize correctly.

**Security & legal defensibility**
5. **End-to-end cryptographic auditability.** SQLite WAL + hash-chained append-only events; daily Merkle root anchored via TEC-signed email. `verify_chain()` must be demo-able on stage.
6. **Non-repudiable officer decisions.** Every HITL action and RTI export is signed with a **DSC (Digital Signature Certificate)** or **Aadhaar eSign**, RFC-3161 timestamped.
7. **PII never leaves infrastructure in plaintext.** Microsoft Presidio + custom Indian recognizers (Aadhaar, PAN, GSTIN, EPFO, ESIC) redact before any LLM call; reversible tokenization restores context locally.
8. **Encryption at rest + in transit.** AES-256 for all persistent stores (audit log, ChromaDB, Postgres, uploaded docs); TLS 1.3 for all transport.
9. **RBAC with 6 personas.** SuperAdmin · ProcurementOfficer · Evaluator · HITLReviewer · Auditor · ExternalObserver. Least-privilege enforced at the API layer.
10. **Air-gap deployable.** Every external dependency (LLM, OCR, embeddings) has a documented on-prem fallback so the stack can run inside a CRPF-controlled network.

**Compliance**
11. **Synthetic data only.** No real tender or bidder documents. `data/synthetic/` is the sole test source.
12. **Accessibility & language.** Production UI: WCAG 2.1 AA, **GIGW** (Guidelines for Indian Government Websites), bilingual Hindi + English minimum.

---

## Architecture at a glance

```
                                          ┌────────────────────────────────────┐
NIT PDF  ─┐                               │ PII Redactor (Presidio + Indian    │
          │                               │ recognisers, reversible tokens)    │
Bid pack ─┤                               └────────────────────────────────────┘
          ▼                                              │
     Ingestion ─> Azure OCR ─> Chunker ──────────────────┤
     (+ doc-type (words,      (spatial                   ▼
       heuristic, bboxes,     proximity)            ChromaDB (dense, BGE-M3)
       ClamAV)   confidence,                        + Whoosh (BM25 sparse)
                 handwriting)                                │
                                                             ▼
                                                 Hybrid retrieval (RRF)
                                                             │
                                           ┌─────────────────┼───────────────────┐
                                           ▼                 ▼                   ▼
                               Criterion extractor   Value extractor   CRPF-specific checkers
                               (Claude tool-use)     (Claude tool-use) (blacklist, EMD,
                                                                        near-relations)
                                           └─────────────────┬───────────────────┘
                                                             ▼
                                                 Conflict detector (doc-type hierarchy)
                                                             │
                                                             ▼
                                 Rule engine (pure Python, property-tested, LLM-free)
                                                             │
                                  ┌──────────────────────────┴──────────────────────────┐
                                  ▼                                                     ▼
                          Verdict + trace                                    Audit store (SQLite WAL +
                                  │                                          hash chain, daily Merkle
                                  │                                          root anchored to TEC email)
                                  ▼                                                     │
                   Streamlit UI (Tier-1 demo) ──────┐                                    │
                                                    ├──> DSC/eSign sign-off ────────────┘
                   Next.js UI (Tier-2+ production) ─┘    (PKCS#11, RFC 3161)

Observability everywhere: structlog → OpenTelemetry → Jaeger/Tempo + Prometheus + Sentry.
```

Full rationale: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md).
Security/threat detail: [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).
Phase-by-phase deliverables: [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Tech stack

| Layer | Tier-1 (demo, 14 days) | Tier-2 (pilot) → Tier-3 (prod) |
|---|---|---|
| Language | Python 3.11+ | + TypeScript (UI) |
| API | FastAPI + Uvicorn + Pydantic v2 | + Envoy/Kong gateway, mTLS between services |
| Jobs | Celery + Redis | + Flower, dead-letter queues, Temporal for long workflows |
| OCR primary | Azure Document Intelligence | + AWS Textract + on-prem PaddleOCR-VL (air-gap) |
| OCR fallback | Google Document AI | + Manual HITL lane |
| LLM primary | Anthropic Claude (tool-use JSON) | + AWS Bedrock (India region) + local Llama-3.3-70B / Sarvam-1 |
| Prompt mgmt | `prompts/` dir, git-versioned | + PromptLayer / Langfuse |
| Embeddings | **BGE-M3** (multilingual, Indic-strong) | + BAAI reranker `bge-reranker-v2-m3` |
| Vector store | ChromaDB (PersistentClient, AES-256 at rest) | + pgvector migration path |
| Sparse retrieval | Whoosh (BM25) with RRF fusion | + Elasticsearch for scale |
| RDBMS | PostgreSQL 16 + Alembic | + read replicas, pgBackRest WAL backups |
| Audit store | SQLite WAL + hash chain + daily Merkle root | + HSM-anchored root, object-lock S3 mirror |
| PII redaction | **Microsoft Presidio** + custom recognisers (Aadhaar/PAN/GSTIN/EPFO/ESIC) | + Tonic.ai / SoE framework for encrypted synthetic training |
| Virus scan | ClamAV on upload | + YARA rules for tender-forgery patterns |
| Signatures | DSC via `python-pkcs11`; Aadhaar eSign API | + TSA (eMudhra RFC 3161) |
| UI (demo) | **Streamlit** | (retired after pilot) |
| UI (prod) | — | **Next.js 15 + shadcn/ui + Tailwind**, i18n (hi/en), WCAG 2.1 AA, GIGW-compliant, offline-capable PWA |
| Observability | structlog + Prometheus FastAPI instrumentator + OpenTelemetry (OTLP) | + Grafana dashboards, Sentry, PagerDuty |
| CI | pytest + mypy + ruff + Hypothesis + Semgrep + Trivy + Syft (SBOM) | + DAST (OWASP ZAP), load test (Locust) |
| Synthetic data | Hand-built in Canva + `Misata` | + NVIDIA NeMo Data Designer; SoE encrypted synthetic |

**Explicit non-choices (for now):**
- **No Pinecone / Weaviate / any hosted vector DB.** Data sovereignty.
- **No end-to-end LLM verdicts.** RTI-defensibility forbids it.
- **No blockchain audit.** A hash chain + Merkle root + signed anchor email gives the same tamper-evidence with zero ops overhead.
- **No fine-tuning in Tier-1.** Few-shot + hybrid RAG + synonym map suffices; LoRA lands in Tier-2 once we have sandbox data.

---

## Directory layout

```
CocoMind/
├── CLAUDE.md
├── docs/
│   ├── Theme.md                    # problem statement
│   ├── IMPLEMENTATION_PLAN.md      # deep plan + rationale
│   ├── ROADMAP.md                  # 3 trust tiers, phase deliverables
│   ├── THREAT_MODEL.md             # STRIDE threat model
│   ├── DOC1.md  DOC 2.md  DOC3.md
│   └── Architectural Blueprint... / National Framework... / Hackathon Research...
├── src/
│   ├── ingestion/       # intake, doc-type heuristic, ClamAV
│   ├── ocr/             # Azure + Google fallback + bbox extraction
│   ├── redaction/       # Presidio + Indian recognisers + reversible tokeniser
│   ├── extraction/      # criterion_extractor, value_extractor (Claude tool-use)
│   ├── retrieval/       # chunker, embedder (BGE-M3), ChromaDB + BM25 + RRF
│   ├── checkers/        # blacklist, near_relations, emd, integrity_pact
│   ├── engine/          # rule_engine.py — pure Python, LLM-free (CI enforced)
│   ├── conflict/        # doc-type hierarchy resolver
│   ├── audit/           # SQLite hash chain + Merkle anchor
│   ├── signing/         # PKCS#11 DSC + Aadhaar eSign + RFC 3161 TSA
│   ├── rbac/            # roles, permissions, middleware
│   ├── observability/   # structlog + OTel + Prometheus
│   ├── pipeline/        # orchestrator
│   ├── api/             # FastAPI routes
│   ├── models/          # Pydantic contracts
│   ├── prompts/         # versioned prompt templates
│   └── config/          # env, synonym_map.json, few-shots
├── ui-streamlit/        # Tier-1 demo
│   ├── dashboard.py
│   ├── hitl_review.py
│   └── rti_export.py
├── ui-next/             # Tier-2+ production (parallel track)
│   ├── app/             # Next.js 15 app router
│   ├── components/ui/   # shadcn/ui
│   ├── messages/        # i18n: en.json, hi.json
│   └── e2e/             # Playwright tests
├── data/
│   ├── synthetic/       # 3 demo bid packages (A=PASS, B=FAIL, C=HITL)
│   ├── nits/            # public NITs for few-shot
│   ├── ground_truth/    # bids × criteria × expected verdict (CSV)
│   └── blacklist/       # CVC debarment list snapshot
├── tests/
│   ├── unit/
│   ├── property/        # Hypothesis on rule_engine
│   ├── red_team/        # prompt-injection + PDF fuzz
│   └── e2e/
├── infra/
│   ├── docker-compose.yml
│   ├── helm/            # production charts (Tier-2+)
│   └── terraform/       # Tier-3
├── .github/workflows/   # CI: pytest, mypy, ruff, Semgrep, Trivy, Syft
└── pyproject.toml
```

---

## Domain glossary

**Procurement**: NIT (Notice Inviting Tender) · EMD (Earnest Money Deposit) · BOQ (Bill of Quantities) · TEC (Tender Evaluation Committee) · PQ/TE (Pre-Qualification / Technical Evaluation) · L1 (Lowest-priced qualified bidder) · RA (Reverse Auction) · LOA (Letter of Award).

**Regulators**: GFR 2017 (General Financial Rules) · RTI 2005 (Right to Information) · CVC (Central Vigilance Commission) · CAG (Comptroller & Auditor General) · DPDPA 2023 (Digital Personal Data Protection Act) · IT Act 2000 §43A / §72.

**Portals**: CPPP · GeM · eprocure.gov.in · MCA21 · GSTN.

**Our artefacts**: VTM (Verdict Traceability Matrix) · HITL (Human-in-the-Loop).

**Identity/crypto**: DSC (Digital Signature Certificate) · TSA (Timestamp Authority) · PKCS#11 (hardware-token API) · Aadhaar eSign.

---

## Workflow rules for Claude Code on this repo

1. **Before writing code, read [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) + [`docs/ROADMAP.md`](docs/ROADMAP.md).** If a task doesn't advance a critical-path gate (C1–C5 in the plan) or a Tier boundary, question it.
2. **The rule engine is sacred.** `src/engine/rule_engine.py` imports no LLM SDKs. CI enforces this via `importlinter`.
3. **Every extraction carries provenance.** `ExtractionResult` must include `source_doc_id`, `page_num`, `bbox`, `chunk_id`, `ocr_confidence`, `llm_confidence`, `redaction_map_id`.
4. **Audit writes are append-only and hash-chained.** Any PR touching `src/audit/` needs `code-reviewer` + `security-reviewer` + a passing `verify_chain()` test + Merkle root parity.
5. **HITL beats silent fail.** When in doubt, route to HITL with a reason string.
6. **PII redaction is mandatory before any LLM call.** Any code path that sends text to Claude/GPT/Llama must go through `src/redaction/` first. CI grep-fails the build otherwise.
7. **RBAC at the API layer.** Every FastAPI route declares `required_role`; a decorator enforces it. No silent bypasses.
8. **Synthetic data only.** `data/synthetic/` is the only source of truth for tests.
9. **Commit format:** `<emoji> <type>: <description>` — e.g. `✨ feat: hybrid retrieval with RRF`, `🔒 security: Presidio pipeline`, `📝 docs: threat model STRIDE sheet`.

---

## Quickstart

```bash
# setup
python -m venv .venv && source .venv/Scripts/activate
pip install -e ".[dev]"
cp .env.example .env   # fill AZURE_DOCINT_KEY, ANTHROPIC_API_KEY, DATABASE_URL, DSC_PKCS11_LIB

# services
docker compose up -d postgres redis clamav

# critical-path smoke gates (order matters — see plan § C1–C5)
pytest tests/unit/test_ocr.py             # C1: Azure returns bboxes
pytest tests/unit/test_redaction.py       # C1b: Presidio redacts Aadhaar/PAN
pytest tests/unit/test_llm_extract.py     # C2: LLM returns valid JSON
pytest tests/property/test_rule_engine.py # C3: Hypothesis — rule engine invariants
pytest tests/red_team/                    # C3b: prompt injection blocked
pytest tests/e2e/test_pipeline.py         # C4: full VTM for Bid A
pytest tests/e2e/test_audit_chain.py      # C5: verify_chain + Merkle anchor

# run demo UI
streamlit run ui-streamlit/dashboard.py
```

---

## Where to look for what

| If you need … | Read |
|---|---|
| Problem statement + success criteria | `docs/Theme.md` |
| End-to-end workflow + rationale | `docs/IMPLEMENTATION_PLAN.md` |
| Phase-by-phase deliverables (Tier 1 → 3) | `docs/ROADMAP.md` |
| STRIDE threat model + mitigations | `docs/THREAT_MODEL.md` |
| Original 14-day task list | `docs/DOC 2.md` |
| Why-this-wins narrative | `docs/DOC3.md` |
| Background research (UBID, CDC, RAG) | `docs/Architectural Blueprint ...md`, `docs/National Framework ...md`, `docs/Hackathon Research ...md` |
