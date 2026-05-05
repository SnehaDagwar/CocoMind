"""CocoMind — Tier-1 Demo Home Page.

Multi-page Streamlit app entrypoint. Run with:
    streamlit run ui-streamlit/Home.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CocoMind — CRPF Tender Evaluation",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS (applied once on the app root) ────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Deep navy background */
  .stApp {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a0f1e 100%);
    color: #e2e8f0;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #1a1f3a 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.2);
  }

  /* Glassmorphism cards */
  .glass-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }

  /* Verdict badges */
  .badge-pass {
    display: inline-block;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.5px;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
  }
  .badge-fail {
    display: inline-block;
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.5px;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
  }
  .badge-ambiguous {
    display: inline-block;
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.5px;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
  }

  /* Metric cards */
  .metric-card {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
  }
  .metric-value {
    font-size: 36px;
    font-weight: 800;
    color: #e2e8f0;
    line-height: 1;
  }
  .metric-label {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }

  /* Hero gradient text */
  .hero-title {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 42px;
    font-weight: 800;
    margin: 0;
    line-height: 1.2;
  }

  /* Pipeline stage chips */
  .stage-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
    color: #a5b4fc;
    margin: 3px;
  }

  /* Override Streamlit defaults */
  .stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.2s ease;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
  }
  .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
  }

  /* Selectbox + multiselect */
  .stSelectbox > div > div {
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
  }

  /* Expander headers */
  [data-testid="stExpander"] {
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 10px !important;
  }

  /* Info/Warning/Error/Success */
  [data-testid="stAlert"] {
    border-radius: 12px;
  }

  /* Divider */
  hr {
    border-color: rgba(99, 102, 241, 0.2) !important;
  }

  /* Progress bar */
  [data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
    border-radius: 10px !important;
  }

  /* Table */
  [data-testid="stTable"] {
    border-radius: 12px;
    overflow: hidden;
  }

  .tier-badge {
    display: inline-block;
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid rgba(245, 158, 11, 0.5);
    color: #fbbf24;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
  }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 12px 0;">
      <div style="font-size:48px; margin-bottom:8px;">🧠</div>
      <div style="font-size:22px; font-weight:800; background: linear-gradient(135deg, #6366f1, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
        CocoMind
      </div>
      <div style="font-size:11px; color:#64748b; letter-spacing:1px; margin-top:2px;">
        CRPF TENDER EVALUATION
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; font-weight:600;">
      Navigation
    </div>
    """, unsafe_allow_html=True)

    st.page_link("Home.py", label="🏠  Home", icon=None)
    st.page_link("pages/1_Dashboard.py", label="📊  Dashboard", icon=None)
    st.page_link("pages/2_HITL_Review.py", label="🔍  HITL Review", icon=None)
    st.page_link("pages/3_RTI_Export.py", label="📄  RTI Export", icon=None)
    st.page_link("pages/4_Audit_Chain.py", label="🔐  Audit Chain", icon=None)

    st.divider()

    st.markdown("""
    <div style="background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3);
      border-radius: 10px; padding: 12px; font-size: 12px; color: #fbbf24;">
      <b>⚠️ Tier-1 Demo</b><br>
      <span style="color:#94a3b8;">Synthetic data only.<br>
      DSC = dev certificate.</span>
    </div>
    """, unsafe_allow_html=True)

# ─── Home Content ─────────────────────────────────────────────────────────────

st.markdown('<h1 class="hero-title">CocoMind</h1>', unsafe_allow_html=True)
st.markdown("""
<div style="font-size: 18px; color: #94a3b8; margin-top: 4px; margin-bottom: 24px;">
  AI-Assisted CRPF Tender Evaluation Platform &nbsp;·&nbsp;
  <span class="tier-badge">TIER-1 DEMO</span>
</div>
""", unsafe_allow_html=True)

# ─── What CocoMind Does ───────────────────────────────────────────────────────

