# CocoMind — Roadmap

Three trust tiers. Each tier is a superset of the previous. Every feature in the codebase is tagged to a tier in its docstring.

| Tier | Purpose | Horizon | Audience | Environment |
|---|---|---|---|---|
| **Tier-1** | Hackathon demo | 14 days (Round 2) | Jury + CRPF observers | Local sandbox, synthetic data |
| **Tier-2** | Pilot deployment | 3 months post-demo | 1 CRPF circle, internal users | Private cloud / on-prem, real redacted data |
| **Tier-3** | Production | 6–12 months | All CRPF procurement cells | On-prem air-gap, live tenders |

---

## Tier-1 — Hackathon demo (Days 1–14)

**Goal:** a system that upload-to-verdict runs in <5 min, produces a signed VTM + RTI export, and answers every hard question with something already in the architecture.

**Scope:**
- 6-stage pipeline: ingest → OCR (Azure) → redact (Presidio) → chunk/embed (BGE-M3) → hybrid retrieve (Chroma+BM25+RRF) → extract (Claude tool-use) → conflict → rule engine → audit chain → Streamlit UI.
- 4 CRPF checkers: blacklist, near-relations, EMD validity, integrity pact.
- 3 designed demo bids (A=PASS, B=FAIL, C=HITL+redaction+prompt-injection).
- DSC sign-off on HITL decisions (dev cert, labelled as dev in UI).
- Daily Merkle root via email to a demo `tec-chair@demo.local`.
- CI: ruff + mypy + pytest + Hypothesis + Semgrep + Trivy + Syft + import-linter.

**Success criteria:** C1–C5 gates green (see `IMPLEMENTATION_PLAN.md` §5); three clean demo rehearsals; backup video recorded.

**Explicit exclusions:** Next.js UI, live CVC blacklist API, real DSC token, penetration test, multi-region, load test.

---

## Tier-2 — Pilot deployment (Months 1–3 post-demo)

**Goal:** get a real CRPF procurement circle using CocoMind on redacted historical tenders, with real DSC tokens and auditable outcomes that a TEC chair will sign.

**New capabilities:**
- **Next.js 15 UI** (shadcn/ui + Tailwind + `next-intl` en/hi) with GIGW compliance, WCAG 2.1 AA, offline PWA, low-bandwidth mode, mobile/tablet responsive.
- **OIDC via MeriPehchaan** (national SSO) for officer login.
- **Real DSC (eMudhra/Capricorn)** via PKCS#11; Aadhaar eSign fallback via NSDL.
- **RFC 3161 timestamp** on every signed record (eMudhra TSA).
- **Reranker** (`bge-reranker-v2-m3`) on fused top-20.
- **RAGAS evaluation harness** — nightly run against ground-truth set; drift alerts.
- **CVC debarment list** refresh job (weekly scrape → versioned snapshot).
- **Prompt management** (PromptLayer or Langfuse) with A/B + versioning + cost tracking.
- **Observability**: Grafana dashboards (pipeline latency, OCR confidence histogram, HITL queue depth, LLM cost/bid), Sentry error tracking.
- **Backup + DR**: pgBackRest WAL archival to object-lock S3; daily audit-file snapshot; RPO 1h / RTO 4h.
- **DPIA** (Data Protection Impact Assessment) filed with the DPO.
- **CERT-In empanelled pentest** before go-live.
- **Load test** (Locust) — 500 concurrent bids / 100 NITs.
- **Helm chart** for Kubernetes deployment.

**Success criteria:**
- Real TEC chair signs off on a real (redacted) evaluation run.
- Zero PII leaked in an independent audit.
- Pentest report clean (no critical, no high > 5 days old).
- RAGAS faithfulness ≥ 0.85, answer-relevance ≥ 0.80.
- 99.5% uptime over the 3-month window.

**Deferred to Tier-3:**
- Live integrations (GeM, CPPP, MCA21, GSTN).
- Multi-region failover.
- On-prem Llama deployment.
- HSM-backed key storage.
- Formal STQC audit.

---

## Tier-3 — Production (Months 4–12 and ongoing)

**Goal:** CocoMind as the default evaluation surface for CRPF procurement, surviving CAG audits and RTI storms, usable in air-gapped environments.

**New capabilities:**
- **Air-gap deployment**: on-prem Llama-3.3-70B (or Sarvam-1) + on-prem PaddleOCR-VL + offline BGE-M3. Zero external API dependency.
- **HSM-backed keys** for DSC + audit-chain root signing.
- **Live integrations via API Setu**:
  - MCA21 → company registration verification
  - GSTN → GST compliance check
  - GeM / CPPP / eprocure.gov.in → NIT auto-fetch
  - EPFO / ESIC → employer compliance check
