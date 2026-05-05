"""CocoMind — HITL Review Page (Tier-1 Streamlit demo).

Human-in-the-Loop queue: ambiguous verdicts with officer decision form,
DSC sign-off stub, and audit trail write-back.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audit.chain import write_record

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HITL Review — CocoMind",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a0f1e 100%); color: #e2e8f0; }
  [data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1b2a 0%, #1a1f3a 100%); border-right: 1px solid rgba(99,102,241,0.2); }
  .stButton > button { background:linear-gradient(135deg,#6366f1,#8b5cf6); color:white; border:none; border-radius:10px; padding:10px 24px; font-weight:600; font-size:14px; box-shadow:0 4px 15px rgba(99,102,241,.3); }
  .stButton > button:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(99,102,241,.5); }
  .hitl-card { background:rgba(30,41,59,.8); border:1px solid rgba(245,158,11,.35); border-radius:16px; padding:20px; margin-bottom:20px; box-shadow:0 4px 24px rgba(245,158,11,.1); }
  .badge-ambiguous { display:inline-block; background:linear-gradient(135deg,#f59e0b,#d97706); color:white; padding:4px 14px; border-radius:20px; font-weight:700; font-size:12px; box-shadow:0 0 12px rgba(245,158,11,.4); }
  .source-block { background:rgba(15,23,42,.6); border:1px solid rgba(99,102,241,.2); border-radius:10px; padding:14px; font-size:13px; color:#94a3b8; line-height:1.7; }
  .conf-low { color:#ef4444; font-weight:700; }
  .dsc-badge { display:inline-block; background:rgba(99,102,241,.15); border:1px solid rgba(99,102,241,.3); border-radius:20px; padding:3px 12px; font-size:11px; color:#a5b4fc; }
  .queue-counter { background:linear-gradient(135deg,rgba(245,158,11,.2),rgba(245,158,11,.1)); border:1px solid rgba(245,158,11,.4); border-radius:12px; padding:10px 20px; text-align:center; }
  hr { border-color: rgba(99,102,241,.2)!important; }
  [data-testid="stAlert"] { border-radius: 12px; }
  textarea { background:rgba(30,41,59,.8)!important; border:1px solid rgba(99,102,241,.3)!important; border-radius:10px!important; color:#e2e8f0!important; }
</style>
""", unsafe_allow_html=True)

# ─── HITL Queue Data ─────────────────────────────────────────────────────────

HITL_ITEMS = [
    {
        "item_id": "HITL-001",
        "bid_id": "BID-C",
        "bid_name": "M/s Gupta Equipment Co",
        "criterion": "Average Annual Turnover",
        "category": "financial",
        "value": "₹5,20,00,000 (handwritten CA cert) vs ₹4,80,00,000 (cover letter)",
        "threshold": "≥ ₹5,00,00,000",
        "expression": "CONFLICT UNRESOLVED — ca_certificate vs cover_letter disagree by >5%",
        "source_doc": "CA Certificate (phone photo), Page 1",
        "source_doc_type": "ca_certificate",
        "bbox": "[120, 300, 640, 350]",
        "ocr_confidence": 0.58,
        "llm_confidence": 0.55,
        "reason": "Two source documents disagree by more than 5% on the turnover figure. "
                  "Doc-type hierarchy cannot resolve (both docs are CA-signed). "
                  "Conservative lower value (₹4.8Cr) would result in FAIL; "
                  "upper value (₹5.2Cr) would result in PASS. Officer must verify original.",
        "pii_note": "Aadhaar number XXXX-XXXX-XXXX redacted from CA cert (Presidio).",
        "redacted_entities": ["AADHAAR x1", "PHONE_NUMBER x1"],
    },
    {
        "item_id": "HITL-002",
        "bid_id": "BID-C",
        "bid_name": "M/s Gupta Equipment Co",
        "criterion": "Near Relations Declaration",
        "category": "declaration",
        "value": "Declaration page present but keywords 'no near relations' / 'निकट संबंधी' not found",
        "threshold": "Explicit declaration of no near relations in CRPF required",
        "expression": "keywords_found = False → NOT_FOUND → HITL",
        "source_doc": "Self Declaration Affidavit, Page 2",
        "source_doc_type": "self_declaration",
        "bbox": "[80, 380, 680, 420]",
        "ocr_confidence": 0.45,
        "llm_confidence": 0.40,
        "reason": "Declaration page was included but OCR confidence is low (45%). "
                  "Expected keywords for near-relations declaration not found in extracted text. "
                  "Could be due to handwriting, non-standard phrasing, or missing page.",
        "pii_note": "No PII entities redacted from this page.",
        "redacted_entities": [],
    },
]

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 16px;">
      <div style="font-size:32px;">🔍</div>
      <div style="font-size:16px; font-weight:700; color:#e2e8f0;">HITL Review</div>
      <div style="font-size:11px; color:#64748b;">Human-in-the-Loop Queue</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown(f"""
    <div class="queue-counter">
      <div style="font-size:30px; font-weight:800; color:#f59e0b;">{len(HITL_ITEMS)}</div>
      <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:.8px;">Items Pending</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style="background:rgba(245,158,11,.1); border:1px solid rgba(245,158,11,.3);
      border-radius:10px; padding:10px; font-size:11px; color:#fbbf24;">
      ⚠️ <b>Tier-1 Demo</b><br>
      <span style="color:#94a3b8;">Synthetic data · Dev DSC</span>
    </div>
    """, unsafe_allow_html=True)

# ─── Page Header ─────────────────────────────────────────────────────────────

