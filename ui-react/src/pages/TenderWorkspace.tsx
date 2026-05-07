import { useEffect, useMemo, useState } from 'react';
import type { ChangeEvent, FormEvent, ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Download,
  FileCheck,
  FileText,
  Play,
  Plus,
  RefreshCw,
  Upload,
} from 'lucide-react';
import { api, getStoredUser } from '../api';
import type { Bidder, Criterion, EvaluationJob, HitlItem, Report, Tender, UploadedDocument, VtmRow } from '../api';

const steps = [
  'Upload Tender',
  'Extract Criteria',
  'Upload Bids',
  'Evaluate',
  'VTM',
  'Manual Review',
  'Final Report',
  'Audit & Export',
];

export function TenderWorkspace() {
  const { tenderId = '' } = useParams();
  const user = getStoredUser();
  const [tender, setTender] = useState<Tender | null>(null);
  const [criteria, setCriteria] = useState<Criterion[]>([]);
  const [bidders, setBidders] = useState<Bidder[]>([]);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [job, setJob] = useState<EvaluationJob | null>(null);
  const [vtm, setVtm] = useState<Record<string, VtmRow[]>>({});
  const [summary, setSummary] = useState<Report['summary']>({});
  const [hitl, setHitl] = useState<HitlItem[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [auditStatus, setAuditStatus] = useState<string>('Not checked');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const activeStep = useMemo(() => stepIndex(tender?.status), [tender?.status]);
  const unresolvedHitl = hitl.filter((item) => !item.resolved);

  async function load() {
    setError('');
    try {
      const detail = await api.getTender(tenderId);
      setTender(detail.tender);
      setCriteria(detail.criteria);
      setBidders(detail.bidders);
      setDocuments(detail.documents);
      if (detail.tender.latest_job_id) {
        const { job: currentJob } = await api.getJob(detail.tender.latest_job_id);
        setJob(currentJob);
      }
      await Promise.all([loadVtm(), loadHitl()]);
      if (detail.tender.report_id) {
        const { report: currentReport } = await api.getReport(detail.tender.report_id);
        setReport(currentReport);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tender');
    } finally {
      setLoading(false);
    }
  }

  async function loadVtm() {
    try {
      const data = await api.getVtm(tenderId);
      setVtm(data.vtm);
      setSummary(data.summary);
    } catch {
      setVtm({});
      setSummary({});
    }
  }

  async function loadHitl() {
    try {
      const data = await api.getHitl(tenderId);
      setHitl(data.items);
    } catch {
      setHitl([]);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenderId]);

  useEffect(() => {
    if (!job || ['COMPLETED', 'FAILED'].includes(job.status)) return;
    const id = window.setInterval(async () => {
      const { job: nextJob } = await api.getJob(job.job_id);
      setJob(nextJob);
      if (nextJob.status === 'COMPLETED') {
        await load();
      }
    }, 1200);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job?.job_id, job?.status]);

  async function action<T>(fn: () => Promise<T>) {
    setError('');
    try {
      const result = await fn();
      await load();
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
      return null;
    }
  }

  if (loading) return <div className="glass-card p-10 text-center text-neutral-500">Loading tender workspace...</div>;
  if (!tender) return <div className="glass-card p-10 text-center text-semantic-error">Tender not found</div>;

  return (
    <div className="space-y-8">
      <header className="space-y-5">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-bold text-neutral-500 hover:text-neutral-900">
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-display text-3xl font-bold">{tender.name}</h1>
            <p className="mt-2 text-neutral-500">{tender.reference_number} · {tender.procurement_circle}</p>
          </div>
          <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-xl border border-neutral-300 bg-white px-4 py-3 text-sm font-bold text-neutral-700">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
        <Stepper activeStep={activeStep} />
        {error && <div className="rounded-xl border border-semantic-error/30 bg-semantic-error/10 p-4 text-sm font-semibold text-semantic-error">{error}</div>}
      </header>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <NitSection disabled={user?.role !== 'ProcurementOfficer'} documents={documents.filter((doc) => !doc.bid_id)} onUpload={(file) => action(() => api.uploadNit(tenderId, file))} />
          <CriteriaSection disabled={!tender.nit_document_id} criteria={criteria} onExtract={() => action(() => api.extractCriteria(tenderId))} onUpdate={(criterion) => action(() => api.updateCriterion(tenderId, criterion.id, criterion))} />
          <BidSection disabled={criteria.length === 0 || user?.role !== 'ProcurementOfficer'} bidders={bidders} onCreate={(payload) => action(() => api.createBidder(tenderId, payload))} onUpload={(bidId, file) => action(() => api.uploadBidDoc(tenderId, bidId, file))} />
          <EvaluationSection disabled={criteria.length === 0 || bidders.length === 0} job={job} onStart={() => action(async () => {
            const { job: started } = await api.startJob(tenderId);
            setJob(started);
            return started;
          })} />
          <VtmSection vtm={vtm} summary={summary} />
          <HitlSection items={hitl} disabled={user?.role !== 'HITLReviewer'} onResolve={(itemId, payload) => action(() => api.submitHitl(itemId, payload))} />
          <ReportSection report={report} disabled={Object.keys(vtm).length === 0 || unresolvedHitl.length > 0} onGenerate={() => action(async () => {
            const { report: generated } = await api.createReport(tenderId);
            setReport(generated);
            return generated;
          })} />
        </div>

        <aside className="space-y-6">
          <NextAction tender={tender} criteria={criteria} bidders={bidders} hitlCount={unresolvedHitl.length} report={report} />
          <AuditExport auditStatus={auditStatus} setAuditStatus={setAuditStatus} summary={summary} />
        </aside>
      </section>
    </div>
  );
}

function Stepper({ activeStep }: { activeStep: number }) {
  return (
    <div className="glass-card overflow-x-auto p-4">
      <ol className="flex min-w-max gap-3">
        {steps.map((step, index) => (
          <li key={step} className={`flex items-center gap-2 rounded-full px-3 py-2 text-xs font-bold ${index <= activeStep ? 'bg-primary-500/10 text-primary-600' : 'bg-neutral-100 text-neutral-500'}`}>
            <span className="grid h-5 w-5 place-items-center rounded-full bg-white">{index + 1}</span>
            {step}
          </li>
        ))}
      </ol>
    </div>
  );
}

function NitSection({ disabled, documents, onUpload }: { disabled: boolean; documents: UploadedDocument[]; onUpload: (file: File) => void }) {
  return <Panel title="1. Upload Tender Document" icon={Upload}>
    <UploadControl disabled={disabled} label="Upload NIT / tender document" onUpload={onUpload} />
    <DocumentList documents={documents} empty="No tender document uploaded yet." />
  </Panel>;
}

function CriteriaSection({ disabled, criteria, onExtract, onUpdate }: { disabled: boolean; criteria: Criterion[]; onExtract: () => void; onUpdate: (criterion: Criterion) => void }) {
  return <Panel title="2. AI Extracts Criteria" icon={FileText}>
    <button type="button" disabled={disabled} onClick={onExtract} className="rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white disabled:bg-neutral-300">
      Extract Criteria
    </button>
    {criteria.length === 0 ? <Empty text="No criteria extracted yet." /> : (
      <div className="mt-4 overflow-hidden rounded-xl border border-neutral-200">
        {criteria.map((criterion) => <CriterionRow key={criterion.id} criterion={criterion} onSave={onUpdate} />)}
      </div>
    )}
  </Panel>;
}

function CriterionRow({ criterion, onSave }: { criterion: Criterion; onSave: (criterion: Criterion) => void }) {
  const [draft, setDraft] = useState(criterion);
  return (
    <div className="grid grid-cols-1 gap-3 border-b border-neutral-200 p-4 last:border-b-0 lg:grid-cols-[1fr_160px_120px_120px] lg:items-center">
      <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} className="rounded-lg border border-neutral-300 px-3 py-2 text-sm font-semibold" />
      <input value={String(draft.threshold_value ?? '')} onChange={(e) => setDraft({ ...draft, threshold_value: e.target.value })} className="rounded-lg border border-neutral-300 px-3 py-2 text-sm" />
      <span className="text-xs font-bold uppercase text-neutral-500">{draft.category}</span>
      <button type="button" onClick={() => onSave(draft)} className="rounded-lg border border-neutral-300 px-3 py-2 text-xs font-bold hover:bg-neutral-50">Save</button>
    </div>
  );
}

function BidSection({ disabled, bidders, onCreate, onUpload }: { disabled: boolean; bidders: Bidder[]; onCreate: (payload: { bid_id: string; bid_name: string }) => void; onUpload: (bidId: string, file: File) => void }) {
  return <Panel title="3. Upload Bidder Documents" icon={Plus}>
    <BidForm disabled={disabled} onCreate={onCreate} />
    {bidders.length === 0 ? <Empty text="No bidders uploaded yet." /> : (
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {bidders.map((bidder) => (
          <div key={bidder.bid_id} className="rounded-xl border border-neutral-200 p-4">
            <h3 className="font-bold">{bidder.bid_id}</h3>
            <p className="text-sm text-neutral-500">{bidder.bid_name}</p>
            <UploadControl disabled={disabled} label="Upload bundle" compact onUpload={(file) => onUpload(bidder.bid_id, file)} />
            <DocumentList documents={bidder.documents} empty="No docs." />
          </div>
        ))}
      </div>
    )}
  </Panel>;
}

function BidForm({ disabled, onCreate }: { disabled: boolean; onCreate: (payload: { bid_id: string; bid_name: string }) => void }) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    onCreate({ bid_id: String(form.get('bid_id')), bid_name: String(form.get('bid_name')) });
    event.currentTarget.reset();
  }
  return (
    <form onSubmit={submit} className="grid grid-cols-1 gap-3 lg:grid-cols-[140px_1fr_auto]">
      <input name="bid_id" required disabled={disabled} placeholder="BID-A" className="rounded-xl border border-neutral-300 px-4 py-3 text-sm" />
      <input name="bid_name" required disabled={disabled} placeholder="Bidder company name" className="rounded-xl border border-neutral-300 px-4 py-3 text-sm" />
      <button disabled={disabled} className="rounded-xl bg-neutral-900 px-4 py-3 text-sm font-bold text-white disabled:bg-neutral-300">Add Bidder</button>
    </form>
  );
}

