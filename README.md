<h1 align="center">CocoMind 🧠</h1>

<div align="center">
  <h3>Secure, AI-Assisted Tender Evaluation & Eligibility Platform</h3>
  <p>Engineered for the Central Reserve Police Force (CRPF) Procurement Ecosystem</p>

  [![Status](https://img.shields.io/badge/Status-Tier--1%20Ready-success)](#)
  [![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](#)
  [![License](https://img.shields.io/badge/License-MIT-green)](#)
  [![Security](https://img.shields.io/badge/Security-RTI--Defensible-critical)](#)
</div>

---

## 📖 The Problem: Why CocoMind Was Built

Government procurement through the Central Public Procurement Portal (CPPP) suffers from massive bottlenecks. When an agency like the CRPF floats a Notice Inviting Tender (NIT), they receive hundreds of bid packages from vendors. These packages consist of hundreds of pages of messy, unstructured PDFs, poorly scanned JPEGs, and handwritten CA certificates. 

Evaluating these bids manually takes weeks. It is prone to human error, subjective bias, and fatigue. More importantly, **every decision must be legally defensible**. If a bidder is disqualified, they have the right to challenge the decision under the **Right to Information (RTI) Act**.

Other AI solutions fail in this space because they use LLMs (Large Language Models) as "black boxes" to make the final PASS/FAIL decision. If an LLM hallucinates a disqualification, the government cannot explain the algorithm in court. 

## 🎯 The Solution: What CocoMind Actually Does

**CocoMind** is a high-performance decision-support platform that automates the extraction and evaluation of complex bids against the NIT criteria, **without compromising legal defensibility**. 

It uses a unique **Tiered Trust Architecture**:
1. **Extraction (AI)**: It uses advanced OCR, spatial chunking, Hybrid Retrieval (BGE-M3 + BM25), and LLMs to read the messy PDFs and extract data (e.g., finding the precise "Annual Turnover" value from a buried CA certificate).
2. **Evaluation (Code)**: It feeds the extracted value into a **100% LLM-free, pure-Python Rule Engine**. The Rule Engine runs deterministic math (`Value >= Threshold`) and outputs the final PASS/FAIL verdict.

This guarantees that the AI only acts as a fast reader, while hard-coded math acts as the judge. 

---

## 🔥 Key Architectural Capabilities

### 1. RTI-Defensible Provenance (White-Box AI)
CocoMind generates a **Verdict Traceability Matrix (VTM)**. For every decision made, the system provides:
- The exact raw text that was extracted.
- A bounding box highlighting the value on the original PDF page.
- The deterministic mathematical expression that evaluated it (e.g., `60000000 >= 50000000`).
If challenged under RTI regulations, procurement officers can instantly generate a PDF report tracing exactly why a bidder was disqualified.

### 2. Immutable Hash-Chained Audit Trail
Government evaluations require absolute tamper-proofing.
- Every verdict and human interaction is recorded in a SQLite Write-Ahead Log (WAL) audit chain.
- Each record's SHA-256 hash mathematically links to the previous record.
- Database `UPDATE` and `DELETE` operations are strictly blocked by cryptographic triggers.
- Daily Merkle roots are generated for ledger verification.

### 3. Human-in-the-Loop (HITL) Fallback
The AI does not make assumptions. If it detects conflicting data (e.g., Cover Letter claims 50 Crore, but Audited Balance Sheet says 40 Crore), or low-confidence blurry handwriting, CocoMind automatically halts the evaluation and routes the specific document to an officer's Streamlit Dashboard for manual review.

### 4. Zero-Trust PII Redaction
Bidders routinely upload documents containing sensitive Indian Personally Identifiable Information (PII).
- CocoMind intercepts the data *before* it reaches the LLM.
- Custom Presidio recognisers use Regex and checksum algorithms (like the Verhoeff algorithm for Aadhaar) to detect Aadhaar, PAN, GSTIN, EPFO, ESIC, and IFSC codes.
- These physical entities are converted into reversible UUID tokens (e.g., `<IN_AADHAAR: 123e4567>`), ensuring the LLM never sees the private data.

---

## 🛠️ Technology Stack

- **Backend Logic**: FastAPI, Pydantic v2
- **Data Ingestion**: PyMuPDF, python-magic, pdf2image
- **Extraction & Intelligence**: Anthropic Claude `tool-use`, Azure Document Intelligence (OCR)
- **Data Privacy**: Microsoft Presidio (Customized for Indian PII)
- **Retrieval Engine**: ChromaDB (Dense/BGE-M3), Whoosh (Sparse/BM25), Reciprocal Rank Fusion
- **User Interface**: Streamlit
- **Code Quality**: Pytest (with Hypothesis Property testing), Ruff, Mypy, Import-Linter (enforcing LLM isolation)

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python**: version `3.11` or higher
- **Git** installed on your system

### 1. Installation

Clone the repository and install the development configuration:

```bash
git clone https://github.com/yash-dev007/CocoMind.git
cd CocoMind
pip install -e ".[dev]"
```

### 2. Environment Configuration

Copy the example environment file and insert your respective API keys:

```bash
cp .env.example .env
```
Ensure you provide a valid `ANTHROPIC_API_KEY` and `AZURE_DOCINT_KEY`.

### 3. Run the Test Suite

We highly recommend running the test suite to verify the rule engine invariants and audit chain locally. Code is fully typed and enforces strict import contracts to isolate the LLM from the execution logic.

```bash
pytest tests/ -v
```

### 4. Boot the Demo Interface

Launch the full-featured Streamlit HITL Dashboard to evaluate mock bids:

```bash
streamlit run ui-streamlit/dashboard.py
```

---

## 👨‍💻 Contributing

We welcome structural improvements, test-case expansions, and additional heuristic PII additions to our Indian Recognisers. 

For a complete breakdown of rules (including our strict rule-engine LLM-isolation mandate), please review our [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

This software is released under the standard [MIT License](LICENSE).
