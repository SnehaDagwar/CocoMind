"""CocoMind — Audit Chain Verification Page (Tier-1 Streamlit demo).

SHA-256 hash chain with daily Merkle root anchoring.
Demonstrates tamper-evidence and RTI-defensibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audit.chain import compute_daily_root, get_all_records, verify_chain

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Audit Chain — CocoMind",
    page_icon="🔐",
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
  .chain-block { background:rgba(15,23,42,.8); border:1px solid rgba(99,102,241,.3); border-radius:10px; padding:14px; margin-bottom:8px; font-family:'JetBrains Mono', 'Courier New', monospace; font-size:11px; }
  .chain-hash { color:#a5b4fc; word-break:break-all; }
  .chain-event { color:#fbbf24; font-weight:600; }
  .chain-ts { color:#64748b; }
  .chain-arrow { text-align:center; color:rgba(99,102,241,.4); font-size:18px; margin:2px 0; }
  .integrity-ok { background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.4); border-radius:12px; padding:14px; text-align:center; }
  .integrity-fail { background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.4); border-radius:12px; padding:14px; text-align:center; }
  .merkle-box { background:rgba(99,102,241,.1); border:1px solid rgba(99,102,241,.4); border-radius:12px; padding:16px; font-family:'Courier New', monospace; font-size:12px; color:#a5b4fc; word-break:break-all; }
  .stat-chip { display:inline-block; background:rgba(30,41,59,.8); border:1px solid rgba(99,102,241,.3); border-radius:20px; padding:4px 14px; font-size:12px; color:#94a3b8; margin:3px; }
  hr { border-color: rgba(99,102,241,.2)!important; }
  [data-testid="stAlert"] { border-radius: 12px; }
  [data-testid="stExpander"] { background:rgba(30,41,59,.5)!important; border:1px solid rgba(99,102,241,.2)!important; border-radius:10px!important; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 16px;">
      <div style="font-size:32px;">🔐</div>
      <div style="font-size:16px; font-weight:700; color:#e2e8f0;">Audit Chain</div>
      <div style="font-size:11px; color:#64748b;">Tamper-Evident Ledger</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div class="glass-card">
      <div style="font-size:13px; font-weight:600; color:#a5b4fc; margin-bottom:10px;">🔒 Security Model</div>
      <div style="font-size:12px; color:#94a3b8; line-height:1.8;">
        ✔ SHA-256 hash chain<br>
        ✔ Daily Merkle root<br>
        ✔ SQLite WAL mode<br>
        ✔ Append-only triggers<br>
        ✔ DSC on HITL decisions<br>
        ✔ RFC-3161 TSA (prod)
      </div>
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
<h1 style="font-size:28px; font-weight:800; background:linear-gradient(135deg,#818cf8,#c4b5fd);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin:0;">
  🔐 Audit Chain Verification
</h1>
<div style="font-size:13px; color:#64748b; margin-top:4px; margin-bottom:20px;">
  SHA-256 hash chain · Daily Merkle root · CAG-defensible · RTI-reproducible
</div>
""", unsafe_allow_html=True)

# ─── Chain Design Explainer ───────────────────────────────────────────────────

with st.expander("📚 How the Audit Chain Works", expanded=False):
    st.markdown("""
    **Structure:** Every verdict, HITL decision, pipeline start/end, and RTI export is an immutable
    **audit record**. Each record is chained to the previous via:

    ```
    record_hash = SHA-256(payload_json || prev_hash)
    ```

    **SQLite WAL:** `UPDATE` and `DELETE` triggers throw an exception — the database is append-only at
    the application layer.

    **Daily Merkle Root:** Every 24h, all record hashes for the day are combined into a Merkle tree.
    The root hash is sent via **TEC-chair email** (SMTP + RFC-3161 TSA timestamp in production).
    This gives a non-repudiable, externally-anchored snapshot that survives even if the SQLite file is
    replaced.

    **Verification:** `verify_chain()` re-derives every `record_hash` from scratch and checks:
    1. Each `record_hash == SHA-256(payload || prev_hash)` ✓
    2. Each record's `prev_hash` matches the previous record's `record_hash` ✓
    If any check fails, the chain is **tampered** and `verify_chain()` returns `False`.

    **RTI:** The entire audit store is an RTI-producible artefact. Any inspector can run
    `verify_chain()` on the exported DB file to confirm no tampering.
    """)

st.divider()

