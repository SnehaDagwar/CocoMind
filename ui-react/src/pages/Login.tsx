import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, ClipboardCheck, FileSearch, Scale, ShieldCheck } from 'lucide-react';
import { api, storeUser } from '../api';
import type { Role } from '../api';

const roles: Array<{ role: Role; title: string; desc: string; icon: typeof ClipboardCheck }> = [
  { role: 'ProcurementOfficer', title: 'Procurement Officer', desc: 'Create tenders, upload documents, and launch evaluation.', icon: ClipboardCheck },
  { role: 'Evaluator', title: 'Evaluator', desc: 'Review criteria, VTM rows, and evaluation outcomes.', icon: Scale },
  { role: 'HITLReviewer', title: 'HITL Reviewer', desc: 'Resolve ambiguous evidence with signed decisions.', icon: FileSearch },
  { role: 'Auditor', title: 'Auditor', desc: 'Verify audit chain and export RTI bundles.', icon: ShieldCheck },
];

export function Login() {
  const navigate = useNavigate();
  const [loadingRole, setLoadingRole] = useState<Role | null>(null);
  const [error, setError] = useState('');

  async function selectRole(role: Role) {
    setLoadingRole(role);
    setError('');
    try {
      const { user } = await api.login(role);
      storeUser(user);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoadingRole(null);
    }
  }

  return (
    <main className="min-h-screen bg-background p-6 text-neutral-900">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl flex-col justify-center gap-8">
        <header>
          <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-500/10 text-primary-500">
            <Brain className="h-8 w-8" />
          </div>
          <h1 className="font-display text-4xl font-bold">CocoMind Login</h1>
          <p className="mt-2 max-w-2xl text-neutral-500">
            Choose a demo RBAC persona to enter the tender evaluation workflow.
          </p>
        </header>

        {error && <div className="rounded-xl border border-semantic-error/30 bg-semantic-error/10 p-4 text-sm font-semibold text-semantic-error">{error}</div>}

        <section className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          {roles.map(({ role, title, desc, icon: Icon }) => (
            <button
              key={role}
              type="button"
              onClick={() => selectRole(role)}
              className="glass-card p-6 text-left hover:border-primary-500/40"
            >
              <Icon className="mb-5 h-8 w-8 text-primary-500" />
              <h2 className="font-display text-lg font-bold">{title}</h2>
              <p className="mt-2 min-h-16 text-sm leading-relaxed text-neutral-500">{desc}</p>
              <div className="mt-5 text-sm font-bold text-primary-600">
                {loadingRole === role ? 'Entering...' : 'Enter workspace'}
              </div>
            </button>
          ))}
        </section>
      </div>
    </main>
  );
}
