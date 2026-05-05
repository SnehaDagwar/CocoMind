import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, FileCheck, FileX, AlertTriangle } from 'lucide-react';
import { SAMPLE_VTMS } from '../data/mock';

export function Dashboard() {
  const [selectedBid, setSelectedBid] = useState(Object.keys(SAMPLE_VTMS)[0]);
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});

  const toggleRow = (index: number) => {
    setExpandedRows(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const data = SAMPLE_VTMS[selectedBid as keyof typeof SAMPLE_VTMS];
  const passCount = data.rows.filter(r => r.verdict === 'PASS').length;
  const failCount = data.rows.filter(r => r.verdict === 'FAIL').length;
  const ambiguousCount = data.rows.filter(r => r.verdict === 'AMBIGUOUS').length;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold text-slate-100 mb-2">📊 Tender Evaluation Dashboard</h1>
          <p className="text-slate-400">Criterion-by-criterion, source-pinned eligibility verdicts</p>
        </div>
        <div className="w-72">
          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Select Bid</label>
          <select 
            className="w-full bg-surface border border-indigo-500/30 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-primary-500 transition-colors cursor-pointer appearance-none"
            value={selectedBid}
            onChange={(e) => setSelectedBid(e.target.value)}
          >
            {Object.entries(SAMPLE_VTMS).map(([key, val]) => (
              <option key={key} value={key}>{key} — {val.name}</option>
            ))}
          </select>
        </div>
      </header>

      <div className="grid grid-cols-4 gap-6">
        <div className="glass-card p-6 flex flex-col items-center justify-center">
          <div className="text-4xl font-display font-bold text-slate-200 mb-1">{data.rows.length}</div>
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Criteria</div>
        </div>
        <div className="glass-card p-6 flex flex-col items-center justify-center border-b-4 border-b-emerald-500">
          <div className="text-4xl font-display font-bold text-emerald-400 mb-1">{passCount}</div>
          <div className="text-xs font-bold text-emerald-500/70 uppercase tracking-wider flex items-center gap-1"><FileCheck className="w-3 h-3"/> PASS</div>
        </div>
        <div className="glass-card p-6 flex flex-col items-center justify-center border-b-4 border-b-red-500">
          <div className="text-4xl font-display font-bold text-red-400 mb-1">{failCount}</div>
          <div className="text-xs font-bold text-red-500/70 uppercase tracking-wider flex items-center gap-1"><FileX className="w-3 h-3"/> FAIL</div>
        </div>
        <div className="glass-card p-6 flex flex-col items-center justify-center border-b-4 border-b-amber-500">
          <div className="text-4xl font-display font-bold text-amber-400 mb-1">{ambiguousCount}</div>
          <div className="text-xs font-bold text-amber-500/70 uppercase tracking-wider flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> AMBIGUOUS</div>
        </div>
      </div>

      {failCount > 0 ? (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 font-medium flex items-center gap-3">
          <FileX className="w-5 h-5" /> <strong>Overall: INELIGIBLE</strong> — {failCount} mandatory criterion(s) failed
        </div>
      ) : ambiguousCount > 0 ? (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-amber-400 font-medium flex items-center gap-3">
          <AlertTriangle className="w-5 h-5" /> <strong>Overall: PENDING HITL</strong> — {ambiguousCount} criterion(s) need manual review
        </div>
      ) : (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-emerald-400 font-medium flex items-center gap-3">
          <FileCheck className="w-5 h-5" /> <strong>Overall: ELIGIBLE</strong> — All mandatory criteria passed
        </div>
      )}

      <div className="glass-card overflow-hidden">
        {data.rows.map((row, i) => (
          <div key={i} className="border-b border-indigo-500/10 last:border-0">
            <div 
              className="p-5 flex items-center gap-6 cursor-pointer hover:bg-white/5 transition-colors"
              onClick={() => toggleRow(i)}
            >
              <div className="flex-1">
                <h3 className="font-bold text-slate-200">{row.criterion}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-slate-500 capitalize">{row.category}</span>
                  <span className="text-slate-600 text-xs">•</span>
                  <span className={`text-xs font-semibold ${row.mandatory ? 'text-rose-400/80' : 'text-amber-400/80'}`}>
                    {row.mandatory ? '🔴 Mandatory' : '🟡 Optional'}
                  </span>
                </div>
              </div>
              <div className="w-32 text-right">
                <span className={`badge-${row.verdict.toLowerCase()}`}>{row.verdict}</span>
              </div>
              <div className="w-32">
                <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                  <span>Confidence</span>
                  <span>{Math.round(row.confidence * 100)}%</span>
                </div>
                <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${row.confidence > 0.9 ? 'bg-emerald-500' : row.confidence > 0.7 ? 'bg-primary-500' : 'bg-amber-500'}`} 
                    style={{ width: `${row.confidence * 100}%` }}
                  />
                </div>
              </div>
              <ChevronDown className={`w-5 h-5 text-slate-500 transition-transform ${expandedRows[i] ? 'rotate-180' : ''}`} />
            </div>

            <AnimatePresence>
              {expandedRows[i] && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden bg-black/20"
                >
                  <div className="p-6 grid grid-cols-2 gap-8 border-t border-white/5">
                    <div className="space-y-4">
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Extracted Value</div>
                        <div className="text-sm text-slate-200">{row.value}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Threshold</div>
                        <div className="text-sm text-slate-200">{row.threshold}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Rule Expression</div>
                        <code className="text-xs bg-surface px-2 py-1 rounded text-primary-300 border border-primary-500/20">{row.expression}</code>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Source Pinned</div>
                        <div className="text-sm text-slate-200">{row.source}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Document Type</div>
                        <div className="text-sm text-slate-200 font-mono text-xs">{row.doc_type}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Confidence Score</div>
                        <div className="text-sm text-slate-200">{(row.confidence * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
