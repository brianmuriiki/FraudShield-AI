const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export type TransactionType = 'CASH_IN' | 'CASH_OUT' | 'DEBIT' | 'PAYMENT' | 'TRANSFER'

export type PredictionRequest = {
  step: number
  amount: number
  oldbalanceOrg: number
  oldbalanceDest: number
} & Record<`type_${TransactionType}`, 0 | 1>

export type PredictionResponse = {
  risk_score: number
  threshold?: number
  prediction?: string
  status?: string
  transaction_id?: string
  explanation?: Array<{ feature: string; value: number | string; contribution: number; relative_influence?: number }>
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
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
  predict: (payload: PredictionRequest) => request<PredictionResponse>('/predictions/predict', { method: 'POST', body: JSON.stringify(payload) }),
  explain: (transaction_id: string) => request<{ explanation: PredictionResponse['explanation'] }>('/predictions/explain', { method: 'POST', body: JSON.stringify({ transaction_id }) }),
  transactions: (query = '') => request<unknown>(`/transactions${query ? `?${query}` : ''}`),
  transaction: (id: string) => request<unknown>(`/transactions/${encodeURIComponent(id)}`),
  dashboard: () => request<unknown>('/dashboard/summary'),
  model: () => request<unknown>('/model/metadata'),
  investigations: () => request<unknown>('/investigations'),
  createInvestigation: (payload: unknown) => request<unknown>('/investigations', { method: 'POST', body: JSON.stringify(payload) }),
  updateInvestigation: (id: string, payload: unknown) => request<unknown>(`/investigations/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(payload) }),
}