function EvaluationSection({ disabled, job, onStart }: { disabled: boolean; job: EvaluationJob | null; onStart: () => void }) {
  return <Panel title="4. Parse Documents & Evaluate Eligibility" icon={Play}>
    <button type="button" disabled={disabled || (job !== null && !['COMPLETED', 'FAILED'].includes(job.status))} onClick={onStart} className="inline-flex items-center gap-2 rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white disabled:bg-neutral-300">
      <Play className="h-4 w-4" />
      Start Evaluation
    </button>
    {job && <div className="mt-4 rounded-xl border border-neutral-200 p-4">
      <div className="mb-2 flex justify-between text-sm font-bold"><span>{job.status}</span><span>{job.progress}%</span></div>
      <div className="h-2 overflow-hidden rounded-full bg-neutral-200"><div className="h-full bg-primary-500" style={{ width: `${job.progress}%` }} /></div>
      <p className="mt-2 text-sm text-neutral-500">{job.message}{job.demo_backed ? ' · Demo-backed fallback' : ''}</p>
    </div>}
  </Panel>;
}

function VtmSection({ vtm, summary }: { vtm: Record<string, VtmRow[]>; summary: Report['summary'] }) {
  return <Panel title="5. Verdict Traceability Matrix" icon={FileCheck}>
    {Object.keys(vtm).length === 0 ? <Empty text="Run evaluation to generate VTM rows." /> : (
      <div className="space-y-5">
        {Object.entries(vtm).map(([bidId, rows]) => (
          <div key={bidId} className="overflow-hidden rounded-xl border border-neutral-200">
            <div className="flex flex-col gap-2 bg-neutral-50 p-4 lg:flex-row lg:items-center lg:justify-between">
              <h3 className="font-bold">{bidId} · {rows[0]?.bid_name}</h3>
              <span className="text-sm font-bold text-neutral-600">{summary[bidId]?.overall}</span>
            </div>
            {rows.map((row) => <VtmRowView key={`${bidId}-${row.criterion_id}`} row={row} />)}
          </div>
        ))}
      </div>
    )}
  </Panel>;
}

