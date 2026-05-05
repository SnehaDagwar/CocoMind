
import { NavLink } from 'react-router-dom';
import { Brain, LayoutDashboard, Search, FileDown, ShieldCheck } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { path: '/', label: 'Home', icon: Brain },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/hitl', label: 'HITL Review', icon: Search },
  { path: '/rti', label: 'RTI Export', icon: FileDown },
  { path: '/audit', label: 'Audit Chain', icon: ShieldCheck },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-indigo-500/20 bg-surface/50 backdrop-blur-xl flex flex-col h-screen sticky top-0">
      <div className="p-6 text-center space-y-2">
        <div className="flex justify-center mb-4">
          <Brain className="w-12 h-12 text-primary-500" />
        </div>
        <h1 className="text-2xl font-bold font-display gradient-text">CocoMind</h1>
        <p className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold">
          CRPF Tender Evaluation
        </p>
      </div>

      <div className="px-6 py-4">
        <h2 className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-4">Navigation</h2>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                  isActive 
                    ? "bg-primary-500/15 text-primary-400 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] border border-primary-500/20" 
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                )
              }
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="mt-auto p-6">
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-center">
          <p className="text-amber-400 text-xs font-bold mb-1 flex items-center justify-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            TIER-1 DEMO
          </p>
          <p className="text-[10px] text-slate-400">
            Synthetic data only.<br />DSC = dev certificate.
          </p>
        </div>
      </div>
    </aside>
  );
}
