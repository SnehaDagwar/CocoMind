"""CocoMind — Verdict Dashboard (Tier-1 Streamlit demo).

Bid selector, per-bid criterion table with colored verdict badges,
expandable rows showing full provenance trace.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audit.chain import verify_chain, get_all_records, compute_daily_root
from src.models.verdicts import VerdictStatus


# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CocoMind — CRPF Tender Evaluation",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .verdict-pass { 
        background: #22c55e; color: white; padding: 4px 12px; 
        border-radius: 12px; font-weight: 600; font-size: 13px; 
    }
    .verdict-fail { 
        background: #ef4444; color: white; padding: 4px 12px; 
        border-radius: 12px; font-weight: 600; font-size: 13px; 
    }
    .verdict-ambiguous { 
        background: #f59e0b; color: white; padding: 4px 12px; 
        border-radius: 12px; font-weight: 600; font-size: 13px; 
    }
    .metric-card {
        background: #1e293b; padding: 16px; border-radius: 12px;
        border: 1px solid #334155; text-align: center;
    }
    .metric-value { font-size: 32px; font-weight: 700; color: #e2e8f0; }
    .metric-label { font-size: 13px; color: #94a3b8; margin-top: 4px; }
    .stApp { background-color: #0f172a; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.image("https://img.icons8.com/fluency/96/brain.png", width=64)
st.sidebar.title("🧠 CocoMind")
st.sidebar.caption("CRPF Tender Evaluation Platform")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🔍 HITL Review", "📄 RTI Export", "🔐 Audit Chain"],
    index=0,
)

st.sidebar.divider()
st.sidebar.info(
    "**Tier-1 Demo** — Synthetic data only. "
    "DSC signatures use dev certificates."
)

# ─── Sample data (for demo before pipeline is connected) ─────────────────────

SAMPLE_VTMS = {
    "BID-A": {
        "name": "M/s Sharma Industrial Pvt Ltd",
        "rows": [
            {
                "criterion": "Average Annual Turnover",
                "category": "financial",
                "mandatory": True,
                "verdict": "PASS",
                "value": "₹6,00,00,000",
                "threshold": "≥ ₹5,00,00,000",
                "expression": "60000000 >= 50000000",
                "source": "CA Certificate, Page 2",
                "confidence": 0.95,
                "doc_type": "ca_certificate",
            },
            {
                "criterion": "Similar Works Experience",
                "category": "technical",
                "mandatory": True,
                "verdict": "PASS",
                "value": "5 projects",
                "threshold": "≥ 3 projects",
                "expression": "5 >= 3",
                "source": "Experience Certificate, Page 1",
                "confidence": 0.92,
                "doc_type": "experience_cert",
            },
            {
                "criterion": "GST Registration",
                "category": "compliance",
                "mandatory": True,
                "verdict": "PASS",
                "value": "Valid (07AAACS1234A1ZH)",
                "threshold": "Valid registration",
                "expression": "bool(True) = True",
                "source": "GST Certificate, Page 1",
                "confidence": 0.98,
                "doc_type": "gst_cert",
            },
            {
                "criterion": "EMD / Bank Guarantee",
                "category": "financial",
                "mandatory": True,
                "verdict": "PASS",
                "value": "₹10,00,000 valid till 2026-08-15",
                "threshold": "≥ 2% of NIT value, ≥45 days validity",
                "expression": "BG ₹10,00,000 ≥ ₹5,00,000 and validity OK",
                "source": "BG Document, Page 1",
                "confidence": 0.90,
                "doc_type": "emd_document",
            },
        ],
    },
    "BID-B": {
        "name": "M/s Verma Tech Solutions",
        "rows": [
            {
                "criterion": "Average Annual Turnover",
                "category": "financial",
                "mandatory": True,
                "verdict": "PASS",
                "value": "₹7,50,00,000",
                "threshold": "≥ ₹5,00,00,000",
                "expression": "75000000 >= 50000000",
                "source": "Audited Financial Statement, Page 4",
                "confidence": 0.93,
                "doc_type": "audited_financial_statement",
            },
            {
                "criterion": "Similar Works Experience",
                "category": "technical",
                "mandatory": True,
                "verdict": "FAIL",
                "value": "1 project",
                "threshold": "≥ 3 projects",
                "expression": "1 >= 3 → False",
                "source": "Experience Certificate, Page 1",
                "confidence": 0.88,
                "doc_type": "experience_cert",
            },
            {
                "criterion": "GST Registration",
                "category": "compliance",
                "mandatory": True,
                "verdict": "PASS",
                "value": "Valid",
                "threshold": "Valid registration",
                "expression": "bool(True) = True",
                "source": "GST Certificate, Page 1",
                "confidence": 0.97,
                "doc_type": "gst_cert",
            },
        ],
    },
    "BID-C": {
        "name": "M/s Gupta Equipment Co",
        "rows": [
            {
                "criterion": "Average Annual Turnover",
                "category": "financial",
                "mandatory": True,
                "verdict": "AMBIGUOUS",
                "value": "₹5,20,00,000 (from handwritten CA cert) vs ₹4,80,00,000 (cover letter)",
                "threshold": "≥ ₹5,00,00,000",
                "expression": "Conflict unresolved — handwritten CA cert + cover letter disagree",
                "source": "CA Certificate (photo), Page 1",
                "confidence": 0.55,
                "doc_type": "ca_certificate",
            },
            {
                "criterion": "Near Relations Declaration",
                "category": "declaration",
                "mandatory": True,
                "verdict": "AMBIGUOUS",
                "value": "Declaration present but unclear",
                "threshold": "Must declare no near relations",
                "expression": "Keywords not found — needs HITL review",
                "source": "Self Declaration, Page 2",
                "confidence": 0.40,
                "doc_type": "self_declaration",
            },
        ],
    },
}


# ─── Dashboard page ──────────────────────────────────────────────────────────

if page == "📊 Dashboard":
    st.title("📊 Tender Evaluation Dashboard")
    st.caption("Criterion-by-criterion, source-pinned eligibility verdicts")

    # Bid selector
    bid_options = {f"{k} — {v['name']}": k for k, v in SAMPLE_VTMS.items()}
    selected_label = st.selectbox("Select Bid", list(bid_options.keys()))
    selected_bid = bid_options[selected_label]
    bid_data = SAMPLE_VTMS[selected_bid]

    st.divider()

    # Summary metrics
    rows = bid_data["rows"]
    pass_count = sum(1 for r in rows if r["verdict"] == "PASS")
    fail_count = sum(1 for r in rows if r["verdict"] == "FAIL")
    ambiguous_count = sum(1 for r in rows if r["verdict"] == "AMBIGUOUS")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Criteria", len(rows))
    with col2:
        st.metric("✅ PASS", pass_count)
    with col3:
        st.metric("❌ FAIL", fail_count)
    with col4:
        st.metric("⚠️ AMBIGUOUS", ambiguous_count)

    # Overall verdict
    if fail_count > 0:
        st.error(f"**Overall: INELIGIBLE** — {fail_count} mandatory criterion(s) failed")
    elif ambiguous_count > 0:
        st.warning(f"**Overall: PENDING HITL** — {ambiguous_count} criterion(s) need manual review")
    else:
        st.success("**Overall: ELIGIBLE** — All mandatory criteria passed")

    st.divider()

    # Criterion table with expandable trace
    for i, row in enumerate(rows):
        verdict = row["verdict"]
        badge_class = f"verdict-{verdict.lower()}"

        col_name, col_cat, col_verdict, col_conf = st.columns([3, 1.5, 1, 1])

        with col_name:
            st.write(f"**{row['criterion']}**")
        with col_cat:
            mandatory_badge = "🔴 Mandatory" if row.get("mandatory", True) else "🟡 Optional"
            st.caption(f"{row['category'].title()} · {mandatory_badge}")
        with col_verdict:
            st.markdown(f'<span class="{badge_class}">{verdict}</span>', unsafe_allow_html=True)
        with col_conf:
            st.progress(row["confidence"])

        with st.expander(f"📋 Full Trace — {row['criterion']}", expanded=False):
            trace_col1, trace_col2 = st.columns(2)
            with trace_col1:
                st.write("**Extracted Value:**", row["value"])
                st.write("**Threshold:**", row["threshold"])
                st.write("**Rule Expression:**", f"`{row['expression']}`")
            with trace_col2:
                st.write("**Source:**", row["source"])
                st.write("**Doc Type:**", row["doc_type"])
                st.write("**Confidence:**", f"{row['confidence']:.0%}")

        st.divider()


# ─── HITL Review page ────────────────────────────────────────────────────────

elif page == "🔍 HITL Review":
    st.title("🔍 Human-in-the-Loop Review")
    st.caption("Resolve ambiguous verdicts with officer sign-off")

    # Filter for AMBIGUOUS items
    hitl_items = []
    for bid_id, bid_data in SAMPLE_VTMS.items():
        for row in bid_data["rows"]:
            if row["verdict"] == "AMBIGUOUS":
                hitl_items.append({"bid_id": bid_id, "bid_name": bid_data["name"], **row})

    if not hitl_items:
        st.success("✅ No items pending HITL review")
    else:
        st.warning(f"⚠️ {len(hitl_items)} item(s) pending review")

        for i, item in enumerate(hitl_items):
            st.subheader(f"{item['bid_name']} — {item['criterion']}")

            col_left, col_right = st.columns(2)

            with col_left:
                st.write("**📄 Source Document**")
                st.info(f"Document: {item['source']}\nDoc Type: {item['doc_type']}")
                st.write(f"**Extracted Value:** {item['value']}")
                st.write(f"**Confidence:** {item['confidence']:.0%}")
                st.write(f"**Reason:** {item['expression']}")

            with col_right:
                st.write("**👤 Officer Decision**")
                decision = st.radio(
                    "Decision",
                    ["Confirm", "Override", "Not Provided"],
                    key=f"decision_{i}",
                )

                override_value = None
                if decision == "Override":
                    override_value = st.text_input(
                        "Override Value",
                        key=f"override_{i}",
                    )

                justification = st.text_area(
                    "Justification (required)",
                    key=f"justification_{i}",
                    placeholder="Provide reason for your decision...",
                )

                if st.button("Submit Decision", key=f"submit_{i}"):
                    if not justification:
                        st.error("Justification is required")
                    else:
                        st.success(
                            f"✅ Decision recorded: {decision}. "
                            f"Audit record created. (DSC sign-off in production)"
                        )

            st.divider()


# ─── RTI Export page ─────────────────────────────────────────────────────────

elif page == "📄 RTI Export":
    st.title("📄 RTI Export")
    st.caption("Generate DSC-signed evaluation reports for RTI responses")

    bid_options = {f"{k} — {v['name']}": k for k, v in SAMPLE_VTMS.items()}
    selected_label = st.selectbox("Select Bid for Export", list(bid_options.keys()))
    selected_bid = bid_options[selected_label]
    bid_data = SAMPLE_VTMS[selected_bid]

    if st.button("Generate RTI Export"):
        export_data = {
            "bid_id": selected_bid,
            "bid_name": bid_data["name"],
            "criteria_evaluated": len(bid_data["rows"]),
            "verdicts": bid_data["rows"],
        }

        st.json(export_data)

        st.download_button(
            label="📥 Download JSON Export",
            data=json.dumps(export_data, indent=2),
            file_name=f"rti_export_{selected_bid}.json",
            mime="application/json",
        )

        st.info("📝 PDF export with DSC signature available in production mode.")


# ─── Audit Chain page ────────────────────────────────────────────────────────

elif page == "🔐 Audit Chain":
    st.title("🔐 Audit Chain Verification")
    st.caption("SHA-256 hash chain with daily Merkle root anchoring")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Verify Chain Integrity"):
            try:
                is_valid = verify_chain()
                if is_valid:
                    st.success("✅ **Chain INTACT** — All hashes verified successfully")
                else:
                    st.error("❌ **Chain TAMPERED** — Hash mismatch detected!")
            except Exception as e:
                st.warning(f"⚠️ Audit DB not initialised yet: {e}")

    with col2:
        if st.button("📊 Compute Daily Merkle Root"):
            try:
                root = compute_daily_root()
                st.code(f"Merkle Root: {root}", language="text")
            except Exception as e:
                st.warning(f"⚠️ {e}")

    st.divider()

    if st.button("📋 Show Audit Records"):
        try:
            records = get_all_records()
            if records:
                for r in records[-10:]:  # Show last 10
                    with st.expander(f"🔗 {r['event_type']} — {r['ts_utc'][:19]}"):
                        st.write(f"**Record ID:** `{r['record_id']}`")
                        st.write(f"**Hash:** `{r['record_hash'][:16]}...`")
                        st.write(f"**Prev Hash:** `{r['prev_hash'][:16]}...`")
                        st.json(r["payload"])
            else:
                st.info("No audit records yet. Run the pipeline to generate records.")
        except Exception as e:
            st.warning(f"⚠️ {e}")
