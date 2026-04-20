# CocoMind 🧠

> **AI-Assisted CRPF Tender Evaluation and Eligibility Analysis Platform**

CocoMind is a high-performance, RTI-defensible decision-support system designed to automate the evaluation of complex tender and procurement bids (e.g., NITs). Built with an unwavering commitment to compliance, security, and transparency, CocoMind employs Tiered Trust Architecture to accelerate technical evaluations without compromising legal defensibility.

![Demo Badge](https://img.shields.io/badge/Status-Tier--1%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌟 Key Features

1. **RTI-Defensible Provenance**: Every automated decision is backed by an exact chunk of source text, bounding boxes, and OCR/LLM confidence scores. A 100% pure-Python Rule Engine dictates all logic (zero LLMs are used for pass/fail decisions).
2. **Immutable Audit Trail**: SQLite WAL hash-chained audit logging ensures that `UPDATE`/`DELETE` are cryptographically and statically blocked. Features daily Merkle root anchoring.
3. **Mandatory PII Redaction**: Before any text hits an LLM, Indian-specific PII (Aadhaar, PAN, GSTIN, EPFO, ESIC, IFSC) is irreversibly masked via Presidio and custom checksum recognisers.
4. **Intelligent Hybrid Retrieval**: Fuses dense `BGE-M3` embeddings via ChromaDB and sparse `BM25` Whoosh matching with Reciprocal Rank Fusion (RRF) for flawless evidence extraction.
5. **Tiered Trust & HITL (Human-in-the-Loop)**: CocoMind auto-passes high-confidence matches and immediately escalates ambiguous data, poorly-scanned documents, or confidence drops to human Procurement Officers for review.

## 🚀 Quickstart

### Prerequisites:
- Python 3.11+
- Git

### Installation:

1. **Clone the repo**
   ```bash
   git clone https://github.com/yash-dev007/CocoMind.git
   cd CocoMind
   ```

2. **Install core + dev dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Add your Anthropic and Azure Document Intelligence keys
   ```

4. **Launch the Demo Dashboard**
   ```bash
   streamlit run ui-streamlit/dashboard.py
   ```

---

## 💻 Tech Stack

- **Backend**: FastAPI, Pydantic v2
- **UI**: Streamlit
- **Extraction / LLM**: Anthropic Claude + Azure Document Intelligence
- **Retrieval**: ChromaDB, Whoosh, Sentence-Transformers (`BGE-M3`)
- **Redaction**: Microsoft Presidio
- **Persistence**: SQLite (Audit), PostgreSQL (Relational)
- **Quality**: Pytest, Ruff, Mypy, Hypothesis, Import-Linter

---

## 🛡️ Security & Contracts

We heavily enforce architectural boundaries to stay legally compliant for Government Procurement usage:
- **LLM Isolation**: `src.engine` cannot import AI libraries. Enforced via `import-linter`.
- **RBAC Guardrails**: 6 Distinct Personas dictating exactly who can evaluate, review, or authorize signatures.
- **Prompt Injection Defense**: Adversarial AI payloads hit the deterministic Rule Engine boundary and immediately `FAIL`.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, development workflow, and testing requirements.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
