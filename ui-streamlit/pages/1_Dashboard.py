"""CocoMind — Verdict Dashboard Page (Tier-1 Streamlit demo).

Bid selector, per-bid criterion table with colored verdict badges,
expandable rows showing full provenance trace, pipeline status metrics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audit.chain import verify_chain
from src.models.verdicts import VerdictStatus  # noqa: F401

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Dashboard — CocoMind",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS (reuse from Home) ────────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a0f1e 100%); color: #e2e8f0; }
  [data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1b2a 0%, #1a1f3a 100%); border-right: 1px solid rgba(99,102,241,0.2); }
  .badge-pass { display:inline-block; background:linear-gradient(135deg,#10b981,#059669); color:white; padding:4px 14px; border-radius:20px; font-weight:700; font-size:12px; letter-spacing:.5px; box-shadow:0 0 12px rgba(16,185,129,.4); }
  .badge-fail { display:inline-block; background:linear-gradient(135deg,#ef4444,#dc2626); color:white; padding:4px 14px; border-radius:20px; font-weight:700; font-size:12px; letter-spacing:.5px; box-shadow:0 0 12px rgba(239,68,68,.4); }
  .badge-ambiguous { display:inline-block; background:linear-gradient(135deg,#f59e0b,#d97706); color:white; padding:4px 14px; border-radius:20px; font-weight:700; font-size:12px; letter-spacing:.5px; box-shadow:0 0 12px rgba(245,158,11,.4); }
  .metric-card { background:rgba(30,41,59,.8); border:1px solid rgba(99,102,241,.3); border-radius:14px; padding:20px; text-align:center; }
  .metric-value { font-size:36px; font-weight:800; color:#e2e8f0; line-height:1; }
  .metric-label { font-size:11px; color:#94a3b8; margin-top:6px; text-transform:uppercase; letter-spacing:.8px; }
  .stButton > button { background:linear-gradient(135deg,#6366f1,#8b5cf6); color:white; border:none; border-radius:10px; padding:10px 24px; font-weight:600; font-size:14px; box-shadow:0 4px 15px rgba(99,102,241,.3); }
  .stButton > button:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(99,102,241,.5); }
  [data-testid="stExpander"] { background:rgba(30,41,59,.5)!important; border:1px solid rgba(99,102,241,.2)!important; border-radius:10px!important; }
  [data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,#6366f1,#8b5cf6)!important; border-radius:10px!important; }
  .criterion-row { border-bottom: 1px solid rgba(99,102,241,0.1); padding: 12px 0; }
  .doc-type-chip { display:inline-block; background:rgba(99,102,241,.15); border:1px solid rgba(99,102,241,.3); border-radius:12px; padding:2px 10px; font-size:11px; color:#a5b4fc; }
  .conf-bar-bg { background: rgba(30,41,59,.8); border-radius:4px; overflow:hidden; height:6px; }
  .conf-bar-fill-high { background: linear-gradient(90deg, #10b981, #059669); height:6px; border-radius:4px; }
  .conf-bar-fill-mid { background: linear-gradient(90deg, #f59e0b, #d97706); height:6px; border-radius:4px; }
  .conf-bar-fill-low { background: linear-gradient(90deg, #ef4444, #dc2626); height:6px; border-radius:4px; }
  hr { border-color: rgba(99,102,241,.2)!important; }
</style>
""", unsafe_allow_html=True)

# ─── Sample VTM Data ──────────────────────────────────────────────────────────

