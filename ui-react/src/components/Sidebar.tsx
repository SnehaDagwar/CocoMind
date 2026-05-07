
import { NavLink, useNavigate } from 'react-router-dom';
import { Brain, FileDown, LayoutDashboard, LogOut, Search, ShieldCheck } from 'lucide-react';
import { clearUser, getStoredUser } from '../api';
import { cn } from '../lib/utils';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/hitl', label: 'HITL Review', icon: Search },
  { path: '/rti', label: 'RTI Export', icon: FileDown },
  { path: '/audit', label: 'Audit Chain', icon: ShieldCheck },
];

export function Sidebar() {
  const navigate = useNavigate();
  const user = getStoredUser();

  function logout() {
    clearUser();
    navigate('/login');
  }

  return (
    <aside className="border-b border-neutral-300/50 bg-surface lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:flex-col lg:border-b-0 lg:border-r">
      <div className="p-4 text-center space-y-2 lg:p-6">
        <div className="flex justify-center lg:mb-4">
          <Brain className="w-10 h-10 text-primary-500 lg:h-12 lg:w-12" />
        </div>
        <h1 className="text-xl font-bold font-display text-neutral-900 lg:text-2xl">CocoMind</h1>
        <p className="text-[10px] uppercase tracking-widest text-neutral-500 font-semibold">
          CRPF Tender Evaluation
        </p>
      </div>

      <div className="px-4 pb-4 lg:px-6 lg:py-4">
        <h2 className="hidden text-[10px] uppercase tracking-widest text-neutral-500 font-bold mb-4 lg:block">Navigation</h2>
        <nav className="flex gap-2 overflow-x-auto lg:block lg:space-y-1 lg:overflow-visible">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex shrink-0 items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 lg:gap-3",
                  isActive 
                    ? "bg-primary-500/10 text-primary-600 font-bold" 
                    : "text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100"
                )
              }
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="mt-auto hidden p-6 lg:block">
        {user && (
          <div className="mb-4 rounded-xl border border-neutral-200 bg-neutral-50 p-4">
            <p className="text-sm font-bold text-neutral-900">{user.name}</p>
            <p className="text-[10px] uppercase tracking-wider text-neutral-500">{user.role}</p>
            <button type="button" onClick={logout} className="mt-3 inline-flex items-center gap-2 text-xs font-bold text-neutral-500 hover:text-neutral-900">
              <LogOut className="h-3.5 w-3.5" />
              Logout
            </button>
          </div>
        )}
        <div className="bg-semantic-warning/10 border border-semantic-warning/20 rounded-xl p-4 text-center">
          <p className="text-semantic-warning text-xs font-bold mb-1 flex items-center justify-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-semantic-warning animate-pulse"></span>
            TIER-1 DEMO
          </p>
          <p className="text-[10px] text-neutral-500">
            Synthetic data only.<br />DSC = dev certificate.
          </p>
        </div>
      </div>
    </aside>
  );
}
