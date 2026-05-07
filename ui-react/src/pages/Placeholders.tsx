import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Copy,
  Download,
  FileJson,
  LockKeyhole,
  Search,
  ShieldCheck,
  Stamp,
} from 'lucide-react';
import { AUDIT_RECORDS, HITL_ITEMS, SAMPLE_VTMS } from '../data/mock';

type HitlDecision = 'Confirm extracted value' | 'Override value' | 'Mark not provided';

export function HITLReview() {
  const [selectedId, setSelectedId] = useState(HITL_ITEMS[0]?.id ?? '');
  const [decision, setDecision] = useState<HitlDecision>('Confirm extracted value');
  const [overrideValue, setOverrideValue] = useState('');
  const [justification, setJustification] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const selectedItem = HITL_ITEMS.find((item) => item.id === selectedId) ?? HITL_ITEMS[0];
  const canSubmit = Boolean(justification.trim()) && (decision !== 'Override value' || Boolean(overrideValue.trim()));

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-neutral-900 mb-2 flex items-center gap-3">
            <Search className="h-8 w-8 text-primary-500" />
            Human-in-the-Loop Review
          </h1>
          <p className="text-neutral-500">Resolve ambiguous verdicts with officer sign-off</p>
        </div>
        <div className="glass-card px-5 py-4">
          <div className="text-3xl font-display font-bold text-semantic-warning">{HITL_ITEMS.length}</div>
          <div className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Pending Items</div>
        </div>
      </header>

      {HITL_ITEMS.length === 0 ? (
        <div className="glass-card p-10 text-center">
          <CheckCircle2 className="mx-auto h-12 w-12 text-semantic-success" />
          <p className="mt-4 font-bold text-neutral-900">No items pending HITL review</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr] gap-6">
          <aside className="glass-card overflow-hidden">
            {HITL_ITEMS.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setSelectedId(item.id);
                  setSubmitted(false);
                }}
                className={`w-full text-left p-5 border-b border-neutral-200 last:border-b-0 transition-colors ${
                  item.id === selectedItem.id ? 'bg-semantic-warning/10' : 'hover:bg-neutral-50'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-bold text-neutral-500">{item.id}</span>
                  <span className="badge-ambiguous">AMBIGUOUS</span>
                </div>
                <h2 className="mt-3 font-bold text-neutral-900">{item.criterion}</h2>
                <p className="mt-1 text-sm text-neutral-500">{item.bidId} - {item.bidName}</p>
              </button>
            ))}
          </aside>

          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass-card p-6 space-y-5">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-neutral-500 font-bold mb-1">Source Document</div>
                <div className="font-bold text-neutral-900">{selectedItem.source}</div>
                <div className="mt-1 text-xs font-mono text-neutral-500">{selectedItem.doc_type}</div>
              </div>

              <div className="rounded-xl border border-semantic-warning/30 bg-semantic-warning/10 p-5">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-xs font-bold text-semantic-warning uppercase tracking-wider">Highlighted Evidence</span>
                  <span className="text-xs font-mono text-neutral-500">{selectedItem.bbox}</span>
                </div>
                <p className="text-sm leading-relaxed text-neutral-700">{selectedItem.evidence}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Trace label="Extracted Value" value={selectedItem.value} />
                <Trace label="Threshold" value={selectedItem.threshold} />
                <Trace label="Rule Expression" value={selectedItem.expression} code />
                <Trace label="Confidence" value={`${Math.round(selectedItem.confidence * 100)}%`} />
              </div>
            </div>

            <form
              className="glass-card p-6 space-y-5"
              onSubmit={(event) => {
                event.preventDefault();
                if (canSubmit) setSubmitted(true);
              }}
            >
              <div>
                <h2 className="font-display text-xl font-bold text-neutral-900 flex items-center gap-2">
                  <ClipboardCheck className="h-5 w-5 text-primary-500" />
                  Officer Decision
                </h2>
                <p className="mt-1 text-sm text-neutral-500">A justification is required before the decision can be audit logged.</p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {(['Confirm extracted value', 'Override value', 'Mark not provided'] as HitlDecision[]).map((option) => (
                  <label key={option} className="flex cursor-pointer items-center gap-3 rounded-xl border border-neutral-300 bg-white px-4 py-3 text-sm font-semibold text-neutral-700">
                    <input
                      type="radio"
                      name="decision"
                      value={option}
                      checked={decision === option}
                      onChange={() => setDecision(option)}
                      className="accent-primary-500"
                    />
                    {option}
                  </label>
                ))}
              </div>

              {decision === 'Override value' && (
                <input
                  value={overrideValue}
                  onChange={(event) => setOverrideValue(event.target.value)}
                  placeholder="Enter corrected value"
                  className="w-full rounded-xl border border-neutral-300 bg-white px-4 py-3 text-sm outline-none focus:border-primary-500"
                />
              )}

              <textarea
                value={justification}
                onChange={(event) => setJustification(event.target.value)}
                placeholder="Officer justification"
                rows={5}
                className="w-full resize-none rounded-xl border border-neutral-300 bg-white px-4 py-3 text-sm outline-none focus:border-primary-500"
              />

              <button
                type="submit"
                disabled={!canSubmit}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-primary-600 disabled:cursor-not-allowed disabled:bg-neutral-300"
              >
                <Stamp className="h-4 w-4" />
                Submit Signed Decision
              </button>

              {submitted && (
                <div className="rounded-xl border border-semantic-success/30 bg-semantic-success/10 p-4 text-sm font-semibold text-semantic-success">
                  Decision recorded locally for demo. Production flow signs this event with DSC and appends it to the audit chain.
                </div>
              )}
            </form>
          </section>
        </div>
      )}
    </motion.div>
  );
}

export function RTIExport() {
  const [selectedBid, setSelectedBid] = useState(Object.keys(SAMPLE_VTMS)[0]);
  const bid = SAMPLE_VTMS[selectedBid];
  const exportPayload = useMemo(
    () => ({
      export_format: 'RTI_VTM_JSON_v1',
      generated_at: new Date().toISOString(),
      bid_id: selectedBid,
      bid_name: bid.name,
      overall: bid.overall,
      criteria_evaluated: bid.rows.length,
      verdicts: bid.rows,
    }),
    [bid, selectedBid],
  );
  const exportText = JSON.stringify(exportPayload, null, 2);

  const downloadExport = () => {
    const blob = new Blob([exportText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `rti_export_${selectedBid}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-neutral-900 mb-2 flex items-center gap-3">
            <FileJson className="h-8 w-8 text-primary-500" />
            RTI Export
          </h1>
          <p className="text-neutral-500">Generate source-pinned VTM exports for RTI responses</p>
        </div>
        <select
          value={selectedBid}
          onChange={(event) => setSelectedBid(event.target.value)}
          className="w-full rounded-xl border border-neutral-300 bg-white px-4 py-3 text-neutral-900 outline-none focus:border-primary-500 lg:w-80"
        >
          {Object.entries(SAMPLE_VTMS).map(([key, value]) => (
            <option key={key} value={key}>{key} - {value.name}</option>
          ))}
        </select>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-6">
        <section className="glass-card p-6 space-y-5">
          <Trace label="Selected Bid" value={`${selectedBid} - ${bid.name}`} />
          <Trace label="Overall Verdict" value={bid.overall} />
          <Trace label="Criteria Evaluated" value={String(bid.rows.length)} />
          <Trace label="Export Contents" value="VTM rows, source evidence, expressions, confidence scores" />
          <button
            type="button"
            onClick={downloadExport}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-primary-600"
          >
            <Download className="h-4 w-4" />
            Download JSON Export
          </button>
        </section>

        <section className="glass-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-neutral-200 px-5 py-4">
            <h2 className="font-bold text-neutral-900">Export Preview</h2>
            <button
              type="button"
              onClick={() => navigator.clipboard?.writeText(exportText)}
              className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 px-3 py-2 text-xs font-bold text-neutral-700 hover:bg-neutral-50"
            >
              <Copy className="h-3.5 w-3.5" />
              Copy
            </button>
          </div>
          <pre className="max-h-[560px] overflow-auto bg-neutral-950 p-5 text-xs leading-relaxed text-neutral-100">{exportText}</pre>
        </section>
      </div>
    </motion.div>
  );
}