# ─── Verify Chain ────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
      <div style="font-size:13px; font-weight:600; color:#a5b4fc; margin-bottom:12px;">
        🔍 Chain Integrity
      </div>
    """, unsafe_allow_html=True)

    if st.button("Verify Chain Integrity", key="btn_verify"):
        with st.spinner("Re-deriving all hashes..."):
            try:
                is_valid = verify_chain()
                if is_valid:
                    st.markdown("""
                    <div class="integrity-ok">
                      <div style="font-size:28px;">✅</div>
                      <div style="font-weight:700; color:#10b981; font-size:14px;">Chain INTACT</div>
                      <div style="font-size:11px; color:#64748b; margin-top:4px;">All hashes verified</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="integrity-fail">
                      <div style="font-size:28px;">❌</div>
                      <div style="font-weight:700; color:#ef4444; font-size:14px;">Chain TAMPERED</div>
                      <div style="font-size:11px; color:#64748b; margin-top:4px;">Hash mismatch detected!</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ Audit DB not initialised yet: {e}")
                st.info("Run the pipeline first to populate the audit chain.")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
      <div style="font-size:13px; font-weight:600; color:#a5b4fc; margin-bottom:12px;">
        🌳 Daily Merkle Root
      </div>
    """, unsafe_allow_html=True)

    if st.button("Compute Today's Root", key="btn_merkle"):
        with st.spinner("Computing Merkle tree..."):
            try:
                root = compute_daily_root()
                st.markdown(f"""
                <div class="merkle-box">
                  <div style="font-size:10px; color:#64748b; margin-bottom:6px; text-transform:uppercase; letter-spacing:.8px;">
                    Merkle Root (Today)
                  </div>
                  {root}
                </div>
                """, unsafe_allow_html=True)
                st.caption(
                    "📧 In production: this root is emailed to `tec-chair@crpf.gov.in` "
                    "with RFC-3161 TSA timestamp within 5 minutes of midnight UTC."
                )
            except Exception as e:
                st.warning(f"⚠️ {e}")
                st.info("Populate the audit chain first by running the pipeline.")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
      <div style="font-size:13px; font-weight:600; color:#a5b4fc; margin-bottom:12px;">
        📊 Chain Statistics
      </div>
    """, unsafe_allow_html=True)

    if st.button("Load Statistics", key="btn_stats"):
        try:
            records = get_all_records()
            event_counts: dict[str, int] = {}
            for r in records:
                et = r.get("event_type", "UNKNOWN")
                event_counts[et] = event_counts.get(et, 0) + 1

            st.markdown(f"**Total Records:** `{len(records)}`")
            for event_type, count in sorted(event_counts.items()):
                st.markdown(
                    f'<span class="stat-chip">{event_type}: {count}</span>',
                    unsafe_allow_html=True,
                )
        except Exception as e:
            st.warning(f"⚠️ {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Audit Records Viewer ─────────────────────────────────────────────────────

st.divider()
st.markdown("""
<div style="font-size:16px; font-weight:700; color:#e2e8f0; margin-bottom:12px;">
  📋 Audit Record Viewer
</div>
""", unsafe_allow_html=True)

max_records = st.slider("Records to show (most recent)", min_value=5, max_value=50, value=10)

if st.button("📋 Load Audit Records", key="btn_records"):
    try:
        records = get_all_records()
        recent = records[-max_records:][::-1]  # most recent first

        if not recent:
            st.info(
                "ℹ️ No audit records yet. "
                "Run the pipeline (`streamlit run Home.py` then navigate to Dashboard) "
                "to generate records."
            )
        else:
            for r in recent:
                event_color = {
                    "PIPELINE_START": "#6366f1",
                    "PIPELINE_COMPLETE": "#10b981",
                    "VERDICT_COMPUTED": "#a5b4fc",
                    "HITL_DECISION": "#f59e0b",
                    "RTI_EXPORT_GENERATED": "#34d399",
                }.get(r.get("event_type", ""), "#64748b")

                with st.expander(
                    f"🔗 {r.get('event_type', 'EVENT')} · {r.get('ts_utc', '')[:19]}",
                    expanded=False,
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Record ID:** `{r.get('record_id', 'N/A')}`")
                        st.markdown(
                            f"**Event:** "
                            f'<span style="color:{event_color}; font-weight:700;">'
                            f'{r.get("event_type", "N/A")}</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**Timestamp:** `{r.get('ts_utc', 'N/A')}`")
                    with c2:
                        hash_val = r.get("record_hash", "N/A")
                        prev_hash_val = r.get("prev_hash", "N/A")
                        st.markdown(
                            f"**Hash:** `{hash_val[:24]}...`" if len(hash_val) > 24 else f"**Hash:** `{hash_val}`"
                        )
                        st.markdown(
                            f"**Prev Hash:** `{prev_hash_val[:24]}...`" if len(prev_hash_val) > 24 else f"**Prev Hash:** `{prev_hash_val}`"
                        )

                    st.markdown("**Payload:**")
                    st.json(r.get("payload", {}))

    except Exception as e:
        st.warning(f"⚠️ Cannot read audit records: {e}")
        st.info(
            "💡 The audit DB initialises on first pipeline run. "
            "This is expected in a fresh demo environment."
        )

# ─── Tamper Demo ─────────────────────────────────────────────────────────────

st.divider()
st.markdown("""
<div class="glass-card">
  <div style="font-size:14px; font-weight:700; color:#fbbf24; margin-bottom:10px;">
    🎭 Tamper-Detection Demo (For Jury Presentation)
  </div>
  <div style="font-size:13px; color:#94a3b8; line-height:1.8;">
    To demonstrate chain integrity on stage:<br>
    1. Run pipeline → verdicts written to audit chain<br>
    2. Click <b>Verify Chain Integrity</b> → ✅ INTACT<br>
    3. Manually edit a hash in the SQLite DB (SQLite Browser or Python)<br>
    4. Click <b>Verify Chain Integrity</b> → ❌ TAMPERED (hash mismatch on record X)<br>
    5. Restore the DB from backup → chain intact again<br>
    <br>
    This proves the system is <b>mathematically tamper-evident</b> — no court or RTI inquiry can
    dispute a hash-chain-anchored verdict without also forging the Merkle email timestamp.
  </div>
</div>
""", unsafe_allow_html=True)
