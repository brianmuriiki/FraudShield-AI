const configuredBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const API_BASE_URL = configuredBase.endsWith('/api/v1') ? configuredBase : `${configuredBase}/api/v1`
let accessToken: string | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export type TransactionType = 'CASH_IN' | 'CASH_OUT' | 'DEBIT' | 'PAYMENT' | 'TRANSFER'

export type PredictionRequest = {
  step: number
  amount: number
  oldbalanceOrg: number
  oldbalanceDest: number
} & Record<`type_${TransactionType}`, 0 | 1>

export type PredictionResponse = {
  transaction_id: string
  prediction: string
  fraud_score: number
  threshold: number
  risk_level: string
  requires_investigation: boolean
  transaction_type: TransactionType
  model_name: string
  message: string
  features?: Array<{ feature: string; value: number; contribution: number; influence: string; description: string }>
}

export type ExplanationResponse = { transaction_id: string | null; features: NonNullable<PredictionResponse['features']>; warning: string }
export type LoginResponse = { access_token: string; token_type: string; expires_in: number; user: { id: number; email: string; full_name: string; role: string } }
export type Page<T> = { items: T[]; total: number; page: number; page_size: number; pages: number }
export type ApiTransaction = { id: number; transaction_id: string; transaction_type: TransactionType; amount: number; created_at: string; fraud_score: number; threshold: number; prediction: string; risk_level: string; investigation_status: string; step: number; oldbalanceOrg: number; oldbalanceDest: number }
export type Investigation = { id: number; investigation_reference: string; transaction_id: string; assigned_analyst_id: number | null; assigned_analyst?: { id: number; full_name: string; role: string } | null; status: string; outcome: string; priority: string; notes: Array<{ id: number; author_name: string | null; content: string; created_at: string }>; history?: Array<{ id: number; user_name: string | null; action: string; description: string; created_at: string }> }
export type ModelMetadata = { model_name: string; model_version: string; algorithm: string; calibration: string; threshold: number; feature_count: number; features: string[]; supported_transaction_types: TransactionType[]; dataset: string | null; metrics: Record<string, number> | null; metrics_source: string; metrics_note: string; confusion_matrix: number[][] | null; limitations: string[]; calibrated: boolean | null; calibration_warning: string | null; training_versions: Record<string,string>; loading_status?: string }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}), ...init?.headers },
    })
  } catch {
    throw new Error('Could not reach the FraudShield API. Check the backend connection and try again.')
  }
  if (!response.ok) {
    const detail = await response.json().catch(() => null) as { detail?: string; message?: string } | null
    throw new Error(detail?.detail || detail?.message || `Request failed (${response.status}). Please try again.`)
  }
  return response.json() as Promise<T>
}

export const api = {
  login: (email: string, password: string) => request<LoginResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
  predict: (payload: PredictionRequest) => request<PredictionResponse>('/predictions/predict', { method: 'POST', body: JSON.stringify(payload) }),
  explain: (transaction_id: string) => request<ExplanationResponse>(`/predictions/explain/${encodeURIComponent(transaction_id)}`),
  transactions: (query = '') => request<Page<ApiTransaction>>(`/transactions${query ? `?${query}` : ''}`),
  transaction: (id: string) => request<ApiTransaction>(`/transactions/${encodeURIComponent(id)}`),
  transactionStats: () => request<Record<string, unknown>>('/transactions/stats'),
  dashboard: (days = 30) => request<Record<string, unknown>>(`/dashboard/summary?trend_days=${days}`),
  model: () => request<ModelMetadata>('/model/metadata'),
  investigations: (query = '') => request<Page<Investigation>>(`/investigations${query ? `?${query}` : ''}`),
  investigation: (id: string) => request<Investigation>(`/investigations/${encodeURIComponent(id)}`),
  createInvestigation: (payload: unknown) => request<Investigation>('/investigations', { method: 'POST', body: JSON.stringify(payload) }),
  updateInvestigation: (id: string, payload: unknown) => request<Investigation>(`/investigations/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  addInvestigationNote: (id: string, content: string) => request<Investigation['notes'][number]>(`/investigations/${encodeURIComponent(id)}/notes`, { method: 'POST', body: JSON.stringify({ content }) }),
  analysts: () => request<Array<{ id: number; full_name: string; role: string }>>('/users/analysts'),
  users: () => request<Page<{ id: number; email: string; full_name: string; role: string; is_active: boolean }>>('/users?page_size=100'),
  createUser: (payload: unknown) => request<LoginResponse['user']>('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  updateUser: (id: number, payload: unknown) => request<LoginResponse['user'] & { is_active: boolean }>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  auditLogs: () => request<Page<{ id: number; action: string; description: string; created_at: string; user_name?: string | null }>>('/users/audit-logs?page_size=100'),
  analytics: (name: string, query = '') => request<Record<string, any>>(`/analytics/${name}${query ? `?${query}` : ''}`),
  reportSummary: (query = '') => request<Record<string, any>>(`/reports/summary${query ? `?${query}` : ''}`),
  exportTransactions: async (query = '') => {
    let response: Response
    try { response = await fetch(`${API_BASE_URL}/reports/export?format=csv${query ? `&${query}` : ''}`, { headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {} }) }
    catch { throw new Error('Could not reach the FraudShield API. Check the backend connection and try again.') }
    if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail || `Request failed (${response.status}).`) }
    return response.blob()
  },
}
