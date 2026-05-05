"""CocoMind — RTI Export Page (Tier-1 Streamlit demo).

Generate DSC-signed evaluation reports for RTI Act 2005 responses.
JSON export is live; PDF export stub with DSC note.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audit.chain import write_record

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="RTI Export — CocoMind",
    page_icon="📄",
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
  .glass-card { background:rgba(30,41,59,.7); backdrop-filter:blur(12px); border:1px solid rgba(99,102,241,.25); border-radius:16px; padding:20px; margin-bottom:16px; box-shadow:0 8px 32px rgba(0,0,0,.3); }
  .dsc-badge { display:inline-block; background:rgba(99,102,241,.15); border:1px solid rgba(99,102,241,.3); border-radius:20px; padding:3px 12px; font-size:11px; color:#a5b4fc; }
  .badge-pass { display:inline-block; background:linear-gradient(135deg,#10b981,#059669); color:white; padding:3px 12px; border-radius:20px; font-weight:700; font-size:11px; }
  .badge-fail { display:inline-block; background:linear-gradient(135deg,#ef4444,#dc2626); color:white; padding:3px 12px; border-radius:20px; font-weight:700; font-size:11px; }
  .badge-ambiguous { display:inline-block; background:linear-gradient(135deg,#f59e0b,#d97706); color:white; padding:3px 12px; border-radius:20px; font-weight:700; font-size:11px; }
  .legal-box { background:rgba(15,23,42,.7); border:1px solid rgba(99,102,241,.2); border-radius:10px; padding:14px; font-size:12px; color:#64748b; line-height:1.8; }
  hr { border-color: rgba(99,102,241,.2)!important; }
  [data-testid="stAlert"] { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── Data ────────────────────────────────────────────────────────────────────

SAMPLE_VTMS = {
    "BID-A": {
        "name": "M/s Sharma Industrial Pvt Ltd",
        "overall": "ELIGIBLE",
        "rows": [
            {"criterion": "Average Annual Turnover", "verdict": "PASS", "value": "₹6,00,00,000", "threshold": "≥ ₹5,00,00,000", "source": "CA Certificate, Page 2", "confidence": 0.95, "audit_id": "AUD-001-A"},
            {"criterion": "Similar Works Experience", "verdict": "PASS", "value": "5 projects", "threshold": "≥ 3 projects", "source": "Experience Certificate, Page 1", "confidence": 0.92, "audit_id": "AUD-002-A"},
            {"criterion": "GST Registration", "verdict": "PASS", "value": "07AAACS1234A1ZH", "threshold": "Valid GSTIN", "source": "GST Certificate, Page 1", "confidence": 0.98, "audit_id": "AUD-003-A"},
            {"criterion": "EMD / Bank Guarantee", "verdict": "PASS", "value": "₹10,00,000 till 2026-08-15", "threshold": "≥ ₹5,00,000, ≥45 days", "source": "BG Document, Page 1", "confidence": 0.90, "audit_id": "AUD-004-A"},
            {"criterion": "Near Relations Declaration", "verdict": "PASS", "value": "No near relations in CRPF", "threshold": "Explicit declaration", "source": "Self Declaration, Page 1", "confidence": 0.93, "audit_id": "AUD-005-A"},
            {"criterion": "Integrity Pact", "verdict": "PASS", "value": "Signed CRPF template", "threshold": "CRPF standard template", "source": "Integrity Pact, Page 1", "confidence": 0.97, "audit_id": "AUD-006-A"},
        ],
    },
    "BID-B": {
        "name": "M/s Verma Tech Solutions",
        "overall": "INELIGIBLE",
        "rows": [
            {"criterion": "Average Annual Turnover", "verdict": "PASS", "value": "₹7,50,00,000", "threshold": "≥ ₹5,00,00,000", "source": "Audited FS, Page 4", "confidence": 0.93, "audit_id": "AUD-001-B"},
            {"criterion": "Similar Works Experience", "verdict": "FAIL", "value": "1 project", "threshold": "≥ 3 projects", "source": "Experience Certificate, Page 1", "confidence": 0.88, "audit_id": "AUD-002-B"},
            {"criterion": "GST Registration", "verdict": "PASS", "value": "09AABCV1234B1Z5", "threshold": "Valid GSTIN", "source": "GST Certificate, Page 1", "confidence": 0.97, "audit_id": "AUD-003-B"},
            {"criterion": "EMD / Bank Guarantee", "verdict": "PASS", "value": "₹8,00,000 till 2026-09-01", "threshold": "≥ ₹5,00,000, ≥45 days", "source": "BG Document, Page 1", "confidence": 0.91, "audit_id": "AUD-004-B"},
        ],
    },
    "BID-C": {
        "name": "M/s Gupta Equipment Co",
        "overall": "PENDING HITL",
        "rows": [
            {"criterion": "Average Annual Turnover", "verdict": "AMBIGUOUS", "value": "Conflict: ₹5.2Cr vs ₹4.8Cr", "threshold": "≥ ₹5,00,00,000", "source": "CA Certificate (photo), Page 1", "confidence": 0.55, "audit_id": "AUD-001-C"},
            {"criterion": "Near Relations Declaration", "verdict": "AMBIGUOUS", "value": "Keywords not found", "threshold": "Explicit declaration required", "source": "Self Declaration, Page 2", "confidence": 0.40, "audit_id": "AUD-002-C"},
        ],
    },
}

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 16px;">
      <div style="font-size:32px;">📄</div>
      <div style="font-size:16px; font-weight:700; color:#e2e8f0;">RTI Export</div>
      <div style="font-size:11px; color:#64748b;">RTI Act 2005 Compliance</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    bid_options = {f"{k} — {v['name']}": k for k, v in SAMPLE_VTMS.items()}
    selected_label = st.selectbox("🗂️ Select Bid for Export", list(bid_options.keys()))
    selected_bid = bid_options[selected_label]
    bid_data = SAMPLE_VTMS[selected_bid]
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
<h1 style="font-size:28px; font-weight:800; background:linear-gradient(135deg,#34d399,#6ee7b7);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin:0;">
  📄 RTI Export
</h1>
<div style="font-size:13px; color:#64748b; margin-top:4px; margin-bottom:20px;">
  Generate DSC-signed evaluation reports · RTI Act 2005 · CVC Circular 03/01/12 · GFR 2017
</div>
""", unsafe_allow_html=True)