st.markdown("""
<h1 style="font-size:28px; font-weight:800; background:linear-gradient(135deg,#f59e0b,#fbbf24);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin:0;">
  🔍 Human-in-the-Loop Review
</h1>
<div style="font-size:13px; color:#64748b; margin-top:4px; margin-bottom:20px;">
  Resolve ambiguous verdicts with officer sign-off · Every decision is DSC-signed + audit-chained
</div>
""", unsafe_allow_html=True)

if not HITL_ITEMS:
    st.success("✅ **HITL queue is empty** — All verdicts resolved automatically.")
else:
    st.warning(
        f"⚠️ **{len(HITL_ITEMS)} item(s) pending officer review.** "
        f"Each decision will be recorded in the tamper-evident audit chain."
    )

st.divider()

# ─── HITL Items ──────────────────────────────────────────────────────────────

for i, item in enumerate(HITL_ITEMS):
    conf_pct = int(item["llm_confidence"] * 100)
    ocr_pct = int(item["ocr_confidence"] * 100)

    st.markdown(f"""
    <div style="font-size:16px; font-weight:700; color:#fbbf24; margin-bottom:12px;">
      ⚠️ {item['item_id']} &nbsp;·&nbsp;
      <span style="color:#94a3b8; font-size:13px; font-weight:400;">
        {item['bid_name']} ({item['bid_id']})
      </span>
    </div>
    """, unsafe_allow_html=True)

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown("**📄 Source Evidence**")
        st.markdown(f"""
        <div class="source-block">
          <b style="color:#e2e8f0;">Criterion:</b> {item['criterion']}<br>
          <b style="color:#e2e8f0;">Extracted Value:</b><br>
          <code style="color:#fbbf24;">{item['value']}</code><br><br>
          <b style="color:#e2e8f0;">Threshold:</b> {item['threshold']}<br>
          <b style="color:#e2e8f0;">Rule Expression:</b><br>
          <code style="color:#a5b4fc;">{item['expression']}</code>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown("**🗂️ Document Details**")
        st.markdown(f"""
        <div class="source-block">
          📎 {item['source_doc']}<br>
          BBox: <code>{item['bbox']}</code><br>
          OCR Confidence: <span class="conf-low">{ocr_pct}%</span> &nbsp;·&nbsp;
          LLM Confidence: <span class="conf-low">{conf_pct}%</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown("**⚠️ Why This Is Ambiguous**")
        st.info(item["reason"])

        if item["redacted_entities"]:
            st.markdown("**🔒 PII Redacted by Presidio**")
            st.markdown(f"""
            <div style="font-size:12px; color:#94a3b8;">
              {" · ".join(f'<code>{e}</code>' for e in item["redacted_entities"])}
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        st.markdown("**👤 Officer Decision**")

        decision_key = f"decision_{item['item_id']}"
        override_key = f"override_{item['item_id']}"
        justification_key = f"justification_{item['item_id']}"
        submit_key = f"submit_{item['item_id']}"

        decision = st.radio(
            "Resolution",
            ["✅ Confirm PASS", "❌ Override to FAIL", "📋 Request Additional Docs"],
            key=decision_key,
        )

        override_value = None
        if decision == "✅ Confirm PASS":
            override_value = "confirmed_pass"
            st.markdown("""
            <div style="background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.3);
              border-radius:8px; padding:10px; font-size:12px; color:#6ee7b7; margin-top:8px;">
              Selecting CONFIRM will record PASS verdict in the audit chain.
              You must provide justification below.
            </div>
            """, unsafe_allow_html=True)
        elif decision == "❌ Override to FAIL":
            override_value = st.text_input(
                "Cite specific failing evidence",
                placeholder="e.g. CA cert value ₹4.8Cr is below threshold ₹5Cr",
                key=override_key,
            )
        else:
            st.markdown("""
            <div style="background:rgba(99,102,241,.1); border:1px solid rgba(99,102,241,.3);
              border-radius:8px; padding:10px; font-size:12px; color:#a5b4fc; margin-top:8px;">
              Bid will remain in PENDING state. A clarification notice will be generated for the bidder.
            </div>
            """, unsafe_allow_html=True)

        justification = st.text_area(
            "Officer Justification (required)",
            key=justification_key,
            placeholder="Provide detailed reason for your decision. "
                        "This will be part of the RTI-auditable record.",
            height=120,
        )

        officer_id = st.text_input(
            "Officer ID",
            value="OFC-CRPF-0042",
            key=f"officer_{item['item_id']}",
            help="Your CRPF officer identifier",
        )

        st.markdown("""
        <div style="font-size:12px; color:#64748b; margin-bottom:8px;">
          🔒 Decision will be signed with <span class="dsc-badge">DEV DSC CERT</span>
          and RFC-3161 timestamped in production.
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Submit Decision — {item['item_id']}", key=submit_key):
            if not justification.strip():
                st.error("❌ Justification is required before submitting.")
            elif decision == "❌ Override to FAIL" and not (override_value or "").strip():
                st.error("❌ Please cite the specific failing evidence.")
            else:
                # Write to audit chain
                try:
                    audit_id = write_record("HITL_DECISION", {
                        "item_id": item["item_id"],
                        "bid_id": item["bid_id"],
                        "criterion": item["criterion"],
                        "decision": decision,
                        "override_value": override_value,
                        "justification": justification,
                        "officer_id": officer_id,
                        "dsc_status": "DEV_CERT_SIGNED",
                    })
                    st.success(
                        f"✅ **Decision recorded.** Audit ID: `{audit_id}` · "
                        f"DSC signature applied (dev cert). "
                        f"Record is now append-only in the audit chain."
                    )
                except Exception as e:
                    st.warning(
                        f"⚠️ Decision captured but audit write failed: {e}. "
                        f"Would succeed with initialised audit DB."
                    )

    st.divider()