SAMPLE_VTMS = {
    "BID-A": {
        "name": "M/s Sharma Industrial Pvt Ltd",
        "overall": "ELIGIBLE",
        "rows": [
            {
                "criterion": "Average Annual Turnover",
                "category": "financial",
                "mandatory": True,
                "verdict": "PASS",
                "value": "₹6,00,00,000",
                "threshold": "≥ ₹5,00,00,000",
                "expression": "60000000 >= 50000000 → True",
                "source": "CA Certificate, Page 2",
                "bbox": "[120, 340, 680, 390]",
                "confidence": 0.95,
                "ocr_confidence": 0.96,
                "llm_confidence": 0.95,
                "doc_type": "ca_certificate",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-001-A",
            },
            {
                "criterion": "Similar Works Experience",
                "category": "technical",
                "mandatory": True,
                "verdict": "PASS",
                "value": "5 projects ≥ ₹10L each",
                "threshold": "≥ 3 similar projects",
                "expression": "5 >= 3 → True",
                "source": "Experience Certificate, Page 1",
                "bbox": "[80, 200, 600, 260]",
                "confidence": 0.92,
                "ocr_confidence": 0.94,
                "llm_confidence": 0.92,
                "doc_type": "experience_cert",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-002-A",
            },
            {
                "criterion": "GST Registration",
                "category": "compliance",
                "mandatory": True,
                "verdict": "PASS",
                "value": "07AAACS1234A1ZH (Valid)",
                "threshold": "Valid GSTIN required",
                "expression": "bool(True) = True",
                "source": "GST Certificate, Page 1",
                "bbox": "[100, 140, 540, 180]",
                "confidence": 0.98,
                "ocr_confidence": 0.99,
                "llm_confidence": 0.98,
                "doc_type": "gst_cert",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-003-A",
            },
            {
                "criterion": "EMD / Bank Guarantee",
                "category": "financial",
                "mandatory": True,
                "verdict": "PASS",
                "value": "₹10,00,000 · valid till 2026-08-15",
                "threshold": "≥ ₹5,00,000 · ≥ 45 days validity",
                "expression": "BG ₹10L ≥ ₹5L and 2026-08-15 ≥ 2026-06-30",
                "source": "Bank Guarantee, Page 1",
                "bbox": "[60, 300, 700, 360]",
                "confidence": 0.90,
                "ocr_confidence": 0.91,
                "llm_confidence": 0.90,
                "doc_type": "emd_document",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-004-A",
            },
            {
                "criterion": "Near Relations Declaration",
                "category": "declaration",
                "mandatory": True,
                "verdict": "PASS",
                "value": "Declared: No near relations in CRPF",
                "threshold": "Must declare no near relations",
                "expression": "declaration_present and keywords_found",
                "source": "Self Declaration Affidavit, Page 1",
                "bbox": "[100, 420, 680, 460]",
                "confidence": 0.93,
                "ocr_confidence": 0.94,
                "llm_confidence": 0.93,
                "doc_type": "self_declaration",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-005-A",
            },
            {
                "criterion": "Integrity Pact",
                "category": "declaration",
                "mandatory": True,
                "verdict": "PASS",
                "value": "Signed CRPF Integrity Pact (template hash matched)",
                "threshold": "CRPF standard template, signed",
                "expression": "template_hash_match = True",
                "source": "Integrity Pact, Page 1",
                "bbox": "[80, 100, 720, 140]",
                "confidence": 0.97,
                "ocr_confidence": 0.98,
                "llm_confidence": 0.97,
                "doc_type": "integrity_pact",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-006-A",
            },
        ],
    },
    "BID-B": {
        "name": "M/s Verma Tech Solutions",
        "overall": "INELIGIBLE",
        "rows": [
            {
                "criterion": "Average Annual Turnover",
                "category": "financial",
                "mandatory": True,
                "verdict": "PASS",
                "value": "₹7,50,00,000",
                "threshold": "≥ ₹5,00,00,000",
                "expression": "75000000 >= 50000000 → True",
                "source": "Audited Financial Statement, Page 4",
                "bbox": "[100, 280, 680, 320]",
                "confidence": 0.93,
                "ocr_confidence": 0.94,
                "llm_confidence": 0.93,
                "doc_type": "audited_financial_statement",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-001-B",
            },
            {
                "criterion": "Similar Works Experience",
                "category": "technical",
                "mandatory": True,
                "verdict": "FAIL",
                "value": "1 project submitted",
                "threshold": "≥ 3 similar projects",
                "expression": "1 >= 3 → False ❌",
                "source": "Experience Certificate, Page 1",
                "bbox": "[80, 180, 620, 220]",
                "confidence": 0.88,
                "ocr_confidence": 0.90,
                "llm_confidence": 0.88,
                "doc_type": "experience_cert",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-002-B",
            },
            {
                "criterion": "GST Registration",
                "category": "compliance",
                "mandatory": True,
                "verdict": "PASS",
                "value": "09AABCV1234B1Z5 (Valid)",
                "threshold": "Valid GSTIN required",
                "expression": "bool(True) = True",
                "source": "GST Certificate, Page 1",
                "bbox": "[100, 120, 560, 160]",
                "confidence": 0.97,
                "ocr_confidence": 0.98,
                "llm_confidence": 0.97,
                "doc_type": "gst_cert",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-003-B",
            },
            {
                "criterion": "EMD / Bank Guarantee",
                "category": "financial",
                "mandatory": True,
                "verdict": "PASS",
                "value": "₹8,00,000 · valid till 2026-09-01",
                "threshold": "≥ ₹5,00,000 · ≥ 45 days validity",
                "expression": "BG ₹8L ≥ ₹5L and 2026-09-01 ≥ 2026-06-30",
                "source": "Bank Guarantee, Page 1",
                "bbox": "[60, 340, 700, 380]",
                "confidence": 0.91,
                "ocr_confidence": 0.92,
                "llm_confidence": 0.91,
                "doc_type": "emd_document",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-004-B",
            },
        ],
    },
    "BID-C": {
        "name": "M/s Gupta Equipment Co",
        "overall": "PENDING HITL",
        "rows": [
            {
                "criterion": "Average Annual Turnover",
                "category": "financial",
                "mandatory": True,
                "verdict": "AMBIGUOUS",
                "value": "₹5,20,00,000 (handwritten CA) vs ₹4,80,00,000 (cover letter)",
                "threshold": "≥ ₹5,00,00,000",
                "expression": "CONFLICT UNRESOLVED — two docs disagree by >5%",
                "source": "CA Certificate (photo), Page 1",
                "bbox": "[120, 300, 640, 350]",
                "confidence": 0.55,
                "ocr_confidence": 0.58,
                "llm_confidence": 0.55,
                "doc_type": "ca_certificate",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-001-C",
            },
            {
                "criterion": "Near Relations Declaration",
                "category": "declaration",
                "mandatory": True,
                "verdict": "AMBIGUOUS",
                "value": "Declaration present but keywords not found",
                "threshold": "Must declare no near relations in CRPF",
                "expression": "keywords_found = False → NOT_FOUND → HITL",
                "source": "Self Declaration, Page 2",
                "bbox": "[80, 380, 680, 420]",
                "confidence": 0.40,
                "ocr_confidence": 0.45,
                "llm_confidence": 0.40,
                "doc_type": "self_declaration",
                "prompt_version": "value_extractor@v1.3",
                "audit_id": "AUD-002-C",
            },
        ],
    },
}


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 16px;">
      <div style="font-size:32px;">📊</div>
      <div style="font-size:16px; font-weight:700; color:#e2e8f0;">Dashboard</div>
      <div style="font-size:11px; color:#64748b;">Verdict Traceability Matrix</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    bid_options = {f"{k} — {v['name']}": k for k, v in SAMPLE_VTMS.items()}
    selected_label = st.selectbox("🗂️ Select Bid", list(bid_options.keys()))
    selected_bid = bid_options[selected_label]
    bid_data = SAMPLE_VTMS[selected_bid]

    st.divider()

    # Audit chain status
    st.markdown("**🔐 Audit Chain**")
    try:
        chain_ok = verify_chain()
        if chain_ok:
            st.success("Chain INTACT ✅")
        else:
            st.error("Chain TAMPERED ❌")
    except Exception:
        st.info("DB not initialised yet")

    st.divider()
    st.markdown("""
    <div style="background:rgba(245,158,11,.1); border:1px solid rgba(245,158,11,.3);
      border-radius:10px; padding:10px; font-size:11px; color:#fbbf24;">
      ⚠️ <b>Tier-1 Demo</b><br>
      <span style="color:#94a3b8;">Synthetic data · Dev DSC</span>
    </div>
    """, unsafe_allow_html=True)


