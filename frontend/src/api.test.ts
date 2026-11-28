import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, setAccessToken } from './api'

describe('FraudShield API client', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken(null)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('logs in, sends the bearer token on protected calls, and logs out', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: 'unit-token', token_type: 'bearer', expires_in: 60, user: { id: 1, email: 'analyst@example.test', full_name: 'Analyst', role: 'fraud_analyst' } }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ transaction_id: 'TXN-1', prediction: 'Not Flagged', fraud_score: 0.1, threshold: 0.468, risk_level: 'Low', requires_investigation: false, transaction_type: 'PAYMENT', model_name: 'test', message: 'ok' }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ message: 'Logged out' }), { status: 200 }))

    await api.login('analyst@example.test', 'valid-password')
    setAccessToken('unit-token')
    await api.predict({ step: 1, amount: 10, oldbalanceOrg: 20, oldbalanceDest: 5, type_CASH_IN: 0, type_CASH_OUT: 0, type_DEBIT: 0, type_PAYMENT: 1, type_TRANSFER: 0 })
    await api.logout()

    expect(fetchMock).toHaveBeenCalledTimes(3)
    const login = fetchMock.mock.calls[0]
    expect(String(login[0])).toMatch(/\/api\/v1\/auth\/login$/)
    expect(JSON.parse(String(login[1]?.body))).toEqual({ email: 'analyst@example.test', password: 'valid-password' })
    expect(new Headers(fetchMock.mock.calls[1][1]?.headers).get('authorization')).toBe('Bearer unit-token')
    expect(String(fetchMock.mock.calls[2][0])).toMatch(/\/api\/v1\/auth\/logout$/)
  })

  it('requests stored SHAP details with an encoded transaction identifier', async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ transaction_id: 'TXN/1', features: [], warning: '' }), { status: 200 }))
    await api.explain('TXN/1')
    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/predictions\/explain\/TXN%2F1$/)
    expect(fetchMock.mock.calls[0][1]?.method).toBeUndefined()
  })

  it('surfaces backend errors and network failures without fabricating a result', async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Too many login attempts. Try again later.' }), { status: 429 }))
    await expect(api.login('analyst@example.test', 'bad')).rejects.toThrow('Too many login attempts')
    fetchMock.mockRejectedValueOnce(new TypeError('network down'))
    await expect(api.dashboard()).rejects.toThrow('Could not reach the FraudShield API')
  })
})