# ─── Export Info ─────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="glass-card">
  <div style="font-size:15px; font-weight:700; color:#e2e8f0; margin-bottom:12px;">
    📦 Export Package: {selected_bid} — {bid_data['name']}
  </div>
  <div style="display:flex; gap:24px; flex-wrap:wrap; font-size:13px; color:#94a3b8;">
    <span>📊 <b>Criteria Evaluated:</b> {len(bid_data['rows'])}</span>
    <span>✅ <b>PASS:</b> {sum(1 for r in bid_data['rows'] if r['verdict']=='PASS')}</span>
    <span>❌ <b>FAIL:</b> {sum(1 for r in bid_data['rows'] if r['verdict']=='FAIL')}</span>
    <span>⚠️ <b>AMBIGUOUS:</b> {sum(1 for r in bid_data['rows'] if r['verdict']=='AMBIGUOUS')}</span>
    <span>⚖️ <b>Overall:</b> {bid_data['overall']}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Export Buttons ───────────────────────────────────────────────────────────

col_json, col_pdf = st.columns(2)

with col_json:
    st.markdown("""
    <div class="glass-card">
      <div style="font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;">
        📋 JSON Export (Machine-Readable)
      </div>
      <div style="font-size:12px; color:#94a3b8; line-height:1.6; margin-bottom:14px;">
        Full VTM with criterion-level provenance, audit IDs, confidence scores,
        source BBox references, and rule expressions. RTI-submittable.
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📥 Generate JSON Export", key="btn_json"):
        ts = datetime.now(timezone.utc).isoformat()
        export_data = {
            "export_metadata": {
                "generated_at": ts,
                "platform": "CocoMind Tier-1 Demo",
                "export_format": "RTI_VTM_JSON_v1",
                "legal_basis": ["RTI Act 2005", "GFR 2017 Rule 162", "CVC Circular 03/01/12"],
                "dsc_status": "DEV_CERT — Production uses eMudhra/Capricorn DSC",
                "audit_chain": "SQLite WAL + SHA-256 hash chain + daily Merkle root",
                "pii_handling": "Presidio + Indian recognisers — PII redacted before LLM; tokens stored locally",
            },
            "bid_id": selected_bid,
            "bid_name": bid_data["name"],
            "overall_verdict": bid_data["overall"],
            "criteria_count": len(bid_data["rows"]),
            "verdicts": bid_data["rows"],
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.json(export_data)

        st.download_button(
            label="⬇️ Download rti_export.json",
            data=json_str.encode("utf-8"),
            file_name=f"rti_export_{selected_bid}_{ts[:10]}.json",
            mime="application/json",
        )

        # Write audit record
        try:
            audit_id = write_record("RTI_EXPORT_GENERATED", {
                "bid_id": selected_bid,
                "bid_name": bid_data["name"],
                "format": "JSON",
                "generated_at": ts,
                "criteria_count": len(bid_data["rows"]),
            })
            st.success(f"✅ Export audit record written: `{audit_id}`")
        except Exception as e:
            st.info(f"ℹ️ Audit write skipped (DB not initialised): {e}")

with col_pdf:
    st.markdown("""
    <div class="glass-card">
      <div style="font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;">
        📝 PDF Export (Human-Readable)
      </div>
      <div style="font-size:12px; color:#94a3b8; line-height:1.6; margin-bottom:14px;">
        Formatted RTI response document with CRPF letterhead, VTM table,
        DSC signature block, and RFC-3161 timestamp. Suitable for PIO submission.
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📝 Generate PDF Export (Stub)", key="btn_pdf"):
        st.info(
            "📋 **PDF export with DSC signature** is available in production mode. "
            "Production flow: ReportLab renders VTM → officer signs with eMudhra PKCS#11 → "
            "RFC-3161 timestamp from eMudhra TSA → audit record written → PDF delivered."
        )

        # Show what the PDF would contain
        st.markdown("**PDF would contain:**")
        pdf_sections = [
            "🏛️ CRPF letterhead with NIT reference number",
            "📋 Bid identification and bidder details",
            "📊 VTM table: criterion × verdict × source × expression",
            f"⚖️ Overall verdict: {bid_data['overall']}",
            "🔒 Presidio redaction audit: entity types + count (not values)",
            "📝 HITL decisions (if any) with officer ID + justification",
            "🔐 DSC signature block (X.509 cert details)",
            "⏱️ RFC-3161 TSA timestamp",
            "🔗 Audit chain Merkle root reference",
        ]
        for section in pdf_sections:
            st.markdown(f"- {section}")

# ─── Legal Disclosure ─────────────────────────────────────────────────────────

st.divider()
st.markdown("""
<div class="legal-box">
  <b style="color:#a5b4fc;">📚 Legal Framework for This Export</b><br>
  <b>RTI Act 2005 §2(f):</b> This export constitutes "information" as defined — all evaluation records are available for inspection.<br>
  <b>GFR 2017 Rule 162:</b> Transparency in tender evaluation; complete VTM records maintained.<br>
  <b>CVC Circular 03/01/12:</b> Systematic, objective evaluation with documented criteria.<br>
  <b>CAG Guidelines:</b> Audit trail sufficient for re-derivation of all verdicts from source documents.<br>
  <b>DPDPA 2023 §4:</b> PII redacted before LLM; only typed normalised values in this export; no raw bidder PII.<br>
  <br>
  <b>Reproduction:</b> Every verdict in this export can be independently re-derived by running
  <code>verify_chain()</code> + <code>export_for_rti(bid_id)</code> from the audit store.
  The rule engine is deterministic pure Python — same inputs yield identical verdicts.
</div>
""", unsafe_allow_html=True)