function VtmRowView({ row }: { row: VtmRow }) {
  const badge = row.verdict.status === 'PASS' ? 'badge-pass' : row.verdict.status === 'FAIL' ? 'badge-fail' : 'badge-ambiguous';
  return (
    <details className="border-t border-neutral-200 p-4">
      <summary className="cursor-pointer list-none">
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1fr_130px_120px] lg:items-center">
          <div>
            <h4 className="font-bold">{row.criterion_name}</h4>
            <p className="text-xs text-neutral-500">{row.source_doc_type} · page {row.page_num} · audit {row.audit_record_id}</p>
          </div>
          <span className={badge}>{row.verdict.status}</span>
          <span className="text-sm font-semibold text-neutral-500">{Math.round(Math.max(row.ocr_confidence, row.llm_confidence) * 100)}%</span>
        </div>
      </summary>
      <div className="mt-4 grid grid-cols-1 gap-4 text-sm lg:grid-cols-2">
        <Trace label="Extracted value" value={String(row.normalised_value)} />
        <Trace label="Rule expression" value={row.rule_expression || row.verdict.expression} />
        <Trace label="BBox" value={row.bbox ? `${row.bbox.x_min}, ${row.bbox.y_min}, ${row.bbox.x_max}, ${row.bbox.y_max}` : 'n/a'} />
        <Trace label="Source text" value={row.redacted_text || row.raw_text} />
      </div>
    </details>
  );
}