- **Multi-region active-passive** with cross-region WAL streaming.
- **Runtime threat detection** (Falco) on Kubernetes.
- **DAST** (OWASP ZAP) scheduled in CI.
- **Formal audits**: STQC, CERT-In annual, CAG pre-clearance.
- **LoRA fine-tune** on accumulated sandbox data (only if RAGAS shows Claude few-shots falling below 0.85 on our corpus).
- **Red-teaming program** (external) quarterly.
- **Bidder self-service portal** (optional, separate trust boundary) — bidders upload, get pre-submission eligibility preview; their data lives in a separate encrypted tenant.
- **SoE framework** (encrypted synthetic data) for continual improvement without exposing live tender content.

**Success criteria:**
- Passes CAG pre-clearance audit.
- Passes DPDPA Data Protection Board inspection.
- STQC certified.
- Survives a real RTI challenge with verified audit chain + Merkle anchor.
- Officer-hours-per-tender reduced by ≥ 70% on a real tender vs. the manual baseline (measured).
- Zero silent disqualifications across a full financial-year audit.

---

## Trust-tier checklist (use on every PR)

```
□ Tier-1 tags: ingestion · OCR · redaction · hybrid RAG · rule engine · audit chain · 4 checkers · Streamlit · dev-DSC · CI baseline
□ Tier-2 tags: Next.js UI · OIDC · real DSC · TSA · RAGAS · reranker · Grafana · DPIA · pentest
□ Tier-3 tags: air-gap · HSM · API Setu live · multi-region · STQC · CAG clearance
□ Security controls match target tier (see IMPLEMENTATION_PLAN.md §9 matrix)
□ Feature flag gates any cross-tier capability until its tier is live
```

---

## Post-hackathon pilot playbook (summary)

**Month 1 post-demo:**
1. Secure a willing CRPF procurement circle + signed MoU.
2. Scope the pilot: 10 historical redacted tenders.
3. Stand up the Tier-2 cluster (private cloud or circle DC).
4. Run the Next.js track in parallel while Tier-1 pipeline stabilises.
5. Begin DPIA.

**Month 2:**
1. Onboard 3 evaluators + 1 auditor + 1 procurement officer; DSC tokens issued.
2. RAGAS harness live; weekly quality review.
3. CERT-In pentest begins.

**Month 3:**
1. Pentest remediations; DPIA submitted.
2. Live pilot run on 1 ongoing (non-critical) tender with TEC chair shadow-signing.
3. Go / no-go review with CRPF leadership for Tier-3 rollout.

---

## Hard questions (rehearsal sheet for jury)

| Question | Answer |
|---|---|
| "What if the LLM hallucinates a number?" | LLM only normalises text → typed value. A 30-line Python rule engine, in `src/engine/rule_engine.py` with 100% branch coverage + Hypothesis invariants, produces the verdict. Show the file. |
| "What if a bidder hides `ignore prior instructions` in their PDF?" | Redaction runs first. Even if injection survives, the rule engine — not the LLM — decides the verdict. We have a CI red-team suite with 10 payloads. |
| "How is this RTI-defensible?" | SQLite WAL + SHA-256 chained audit, daily Merkle root anchored to TEC-chair email with RFC 3161 timestamp, DSC-signed verdicts, RTI export reproducible from the log alone. `verify_chain()` is one click away. |
| "Data security? PII leakage?" | Presidio + Indian recognisers (Aadhaar Verhoeff-checked, PAN/GSTIN/EPFO) with reversible tokens; raw bytes never leave infra; LLM sees only redacted snippets; CI grep-fails any LLM call that bypasses the redactor. |
| "Scale to 500 bids?" | Each bid = independent Celery task; tested at 500 concurrent in Tier-2 load test. Show Grafana dashboard. |
| "Air-gap?" | Tier-3 runs on-prem Llama-3.3-70B + PaddleOCR-VL + offline BGE-M3. Zero external API. |
| "How do you handle ambiguity?" | Three confidence floors (OCR 0.72, retrieval 0.35, LLM 0.70). Any breach → AMBIGUOUS → HITL queue. Never silent INELIGIBLE. |
| "What's different from Minaions or generic RAG bots?" | Rule engine + hash chain + DSC sign-off + HITL as first-class. This is a decision-support engine with formal verification, not a chatbot. |
| "Will this pass CAG?" | Append-only log + Merkle anchor + signed decisions + reproducible RTI export. Tier-3 includes CAG pre-clearance. |
| "What about Hindi/Marathi?" | BGE-M3 multilingual embeddings; value extractor handles Hindi/Marathi numerals + written-out amounts; synonym map has 6+ variants in each language per criterion. |
