export type Verdict = 'PASS' | 'FAIL' | 'AMBIGUOUS';

export type VtmRow = {
  criterion: string;
  category: string;
  mandatory: boolean;
  verdict: Verdict;
  value: string;
  threshold: string;
  expression: string;
  source: string;
  confidence: number;
  doc_type: string;
  evidence?: string;
  bbox?: string;
};

export type BidVtm = {
  name: string;
  overall: 'ELIGIBLE' | 'INELIGIBLE' | 'PENDING HITL';
  rows: VtmRow[];
};

export const SAMPLE_VTMS: Record<string, BidVtm> = {
  "BID-A": {
    name: "M/s Sharma Industrial Pvt Ltd",
    overall: "ELIGIBLE",
    rows: [
      {
        criterion: "Average Annual Turnover",
        category: "financial",
        mandatory: true,
        verdict: "PASS",
        value: "₹6,00,00,000",
        threshold: "≥ ₹5,00,00,000",
        expression: "60000000 >= 50000000",
        source: "CA Certificate, Page 2",
        confidence: 0.95,
        doc_type: "ca_certificate",
        evidence: "Average annual turnover for FY 2022-23, 2023-24 and 2024-25 is certified as Rs. 6,00,00,000.",
        bbox: "page=2; x=118,y=342,w=231,h=32",
      },
      {
        criterion: "Similar Works Experience",
        category: "technical",
        mandatory: true,
        verdict: "PASS",
        value: "5 projects",
        threshold: "≥ 3 projects",
        expression: "5 >= 3",
        source: "Experience Certificate, Page 1",
        confidence: 0.92,
        doc_type: "experience_cert",
        evidence: "Five comparable supply projects completed for police and paramilitary procurement units.",
        bbox: "page=1; x=94,y=288,w=304,h=54",
      },
      {
        criterion: "GST Registration",
        category: "compliance",
        mandatory: true,
        verdict: "PASS",
        value: "Valid (07AAACS1234A1ZH)",
        threshold: "Valid registration",
        expression: "bool(True) = True",
        source: "GST Certificate, Page 1",
        confidence: 0.98,
        doc_type: "gst_cert",
        evidence: "GSTIN 07AAACS1234A1ZH is active on the certificate date.",
        bbox: "page=1; x=126,y=178,w=218,h=24",
      },
      {
        criterion: "EMD / Bank Guarantee",
        category: "financial",
        mandatory: true,
        verdict: "PASS",
        value: "₹10,00,000 valid till 2026-08-15",
        threshold: "≥ 2% of NIT value, ≥45 days validity",
        expression: "BG ₹10,00,000 ≥ ₹5,00,000 and validity OK",
        source: "BG Document, Page 1",
        confidence: 0.9,
        doc_type: "emd_document",
        evidence: "Bank guarantee amount and validity satisfy the NIT requirement.",
        bbox: "page=1; x=76,y=211,w=346,h=48",
      },
    ],
  },
  "BID-B": {
    name: "M/s Verma Tech Solutions",
    overall: "INELIGIBLE",
    rows: [
      {
        criterion: "Average Annual Turnover",
        category: "financial",
        mandatory: true,
        verdict: "PASS",
        value: "₹7,50,00,000",
        threshold: "≥ ₹5,00,00,000",
        expression: "75000000 >= 50000000",
        source: "Audited Financial Statement, Page 4",
        confidence: 0.93,
        doc_type: "audited_financial_statement",
        evidence: "Audited statement reports average annual turnover as Rs. 7,50,00,000.",
        bbox: "page=4; x=88,y=417,w=276,h=31",
      },
      {
        criterion: "Similar Works Experience",
        category: "technical",
        mandatory: true,
        verdict: "FAIL",
        value: "1 project",
        threshold: "≥ 3 projects",
        expression: "1 >= 3 → False",
        source: "Experience Certificate, Page 1",
        confidence: 0.88,
        doc_type: "experience_cert",
        evidence: "Only one similar work completion certificate is attached.",
        bbox: "page=1; x=112,y=249,w=254,h=39",
      },
      {
        criterion: "GST Registration",
        category: "compliance",
        mandatory: true,
        verdict: "PASS",
        value: "Valid",
        threshold: "Valid registration",
        expression: "bool(True) = True",
        source: "GST Certificate, Page 1",
        confidence: 0.97,
        doc_type: "gst_cert",
        evidence: "GST registration certificate is present and active.",
        bbox: "page=1; x=141,y=196,w=188,h=27",
      },
    ],
  },
  "BID-C": {
    name: "M/s Gupta Equipment Co",
    overall: "PENDING HITL",
    rows: [
      {
        criterion: "Average Annual Turnover",
        category: "financial",
        mandatory: true,
        verdict: "AMBIGUOUS",
        value: "₹5,20,00,000 (from handwritten CA cert) vs ₹4,80,00,000 (cover letter)",
        threshold: "≥ ₹5,00,00,000",
        expression: "Conflict unresolved — handwritten CA cert + cover letter disagree",
        source: "CA Certificate (photo), Page 1",
        confidence: 0.55,
        doc_type: "ca_certificate",
        evidence: "Handwritten CA certificate appears to state Rs. 5,20,00,000, while cover letter states Rs. 4,80,00,000.",
        bbox: "page=1; x=64,y=381,w=332,h=58",
      },
      {
        criterion: "Near Relations Declaration",
        category: "declaration",
        mandatory: true,
        verdict: "AMBIGUOUS",
        value: "Declaration present but unclear",
        threshold: "Must declare no near relations",
        expression: "Keywords not found — needs HITL review",
        source: "Self Declaration, Page 2",
        confidence: 0.4,
        doc_type: "self_declaration",
        evidence: "Declaration is present, but the expected no-near-relations clause could not be confidently located.",
        bbox: "page=2; x=83,y=302,w=311,h=72",
      },
    ],
  },
};

export const HITL_ITEMS = Object.entries(SAMPLE_VTMS).flatMap(([bidId, bid]) =>
  bid.rows
    .filter((row) => row.verdict === 'AMBIGUOUS')
    .map((row, index) => ({
      id: `HITL-${String(index + 1).padStart(3, '0')}`,
      bidId,
      bidName: bid.name,
      ...row,
    })),
);

export const AUDIT_RECORDS = [
  {
    id: 'AUD-2026-001',
    type: 'PIPELINE_STARTED',
    actor: 'procurement_officer.demo',
    timestamp: '2026-05-07T09:15:04Z',
    hash: 'ad5e2b3f8f4c928390bda51410e7a6a9359aa51c782f60291255e4b3bf6d801e',
    previous: 'GENESIS',
  },
  {
    id: 'AUD-2026-002',
    type: 'VERDICT_COMPUTED',
    actor: 'rule_engine',
    timestamp: '2026-05-07T09:16:31Z',
    hash: '60d71ef3d4cd9aafad63dcf7d1343f777e221c789a7f77309e07c902ded89953',
    previous: 'ad5e2b3f8f4c928390bda51410e7a6a9359aa51c782f60291255e4b3bf6d801e',
  },
  {
    id: 'AUD-2026-003',
    type: 'HITL_ROUTED',
    actor: 'conflict_resolver',
    timestamp: '2026-05-07T09:17:12Z',
    hash: 'f70e89037bbeb7a2d71a358967f0f438cc820a2ac175cd4d88666f80fed91231',
    previous: '60d71ef3d4cd9aafad63dcf7d1343f777e221c789a7f77309e07c902ded89953',
  },
];