function HitlSection({ items, disabled, onResolve }: { items: HitlItem[]; disabled: boolean; onResolve: (itemId: string, payload: { decision: string; override_value?: string; justification: string }) => void }) {
  return <Panel title="6. Manual Review Queue" icon={AlertTriangle}>
    {items.length === 0 ? <Empty text="No HITL items pending." /> : (
      <div className="space-y-4">
        {items.map((item) => <HitlCard key={item.item_id} item={item} disabled={disabled || item.resolved} onResolve={onResolve} />)}
      </div>
    )}
  </Panel>;
}

function HitlCard({ item, disabled, onResolve }: { item: HitlItem; disabled: boolean; onResolve: (itemId: string, payload: { decision: string; override_value?: string; justification: string }) => void }) {
  const [decision, setDecision] = useState('CONFIRM');
  const [overrideValue, setOverrideValue] = useState('');
  const [justification, setJustification] = useState('');
  return (
    <div className="rounded-xl border border-semantic-warning/30 bg-semantic-warning/5 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="font-bold">{item.bid_id} · {item.criterion_id}</h3>
          <p className="mt-1 text-sm text-neutral-600">{item.reason_detail || item.reason}</p>
          <p className="mt-2 text-xs text-neutral-500">Source {item.source_doc_id}, page {item.page_num}, confidence {Math.round(item.confidence * 100)}%</p>
        </div>
        {item.resolved && <span className="badge-pass">RESOLVED</span>}
      </div>
      <p className="mt-4 rounded-lg bg-white p-3 text-sm text-neutral-600">{item.ocr_text || 'No OCR text available.'}</p>
      {!item.resolved && (
        <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-[180px_1fr_1fr_auto]">
          <select disabled={disabled} value={decision} onChange={(e) => setDecision(e.target.value)} className="rounded-xl border border-neutral-300 px-3 py-2 text-sm">
            <option value="CONFIRM">Confirm</option>
            <option value="OVERRIDE">Override</option>
            <option value="NOT_PROVIDED">Not Provided</option>
          </select>
          <input disabled={disabled || decision !== 'OVERRIDE'} value={overrideValue} onChange={(e) => setOverrideValue(e.target.value)} placeholder="Override value" className="rounded-xl border border-neutral-300 px-3 py-2 text-sm" />
          <input disabled={disabled} value={justification} onChange={(e) => setJustification(e.target.value)} placeholder="Required justification" className="rounded-xl border border-neutral-300 px-3 py-2 text-sm" />
          <button disabled={disabled || !justification.trim()} onClick={() => onResolve(item.item_id, { decision, override_value: overrideValue || undefined, justification })} className="rounded-xl bg-primary-500 px-4 py-2 text-sm font-bold text-white disabled:bg-neutral-300">
            Submit
          </button>
        </div>
      )}
    </div>
  );
}

function ReportSection({ report, disabled, onGenerate }: { report: Report | null; disabled: boolean; onGenerate: () => void }) {
  return <Panel title="7. Final Report Generation" icon={CheckCircle2}>
    <button type="button" disabled={disabled} onClick={onGenerate} className="rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white disabled:bg-neutral-300">
      Generate Final Report
    </button>
    {report ? <pre className="mt-4 max-h-80 overflow-auto rounded-xl bg-neutral-950 p-4 text-xs text-neutral-100">{JSON.stringify(report.export, null, 2)}</pre> : <Empty text="Resolve required review items, then generate report." />}
  </Panel>;
}

