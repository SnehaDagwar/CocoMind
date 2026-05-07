
import { motion } from 'framer-motion';
import { FileText, ScanSearch, ShieldAlert, Layers, Network, Scale } from 'lucide-react';

const stages = [
  { icon: FileText, name: 'Ingest', desc: 'PDF/DOCX/IMG/ZIP' },
  { icon: ScanSearch, name: 'OCR', desc: 'Azure DI + bbox' },
  { icon: ShieldAlert, name: 'Redact', desc: 'Presidio + Indian PII' },
  { icon: Layers, name: 'Chunk + Embed', desc: 'BGE-M3 + BM25' },
  { icon: Network, name: 'Hybrid Retrieve', desc: 'RRF Fusion' },
  { icon: Scale, name: 'Rule Engine', desc: 'Pure Python verdict' },
];

const bids = [
  {
    icon: "✅",
    title: "BID-A — PASS",
    company: "M/s Sharma Industrial Pvt Ltd",
    color: "emerald",
    desc: "Golden path — typed PDFs, all 6 criteria met cleanly. Demonstrates clean evaluation flow.",
    verdicts: { PASS: 6, FAIL: 0, AMBIGUOUS: 0 },
  },
  {
    icon: "❌",
    title: "BID-B — FAIL",
    company: "M/s Verma Tech Solutions",
    color: "red",
    desc: "Similar Works Experience: only 1 project submitted vs. ≥3 required. Rule engine cites evidence.",
    verdicts: { PASS: 3, FAIL: 1, AMBIGUOUS: 0 },
  },
  {
    icon: "⚠️",
    title: "BID-C — HITL",
    company: "M/s Gupta Equipment Co",
    color: "amber",
    desc: "Handwritten CA cert conflict + ambiguous near-relations + Aadhaar redacted + prompt injection attempt.",
    verdicts: { PASS: 0, FAIL: 0, AMBIGUOUS: 2 },
  },
];

export function Home() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-12"
    >
      <header>
        <h1 className="text-5xl font-display font-bold gradient-text mb-2">CocoMind</h1>
        <p className="text-lg text-neutral-500 flex items-center gap-3">
          AI-Assisted CRPF Tender Evaluation Platform
          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-semantic-warning/10 text-semantic-warning border border-semantic-warning/20">
            TIER-1 DEMO
          </span>
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="glass-card p-8 lg:col-span-3">
          <h2 className="text-xl font-display font-bold text-neutral-900 mb-4 flex items-center gap-2">
            <span>🎯</span> What CocoMind Does
          </h2>
          <p className="text-neutral-500 leading-relaxed mb-6">
            CocoMind reads a CRPF tender (NIT) + bidder submissions and produces 
            <strong className="text-primary-600 font-semibold mx-1">criterion-by-criterion, source-pinned, RTI-auditable eligibility verdicts</strong> 
            — with a hard human-in-the-loop path for ambiguous cases and a legally-signed audit trail.
          </p>
          
          <div className="bg-neutral-100 rounded-xl p-5 border border-neutral-300">
            <h3 className="text-sm font-bold text-neutral-700 mb-3 uppercase tracking-wider">Hard non-negotiables:</h3>
            <ul className="space-y-3 text-sm text-neutral-500">
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>LLM <strong>extracts</strong> — Python rule engine <strong>decides</strong> (never the LLM)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>No silent disqualification — low confidence → HITL queue</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>Cryptographic audit chain + daily Merkle root</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>Presidio PII redaction before every LLM call</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>6 RBAC personas with least-privilege enforcement</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="glass-card p-8 lg:col-span-2">
          <h2 className="text-xl font-display font-bold text-neutral-900 mb-6 flex items-center gap-2">
            <span>🏗️</span> 6-Stage Pipeline
          </h2>
          <div className="space-y-4">
            {stages.map((stage) => (
              <div key={stage.name} className="flex items-center gap-4 p-3 rounded-lg hover:bg-neutral-50 transition-colors group">
                <div className="w-10 h-10 rounded-full bg-primary-500/10 text-primary-500 flex items-center justify-center group-hover:bg-primary-500/20 group-hover:scale-110 transition-all">
                  <stage.icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-neutral-900">{stage.name}</h4>
                  <p className="text-xs text-neutral-500">{stage.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-display font-bold text-neutral-900 mb-6 flex items-center gap-2">
          <span>🗂️</span> 3 Demo Bid Packages
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {bids.map((bid) => (
            <div key={bid.title} className={`glass-card p-6 border-t-4 ${
              bid.color === 'emerald' ? 'border-t-semantic-success' :
              bid.color === 'red' ? 'border-t-semantic-error' : 'border-t-semantic-warning'
            }`}>
              <div className="text-3xl mb-3">{bid.icon}</div>
              <h3 className={`text-lg font-bold mb-1 ${
                bid.color === 'emerald' ? 'text-semantic-success' :
                bid.color === 'red' ? 'text-semantic-error' : 'text-semantic-warning'
              }`}>{bid.title}</h3>
              <p className="text-xs font-semibold text-neutral-500 mb-4">{bid.company}</p>
              <p className="text-sm text-neutral-700 leading-relaxed mb-6">{bid.desc}</p>
              <div className="flex flex-wrap gap-2">
                <span className="badge-pass">{bid.verdicts.PASS} PASS</span>
                <span className="badge-fail">{bid.verdicts.FAIL} FAIL</span>
                <span className="badge-ambiguous">{bid.verdicts.AMBIGUOUS} AMBIGUOUS</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
