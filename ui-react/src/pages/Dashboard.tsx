import { useEffect, useMemo, useState } from 'react';
import type { FormEvent, InputHTMLAttributes } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CalendarDays, FilePlus2, FolderOpen, Plus, RefreshCw } from 'lucide-react';
import { api, getStoredUser } from '../api';
import type { Tender } from '../api';

const statusLabels: Record<string, string> = {
  DRAFT: 'Draft',
  TENDER_UPLOADED: 'Tender Uploaded',
  CRITERIA_EXTRACTED: 'Criteria Extracted',
  BIDS_UPLOADED: 'Bids Uploaded',
  EVALUATING: 'Evaluating',
  HITL_PENDING: 'HITL Pending',
  REPORT_READY: 'Report Ready',
};

export function Dashboard() {
  const user = getStoredUser();
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState('');

  const grouped = useMemo(() => {
    const groups: Record<string, Tender[]> = {};
    tenders.forEach((tender) => {
      groups[tender.status] = [...(groups[tender.status] ?? []), tender];
    });
    return groups;
  }, [tenders]);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const data = await api.listTenders();
      setTenders(data.tenders);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tenders');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, []);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold text-neutral-900">Tender Dashboard</h1>
          <p className="mt-2 text-neutral-500">Operational workspace for upload-to-verdict evaluation.</p>
          {user && <p className="mt-1 text-xs font-bold uppercase tracking-wider text-primary-600">{user.name} · {user.role}</p>}
        </div>
        <div className="flex gap-3">
          <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-xl border border-neutral-300 bg-white px-4 py-3 text-sm font-bold text-neutral-700 hover:bg-neutral-50">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          {user?.role === 'ProcurementOfficer' && (
            <button type="button" onClick={() => setShowCreate(true)} className="inline-flex items-center gap-2 rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white hover:bg-primary-600">
              <Plus className="h-4 w-4" />
              Create Tender
            </button>
          )}
        </div>
      </header>

      {error && <div className="rounded-xl border border-semantic-error/30 bg-semantic-error/10 p-4 text-sm font-semibold text-semantic-error">{error}</div>}

      {loading ? (
        <div className="glass-card p-10 text-center text-neutral-500">Loading tenders...</div>
      ) : tenders.length === 0 ? (
        <EmptyState canCreate={user?.role === 'ProcurementOfficer'} onCreate={() => setShowCreate(true)} />
      ) : (
        <div className="space-y-8">
          {Object.keys(statusLabels).map((status) => (
            <section key={status} className={grouped[status]?.length ? 'space-y-4' : 'hidden'}>
              <h2 className="text-sm font-bold uppercase tracking-wider text-neutral-500">{statusLabels[status]}</h2>
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 xl:grid-cols-3">
                {grouped[status]?.map((tender) => <TenderCard key={tender.tender_id} tender={tender} />)}
              </div>
            </section>
          ))}
        </div>
      )}

      {showCreate && <CreateTenderModal onClose={() => setShowCreate(false)} onCreated={(tender) => {
        setTenders((current) => [tender, ...current]);
        setShowCreate(false);
      }} />}
    </motion.div>
  );
}

function TenderCard({ tender }: { tender: Tender }) {
  return (
    <article className="glass-card p-6">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-lg font-bold text-neutral-900">{tender.name}</h3>
          <p className="mt-1 text-sm text-neutral-500">{tender.reference_number}</p>
        </div>
        <span className="rounded-full border border-primary-500/20 bg-primary-500/10 px-3 py-1 text-xs font-bold text-primary-600">
          {statusLabels[tender.status] ?? tender.status}
        </span>
      </div>
      <div className="space-y-2 text-sm text-neutral-600">
        <p className="flex items-center gap-2"><FolderOpen className="h-4 w-4 text-neutral-400" /> {tender.procurement_circle}</p>
        <p className="flex items-center gap-2"><CalendarDays className="h-4 w-4 text-neutral-400" /> Opens {tender.opening_date || 'not set'}</p>
      </div>
      <Link to={`/tenders/${tender.tender_id}`} className="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-neutral-900 px-4 py-3 text-sm font-bold text-white hover:bg-neutral-700">
        Continue Evaluation
      </Link>
    </article>
  );
}

function EmptyState({ canCreate, onCreate }: { canCreate: boolean; onCreate: () => void }) {
  return (
    <div className="glass-card p-12 text-center">
      <FilePlus2 className="mx-auto h-12 w-12 text-primary-500" />
      <h2 className="mt-4 font-display text-xl font-bold text-neutral-900">No tenders yet</h2>
      <p className="mt-2 text-neutral-500">Create a tender to begin the upload-to-verdict workflow.</p>
      {canCreate && (
        <button type="button" onClick={onCreate} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white hover:bg-primary-600">
          <Plus className="h-4 w-4" />
          Create Tender
        </button>
      )}
    </div>
  );
}

function CreateTenderModal({ onClose, onCreated }: { onClose: () => void; onCreated: (tender: Tender) => void }) {
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError('');
    try {
      const { tender } = await api.createTender({
        name: String(form.get('name')),
        department: String(form.get('department')),
        procurement_circle: String(form.get('procurement_circle')),
        reference_number: String(form.get('reference_number')),
        opening_date: String(form.get('opening_date')),
      });
      onCreated(tender);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create tender');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4">
      <form onSubmit={submit} className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl">
        <h2 className="font-display text-xl font-bold">Create Tender</h2>
        <div className="mt-5 grid grid-cols-1 gap-4">
          <Input name="name" label="Tender name" required defaultValue="Security Equipment Procurement" />
          <Input name="reference_number" label="Reference number" required defaultValue="F.No. CRPF/PHQ/Proc/2026/001" />
          <Input name="department" label="Department / Unit" defaultValue="CRPF Procurement" />
          <Input name="procurement_circle" label="Procurement circle" defaultValue="PHQ New Delhi" />
          <Input name="opening_date" label="Opening date" type="date" />
        </div>
        {error && <div className="mt-4 rounded-xl bg-semantic-error/10 p-3 text-sm font-semibold text-semantic-error">{error}</div>}
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-xl border border-neutral-300 px-4 py-3 text-sm font-bold">Cancel</button>
          <button type="submit" disabled={saving} className="rounded-xl bg-primary-500 px-4 py-3 text-sm font-bold text-white disabled:bg-neutral-300">
            {saving ? 'Creating...' : 'Create Tender'}
          </button>
        </div>
      </form>
    </div>
  );
}

function Input({ label, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="text-sm font-bold text-neutral-700">
      {label}
      <input {...props} className="mt-2 w-full rounded-xl border border-neutral-300 px-4 py-3 text-sm font-medium outline-none focus:border-primary-500" />
    </label>
  );
}