function AuditExport({ auditStatus, setAuditStatus, summary }: { auditStatus: string; setAuditStatus: (value: string) => void; summary: Report['summary'] }) {
  async function verify() {
    const result = await api.verifyAudit();
    setAuditStatus(result.status);
  }
  async function exportFirstBid() {
    const bidId = Object.keys(summary)[0];
    if (!bidId) return;
    const payload = await api.rtiExport(bidId);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `rti_export_${bidId}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }
  return <Panel title="8. Audit & Export" icon={Download}>
    <Trace label="Audit chain" value={auditStatus} />
    <div className="mt-4 grid gap-3">
      <button type="button" onClick={verify} className="rounded-xl border border-neutral-300 px-4 py-3 text-sm font-bold">Verify Chain</button>
      <button type="button" onClick={exportFirstBid} disabled={!Object.keys(summary).length} className="rounded-xl bg-neutral-900 px-4 py-3 text-sm font-bold text-white disabled:bg-neutral-300">Download RTI JSON</button>
    </div>
  </Panel>;
}

function NextAction({ tender, criteria, bidders, hitlCount, report }: { tender: Tender; criteria: Criterion[]; bidders: Bidder[]; hitlCount: number; report: Report | null }) {
  let text = 'Upload the tender/NIT document.';
  if (tender.nit_document_id && criteria.length === 0) text = 'Extract and review eligibility criteria.';
  else if (criteria.length > 0 && bidders.length === 0) text = 'Add bidders and upload their document bundles.';
  else if (bidders.length > 0 && tender.status !== 'HITL_PENDING' && tender.status !== 'REPORT_READY') text = 'Start eligibility evaluation.';
  else if (hitlCount > 0) text = `Resolve ${hitlCount} manual review item(s).`;
  else if (!report && Object.keys(tender).length) text = 'Generate the final report.';
  if (report) text = 'Verify audit chain and export the RTI bundle.';
  return <Panel title="Next Recommended Action" icon={CheckCircle2}><p className="text-sm leading-relaxed text-neutral-600">{text}</p></Panel>;
}

function UploadControl({ disabled, label, compact = false, onUpload }: { disabled: boolean; label: string; compact?: boolean; onUpload: (file: File) => void }) {
  function change(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onUpload(file);
    event.target.value = '';
  }
  return <label className={`mt-4 inline-flex cursor-pointer items-center gap-2 rounded-xl border border-neutral-300 bg-white px-4 py-3 text-sm font-bold text-neutral-700 hover:bg-neutral-50 ${disabled ? 'pointer-events-none opacity-50' : ''}`}>
    <Upload className="h-4 w-4" />
    {compact ? 'Upload' : label}
    <input type="file" className="hidden" disabled={disabled} onChange={change} />
  </label>;
}

function DocumentList({ documents, empty }: { documents: UploadedDocument[]; empty: string }) {
  if (!documents.length) return <Empty text={empty} />;
  return <ul className="mt-4 space-y-2">{documents.map((doc) => <li key={doc.document_id} className="rounded-lg bg-neutral-50 px-3 py-2 text-xs font-semibold text-neutral-600">{doc.filename} · {(doc.size_bytes / 1024).toFixed(1)} KB</li>)}</ul>;
}

function Panel({ title, icon: Icon, children }: { title: string; icon: typeof Upload; children: ReactNode }) {
  return <section className="glass-card p-6">
    <h2 className="mb-4 flex items-center gap-2 font-display text-xl font-bold text-neutral-900"><Icon className="h-5 w-5 text-primary-500" /> {title}</h2>
    {children}
  </section>;
}

function Empty({ text }: { text: string }) {
  return <p className="mt-4 rounded-xl bg-neutral-50 p-4 text-sm text-neutral-500">{text}</p>;
}

function Trace({ label, value }: { label: string; value: string }) {
  return <div><div className="text-[10px] font-bold uppercase tracking-wider text-neutral-500">{label}</div><div className="mt-1 break-words text-sm text-neutral-700">{value}</div></div>;
}

function stepIndex(status?: string) {
  if (!status || status === 'DRAFT') return 0;
  if (status === 'TENDER_UPLOADED') return 1;
  if (status === 'CRITERIA_EXTRACTED') return 2;
  if (status === 'BIDS_UPLOADED') return 3;
  if (status === 'EVALUATING') return 3;
  if (status === 'HITL_PENDING') return 5;
  if (status === 'REPORT_READY') return 7;
  return 0;
}
