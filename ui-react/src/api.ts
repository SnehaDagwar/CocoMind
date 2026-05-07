const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';

export type Role = 'ProcurementOfficer' | 'Evaluator' | 'HITLReviewer' | 'Auditor';

export type DemoUser = {
  user_id: string;
  name: string;
  email: string;
  role: Role;
};

export type Tender = {
  tender_id: string;
  name: string;
  department: string;
  procurement_circle: string;
  reference_number: string;
  opening_date: string;
  status: string;
  created_at: string;
  updated_at: string;
  nit_document_id?: string | null;
  latest_job_id?: string | null;
  report_id?: string | null;
};

export type Criterion = {
  id: string;
  name: string;
  category: string;
  mandatory: boolean;
  data_type: string;
  threshold_operator: string;
  threshold_value: number | boolean | string | null;
  threshold_upper?: number | null;
  source_section: string;
  citation: string;
};

export type UploadedDocument = {
  document_id: string;
  tender_id: string;
  bid_id?: string | null;
  filename: string;
  size_bytes: number;
  doc_hash: string;
  uploaded_at: string;
};

export type Bidder = {
  bid_id: string;
  bid_name: string;
  tender_id: string;
  created_at: string;
  documents: UploadedDocument[];
};

export type EvaluationJob = {
  job_id: string;
  tender_id: string;
  status: string;
  progress: number;
  message: string;
  demo_backed: boolean;
  error?: string;
};

export type VtmRow = {
  bid_id: string;
  bid_name: string;
  criterion_id: string;
  criterion_name: string;
  verdict: { status: 'PASS' | 'FAIL' | 'AMBIGUOUS'; reason: string; expression: string };
  source_doc_id: string;
  source_doc_type: string;
  page_num: number;
  bbox?: { x_min: number; y_min: number; x_max: number; y_max: number } | null;
  raw_text: string;
  redacted_text: string;
  normalised_value: number | boolean | string | null;
  ocr_confidence: number;
  llm_confidence: number;
  retrieval_score: number;
  audit_record_id: string;
  rule_expression: string;
  hitl_decision?: string | null;
  signed_by?: string | null;
};

export type HitlItem = {
  item_id: string;
  bid_id: string;
  criterion_id: string;
  reason: string;
  reason_detail: string;
  source_doc_id: string;
  page_num: number;
  bbox?: { x_min: number; y_min: number; x_max: number; y_max: number } | null;
  ocr_text: string;
  extracted_value: number | boolean | string | null;
  confidence: number;
  resolved: boolean;
};

export type Report = {
  report_id: string;
  tender_id: string;
  generated_at: string;
  chain_verified: boolean;
  summary: Record<string, { overall: string; total: number; pass: number; fail: number; ambiguous: number }>;
  export: unknown;
};

export type TenderDetail = {
  tender: Tender;
  criteria: Criterion[];
  bidders: Bidder[];
  documents: UploadedDocument[];
};

export function getStoredUser(): DemoUser | null {
  const raw = localStorage.getItem('cocomind:user');
  return raw ? JSON.parse(raw) as DemoUser : null;
}

export function storeUser(user: DemoUser) {
  localStorage.setItem('cocomind:user', JSON.stringify(user));
}

export function clearUser() {
  localStorage.removeItem('cocomind:user');
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const user = getStoredUser();
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (user) {
    headers.set('X-User-ID', user.user_id);
    headers.set('X-User-Name', user.name);
    headers.set('X-User-Role', user.role);
    headers.set('X-User-Email', user.email);
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (role: Role) => apiFetch<{ user: DemoUser }>('/demo/login', {
    method: 'POST',
    body: JSON.stringify({ role }),
  }),
  listTenders: () => apiFetch<{ tenders: Tender[] }>('/tenders'),
  createTender: (payload: Partial<Tender>) => apiFetch<{ tender: Tender }>('/tenders', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  getTender: (id: string) => apiFetch<TenderDetail>(`/tenders/${id}`),
  uploadNit: (id: string, file: File) => {
    const body = new FormData();
    body.append('file', file);
    return apiFetch<{ tender: Tender; document: UploadedDocument }>(`/tenders/${id}/nit`, { method: 'POST', body });
  },
  extractCriteria: (id: string) => apiFetch<{ criteria: Criterion[]; demo_backed: boolean }>(`/tenders/${id}/criteria/extract`, { method: 'POST' }),
  updateCriterion: (tenderId: string, criterionId: string, patch: Partial<Criterion>) => apiFetch<{ criterion: Criterion }>(`/tenders/${tenderId}/criteria/${criterionId}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  }),
  createBidder: (tenderId: string, payload: { bid_id: string; bid_name: string }) => apiFetch<{ bidder: Bidder }>(`/tenders/${tenderId}/bids`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  uploadBidDoc: (tenderId: string, bidId: string, file: File) => {
    const body = new FormData();
    body.append('file', file);
    return apiFetch<{ tender: Tender; document: UploadedDocument }>(`/tenders/${tenderId}/bids/${bidId}/documents`, { method: 'POST', body });
  },
  startJob: (tenderId: string) => apiFetch<{ job: EvaluationJob }>(`/tenders/${tenderId}/evaluation-jobs`, { method: 'POST' }),
  getJob: (jobId: string) => apiFetch<{ job: EvaluationJob }>(`/jobs/${jobId}`),
  getVtm: (tenderId: string) => apiFetch<{ vtm: Record<string, VtmRow[]>; summary: Report['summary'] }>(`/tenders/${tenderId}/vtm`),
  getHitl: (tenderId: string) => apiFetch<{ items: HitlItem[] }>(`/tenders/${tenderId}/hitl`),
  submitHitl: (itemId: string, payload: { decision: string; override_value?: string; justification: string }) => apiFetch<{ unresolved_count: number }>(`/hitl/${encodeURIComponent(itemId)}/decision`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  createReport: (tenderId: string) => apiFetch<{ report: Report }>(`/tenders/${tenderId}/reports`, { method: 'POST' }),
  getReport: (reportId: string) => apiFetch<{ report: Report }>(`/reports/${reportId}`),
  verifyAudit: () => apiFetch<{ chain_valid: boolean; status: string }>('/audit/verify'),
  rtiExport: (bidId: string) => apiFetch<unknown>(`/rti/export/${bidId}`),
};