# ─── Page Header ──────────────────────────────────────────────────────────────

st.markdown("""
<h1 style="font-size:28px; font-weight:800; background:linear-gradient(135deg,#6366f1,#a78bfa);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin:0;">
  📊 Tender Evaluation Dashboard
</h1>
<div style="font-size:13px; color:#64748b; margin-top:4px; margin-bottom:20px;">
  Criterion-by-criterion · Source-pinned · RTI-auditable eligibility verdicts
</div>
""", unsafe_allow_html=True)

# ─── Bid Header ───────────────────────────────────────────────────────────────

rows = bid_data["rows"]
pass_count = sum(1 for r in rows if r["verdict"] == "PASS")
fail_count = sum(1 for r in rows if r["verdict"] == "FAIL")
ambiguous_count = sum(1 for r in rows if r["verdict"] == "AMBIGUOUS")

st.markdown(f"""
<div style="background:rgba(30,41,59,.7); border:1px solid rgba(99,102,241,.25);
  border-radius:16px; padding:18px 24px; margin-bottom:20px;">
  <div style="font-size:18px; font-weight:700; color:#e2e8f0;">{selected_bid} — {bid_data['name']}</div>
  <div style="font-size:12px; color:#64748b; margin-top:2px;">
    {len(rows)} criteria evaluated · Overall: <b style="color:{'#10b981' if bid_data['overall']=='ELIGIBLE' else '#ef4444' if bid_data['overall']=='INELIGIBLE' else '#f59e0b'};">{bid_data['overall']}</b>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Metrics ──────────────────────────────────────────────────────────────────

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-card" style="border-color:rgba(99,102,241,.4);">
      <div class="metric-value" style="color:#a5b4fc;">{len(rows)}</div>
      <div class="metric-label">Total Criteria</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card" style="border-color:rgba(16,185,129,.4);">
      <div class="metric-value" style="color:#10b981;">{pass_count}</div>
      <div class="metric-label">✅ Pass</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="metric-card" style="border-color:rgba(239,68,68,.4);">
      <div class="metric-value" style="color:#ef4444;">{fail_count}</div>
      <div class="metric-label">❌ Fail</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card" style="border-color:rgba(245,158,11,.4);">
      <div class="metric-value" style="color:#f59e0b;">{ambiguous_count}</div>
      <div class="metric-label">⚠️ Ambiguous</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ─── Overall Verdict Banner ───────────────────────────────────────────────────

if fail_count > 0:
    st.error(
        f"**🚫 Overall: INELIGIBLE** — {fail_count} mandatory criterion(s) failed. "
        f"Rule engine expression pinned for each FAIL row below."
    )
elif ambiguous_count > 0:
    st.warning(
        f"**⚠️ Overall: PENDING HITL** — {ambiguous_count} criterion(s) require manual review. "
        f"Route to HITL Review page."
    )
else:
    st.success("**✅ Overall: ELIGIBLE** — All mandatory criteria passed cleanly.")

st.divider()

# ─── Criterion Table ──────────────────────────────────────────────────────────

cat_icons = {
    "financial": "💰",
    "technical": "🔧",
    "compliance": "📋",
    "declaration": "📝",
    "document": "📄",
}

for i, row in enumerate(rows):
    verdict = row["verdict"]
    badge_html = f'<span class="badge-{verdict.lower()}">{verdict}</span>'
    cat_icon = cat_icons.get(row["category"], "📌")
    mandatory_color = "#ef4444" if row["mandatory"] else "#f59e0b"
    mandatory_label = "Mandatory" if row["mandatory"] else "Optional"
    conf_pct = int(row["confidence"] * 100)
    conf_class = (
        "conf-bar-fill-high"
        if conf_pct >= 75
        else "conf-bar-fill-mid"
        if conf_pct >= 50
        else "conf-bar-fill-low"
    )

    col_name, col_meta, col_verdict, col_conf = st.columns([3, 2, 1.2, 1.2])

    with col_name:
        st.markdown(
            f"**{row['criterion']}**",
            help=f"Rule Expression: {row['expression']}",
        )
    with col_meta:
        st.markdown(
            f'{cat_icon} {row["category"].title()} &nbsp;'
            f'<span style="color:{mandatory_color}; font-size:11px;">● {mandatory_label}</span>',
            unsafe_allow_html=True,
        )
    with col_verdict:
        st.markdown(badge_html, unsafe_allow_html=True)
    with col_conf:
        st.markdown(
            f"""
            <div style="font-size:12px; color:#94a3b8; margin-bottom:2px;">{conf_pct}%</div>
            <div class="conf-bar-bg">
              <div class="{conf_class}" style="width:{conf_pct}%;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Full provenance trace expander
    with st.expander(f"📋 Full Trace — {row['criterion']}", expanded=False):
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.markdown("**📦 Extracted Value**")
            st.code(row["value"], language="text")
            st.markdown("**📏 Threshold**")
            st.code(row["threshold"], language="text")
        with tc2:
            st.markdown("**⚙️ Rule Expression**")
            st.code(row["expression"], language="python")
            st.markdown("**🏷️ Doc Type**")
            st.markdown(
                f'<span class="doc-type-chip">{row["doc_type"]}</span>',
                unsafe_allow_html=True,
            )
        with tc3:
            st.markdown("**📄 Source**")
            st.info(f"{row['source']}\nBBox: {row['bbox']}")
            st.markdown("**🔬 Confidence Breakdown**")
            st.markdown(
                f"OCR: `{row['ocr_confidence']:.0%}` · LLM: `{row['llm_confidence']:.0%}`"
            )
            st.markdown(f"Prompt: `{row['prompt_version']}`")
            st.markdown(f"Audit ID: `{row['audit_id']}`")

    st.markdown("---")
