# CRPF tender evaluation starts with public NIT publication on CPPP/eprocure.gov.in and
crpf.gov.in, where bidders register, prepare two-bid submissions (technical/financial), and
upload scanned docs like EMD, GST/PAN, EPFO/ESIC, experience certs, affidavits, and financial
proofs (e.g., turnover Rs. 12.8 Lakh avg over 3 years). The AI platform automates from here,
ingesting messy uploads for zero-bias, traceable analysis.scribd+3

## Manual CRPF Workflow
CRPF uses two-bid e-tendering via CPPP/GeM: Bidders submit technical bid (docs/proofs) +
financial BOQ online; EMD (2%, e.g., Rs. 24,011) offline originally. Tender Evaluation Committee
(TEC) opens technical bids post-deadline, checks pre-qual: enlistment validity, similar works
(80%/60%/40% value), net worth Rs. 4 Lakh/banker cert Rs. 12.8 Lakh, no blacklisting/near-
relations in CRPF, affidavits (no retired CRPF <2yrs). Qualified bids open financially; L1 awarded
post-negotiation/RA; RTI demands full traceability.crpf+3
Timeline: NIT publish → Bid due (e.g., online till 11:00 IST) → Tech open → PQ/TE → Price open →
Award/LOA.dcsem+1

## AI Platform Research Workflow
- Data Sourcing: Download CRPF NITs (e.g.,
https://crpf.gov.in/Upload/Tender/1318122024-366.pdf for DG O&M requiring turnover
Rs. 12.8L, 80% similar work). CPPP API for live tenders; mock bidder PDFs/photos (scan
certs via phone). Train on 100+ public NITs/CPWD rules.eprocure+1
- Prototype Setup: GitHub repo; Streamlit/FastAPI backend; Azure/AWS free tier;
LangChain for LLM/RAG; Pinecone free vector DB.
- Fine-Tuning: Use SynthDoG for handwritten OCR data; LoRA on Llama3 for tender-
specific prompting (e.g., "Extract min turnover rule").extend
- Testing: 50 simulated bids vs. real NITs; measure accuracy (F1>95%), audit matrix
completeness.ijcrt
- Hackathon Demo: Upload NIT PDF + bidder zip → Instant Verdict Matrix → HITL flags.

## End-to-End AI Workflow

## Step 1: Tender Ingestion (Admin uploads NIT PDF). OCR (Azure Doc Intel) → LLM+RAG extracts
rules: Mandatory (e.g., "Turnover avg Rs. 12.8L last 3yrs") vs. Optional; store in vector DB with
metadata (page/box).sparkco

## Step 2: Bidder Submission (Drag-drop PDFs/photos/zip). Auto-OCR all docs → Categorize
(financial/experience/certs) via LLM classification.docuexprt

## Step 3: Extraction. Per doc: Few-shot LLM prompts retrieve bidder claims (e.g., "FY24: Rs. 15Cr
turnover"); normalize units ('Cr'→Crore, 'Revenue'→'Turnover').indiaai+1

## Step 4: Matching. Rule-engine verifies (e.g., SymPy: avg() >=12.8 ? Pass); LLM explains edge
cases (conflicts: flag highest conf).bidplus.gem+3

## Step 5: Verdict & Audit. Generate Matrix (table export); low-conf → HITL UI highlights snippet
(e.g., bounding box on scanned turnover table).ofnisystems

## Step 6: Output. Dashboard: Pass % per criterion, full trace; API for CRPF integration; logs for

## RTI.
Edge Handling: Conflicts → HITL priority latest page; Hindi → mBERT; <70% OCR → Re-scan
prompt.minaions+1

## Stage Tools Output Citation
Ingestion Azure Textract JSON text/boxes sparkco
Extraction Claude + RAG Criteria list tenderconsultants.co
Matching Regex + LLM Pass/Fail + reason indiaai
Audit Pandas → PDF Trace Matrix ofnisystems
This workflow cuts manual time 90%, ensures auditability for CRPF's 1000+ annual tenders.