col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("""
    <div class="glass-card">
      <div style="font-size:16px; font-weight:700; color:#e2e8f0; margin-bottom:12px;">
        🎯 What CocoMind Does
      </div>
      <div style="font-size:14px; color:#94a3b8; line-height:1.7;">
        CocoMind reads a CRPF tender (NIT) + bidder submissions and produces
        <b style="color:#a5b4fc;">criterion-by-criterion, source-pinned,
        RTI-auditable eligibility verdicts</b> — with a hard human-in-the-loop path
        for ambiguous cases and a legally-signed audit trail.
      </div>
      <div style="margin-top: 16px; font-size:13px; color:#94a3b8;">
        <b style="color:#e2e8f0;">Hard non-negotiables:</b>
        <ul style="margin:8px 0; padding-left:20px; line-height:2;">
          <li>LLM <b>extracts</b> — Python rule engine <b>decides</b> (never the LLM)</li>
          <li>No silent disqualification — low confidence → HITL queue</li>
          <li>Cryptographic audit chain + daily Merkle root</li>
          <li>Presidio PII redaction before every LLM call</li>
          <li>6 RBAC personas with least-privilege enforcement</li>
        </ul>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="glass-card">
      <div style="font-size:16px; font-weight:700; color:#e2e8f0; margin-bottom:12px;">
        🏗️ 6-Stage Pipeline
      </div>
    """, unsafe_allow_html=True)

    stages = [
        ("📥", "Ingest", "PDF/DOCX/IMG/ZIP"),
        ("🔍", "OCR", "Azure DI + bbox"),
        ("🔒", "Redact", "Presidio + Indian PII"),
        ("🧩", "Chunk + Embed", "BGE-M3 + BM25"),
        ("🔎", "Hybrid Retrieve", "RRF Fusion"),
        ("⚖️", "Rule Engine", "Pure Python verdict"),
    ]

    for icon, name, desc in stages:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; padding:8px 0;
          border-bottom:1px solid rgba(99,102,241,0.1);">
          <div style="font-size:20px; width:30px; text-align:center;">{icon}</div>
          <div>
            <div style="font-size:13px; font-weight:600; color:#e2e8f0;">{name}</div>
            <div style="font-size:11px; color:#64748b;">{desc}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ─── Demo Bids Summary ────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="font-size:18px; font-weight:700; color:#e2e8f0; margin-bottom:16px;">
  🗂️ 3 Demo Bid Packages
</div>
""", unsafe_allow_html=True)

bid_cols = st.columns(3)

bid_info = [
    {
        "icon": "✅",
        "title": "BID-A — PASS",
        "company": "M/s Sharma Industrial Pvt Ltd",
        "color": "#10b981",
        "glow": "rgba(16,185,129,0.2)",
        "desc": "Golden path — typed PDFs, all 6 criteria met cleanly. Demonstrates clean evaluation flow.",
        "verdicts": {"PASS": 6, "FAIL": 0, "AMBIGUOUS": 0},
    },
    {
        "icon": "❌",
        "title": "BID-B — FAIL",
        "company": "M/s Verma Tech Solutions",
        "color": "#ef4444",
        "glow": "rgba(239,68,68,0.2)",
        "desc": "Similar Works Experience: only 1 project submitted vs. ≥3 required. Rule engine cites evidence.",
        "verdicts": {"PASS": 3, "FAIL": 1, "AMBIGUOUS": 0},
    },
    {
        "icon": "⚠️",
        "title": "BID-C — HITL",
        "company": "M/s Gupta Equipment Co",
        "color": "#f59e0b",
        "glow": "rgba(245,158,11,0.2)",
        "desc": "Handwritten CA cert conflict + ambiguous near-relations + Aadhaar redacted + prompt injection attempt.",
        "verdicts": {"PASS": 0, "FAIL": 0, "AMBIGUOUS": 2},
    },
]

for col, bid in zip(bid_cols, bid_info):
    with col:
        v = bid["verdicts"]
        st.markdown(f"""
        <div style="background: rgba(30,41,59,0.7); border: 1px solid {bid['color']}40;
          border-radius: 16px; padding: 20px; height:100%;
          box-shadow: 0 4px 24px {bid['glow']};">
          <div style="font-size:24px; margin-bottom:4px;">{bid['icon']}</div>
          <div style="font-size:15px; font-weight:700; color:{bid['color']};">
            {bid['title']}
          </div>
          <div style="font-size:11px; color:#64748b; margin-bottom:10px;">
            {bid['company']}
          </div>
          <div style="font-size:12px; color:#94a3b8; line-height:1.6; margin-bottom:14px;">
            {bid['desc']}
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <span class="badge-pass">{v['PASS']} PASS</span>
            <span class="badge-fail">{v['FAIL']} FAIL</span>
            <span class="badge-ambiguous">{v['AMBIGUOUS']} AMBIGUOUS</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─── Compliance Footer ────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="text-align:center; font-size:12px; color:#475569; padding:8px;">
  <b>Legal Framework:</b> GFR 2017 · RTI Act 2005 · CVC Circular 03/01/12 · CAG Guidelines · DPDPA 2023 · IT Act §43A
  &nbsp;·&nbsp;
  <b>Security:</b> DPDPA 2023 · Presidio PII Redaction · AES-256 · TLS 1.3 · RBAC (6 personas)
</div>
""", unsafe_allow_html=True)