export function AuditChain() {
  const merkleRoot = '9f55dfc75d07cb61cf8d6cc3a5e9e0cf8c874f14bb56d0f571a589377f013fb7';

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <header>
        <h1 className="text-3xl font-display font-bold text-neutral-900 mb-2 flex items-center gap-3">
          <LockKeyhole className="h-8 w-8 text-primary-500" />
          Audit Chain Verification
        </h1>
        <p className="text-neutral-500">SHA-256 hash chain with daily Merkle root anchoring</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatusCard icon={ShieldCheck} label="Chain Status" value="INTACT" tone="success" />
        <StatusCard icon={ClipboardCheck} label="Audit Records" value={String(AUDIT_RECORDS.length)} tone="info" />
        <StatusCard icon={AlertTriangle} label="Tamper Alerts" value="0" tone="warning" />
      </div>

      <section className="glass-card p-6">
        <div className="text-[10px] uppercase tracking-wider text-neutral-500 font-bold mb-2">Daily Merkle Root</div>
        <code className="block overflow-auto rounded-xl border border-neutral-300 bg-neutral-50 p-4 text-sm text-neutral-700">{merkleRoot}</code>
      </section>

      <section className="glass-card overflow-hidden">
        <div className="border-b border-neutral-200 px-5 py-4">
          <h2 className="font-bold text-neutral-900">Latest Records</h2>
        </div>
        {AUDIT_RECORDS.map((record) => (
          <div key={record.id} className="grid grid-cols-1 gap-3 border-b border-neutral-200 p-5 last:border-b-0 lg:grid-cols-[160px_1fr_220px] lg:items-center">
            <div>
              <div className="font-bold text-neutral-900">{record.id}</div>
              <div className="text-xs text-neutral-500">{record.timestamp}</div>
            </div>
            <div>
              <div className="text-sm font-bold text-neutral-700">{record.type}</div>
              <div className="mt-1 text-xs text-neutral-500">Actor: {record.actor}</div>
              <div className="mt-2 truncate font-mono text-xs text-neutral-500">Prev: {record.previous}</div>
            </div>
            <code className="truncate rounded-lg bg-neutral-100 px-3 py-2 text-xs text-neutral-700">{record.hash}</code>
          </div>
        ))}
      </section>
    </motion.div>
  );
}

function Trace({ label, value, code = false }: { label: string; value: string; code?: boolean }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-neutral-500 font-bold mb-1">{label}</div>
      {code ? (
        <code className="inline-block rounded-lg border border-primary-500/20 bg-white px-2 py-1 text-xs font-bold text-primary-500">{value}</code>
      ) : (
        <div className="text-sm text-neutral-700">{value}</div>
      )}
    </div>
  );
}

function StatusCard({ icon: Icon, label, value, tone }: { icon: typeof ShieldCheck; label: string; value: string; tone: 'success' | 'info' | 'warning' }) {
  const toneClass = {
    success: 'text-semantic-success border-b-semantic-success',
    info: 'text-semantic-info border-b-semantic-info',
    warning: 'text-semantic-warning border-b-semantic-warning',
  }[tone];

  return (
    <div className={`glass-card border-b-4 p-6 ${toneClass}`}>
      <Icon className="mb-4 h-7 w-7" />
      <div className="text-3xl font-display font-bold">{value}</div>
      <div className="mt-1 text-xs font-bold uppercase tracking-wider text-neutral-500">{label}</div>
    </div>
  );
}
