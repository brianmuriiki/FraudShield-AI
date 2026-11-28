import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

const apiBase = `${process.env.FS_API_URL || 'http://127.0.0.1:8000'}/api/v1`
const email = 'audit-admin@test.local'
const password = 'Audit#Pass12345'

async function signIn(page: import('@playwright/test').Page) {
  await page.goto('/')
  await page.getByLabel('Work email').fill(email)
  await page.getByLabel('Password').fill(password)
  const response = page.waitForResponse(r => r.url() === `${apiBase}/auth/login` && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Sign in securely' }).click()
  const login = await response
  expect(login.status()).toBe(200)
  await expect(page.getByRole('heading', { name: 'FraudShield overview' })).toBeVisible()
  return (await login.json()).access_token as string
}

test('real login, invalid credentials, logout revocation and refresh behavior', async ({ page, request }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const documentResponse = await page.goto('/')
  expect(documentResponse).not.toBeNull()
  const documentHeaders = documentResponse!.headers()
  expect(documentHeaders['content-security-policy']).toContain("script-src 'self'")
  expect(documentHeaders['content-security-policy']).not.toContain("script-src 'self' 'unsafe-inline'")
  expect(documentHeaders['x-content-type-options']).toBe('nosniff')
  const health = await request.get(`${apiBase}/health`)
  expect(health.headers()['cache-control']).toBe('no-store')
  expect(health.headers()['x-frame-options']).toBe('DENY')
  await page.getByLabel('Work email').fill('unknown@test.local')
  await page.getByLabel('Password').fill('incorrect')
  const rejected = page.waitForResponse(r => r.url() === `${apiBase}/auth/login` && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Sign in securely' }).click()
  expect((await rejected).status()).toBe(401)
  await expect(page.getByRole('alert')).toContainText('Incorrect email or password')

  const token = await signIn(page)
  const dashboard = await request.get(`${apiBase}/dashboard/summary`, { headers: { Authorization: `Bearer ${token}` } })
  expect(dashboard.status()).toBe(200)
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  const revoked = await request.get(`${apiBase}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
  expect(revoked.status()).toBe(401)

  await signIn(page)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  expect(errors).toEqual([])
})

test('live dashboard and transaction filters show persisted backend records', async ({ page }) => {
  await signIn(page)
  await expect(page.getByText('Connected data')).toBeVisible()
  await page.getByRole('button', { name: 'Transactions' }).click()
  await expect(page.getByRole('heading', { name: 'Transaction stream' })).toBeVisible()
  await page.getByLabel('Search transaction reference').fill('TXN-NO-SUCH-RECORD')
  await expect(page.getByText('No backend transactions match these filters.')).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
})

test('real model prediction and SHAP explanation persist through backend API', async ({ page, request }) => {
  const token = await signIn(page)
  await page.getByRole('button', { name: 'Fraud detection' }).click()
  await expect(page.getByRole('heading', { name: 'Fraud detection lab' })).toBeVisible()
  await page.getByLabel('Transaction amount').fill('25000')
  await page.getByLabel('Transaction type').selectOption('CASH_OUT')
  await page.getByLabel('Transaction time step').fill('42')
  await page.getByLabel('Sender balance before transaction').fill('25000')
  await page.getByLabel('Recipient balance before transaction').fill('500')
  const predictionResponse = page.waitForResponse(r => r.url() === `${apiBase}/predictions/predict` && r.request().method() === 'POST')
  const explanationResponse = page.waitForResponse(r => /\/predictions\/explain\//.test(r.url()) && r.request().method() === 'GET')
  await page.getByRole('button', { name: 'Analyse transaction' }).click()
  const prediction = await predictionResponse
  const explanation = await explanationResponse
  expect(prediction.status()).toBe(200)
  expect(explanation.status()).toBe(200)
  const body = await prediction.json()
  const shap = await explanation.json()
  expect(body.transaction_id).toBeTruthy()
  expect(shap.features).toHaveLength(9)
  await expect(page.getByText('Backend prediction')).toBeVisible()
  await expect(page.getByText('Model explanation')).toBeVisible()
  const saved = await request.get(`${apiBase}/transactions/${body.transaction_id}`, { headers: { Authorization: `Bearer ${token}` } })
  expect(saved.status()).toBe(200)
  await page.screenshot({ path: '../reports/quality_audit/screenshots/prediction-and-shap.png', fullPage: true })
})

test('investigation CRUD, analytics export, model metadata, and admin user controls', async ({ page, request }) => {
  let adminToken = await signIn(page)
  const viewerEmail = `phase3-${Date.now()}@test.local`
  await page.getByRole('button', { name: 'Model intelligence' }).click()
  await expect(page.getByRole('heading', { name: 'XGBoost Fraud Detection Model' })).toBeVisible()
  await expect(page.getByText('3.4.1')).toBeVisible()
  await expect(page.getByText('80.32%')).toBeVisible()

  await page.getByRole('button', { name: 'Fraud detection' }).click()
  await page.getByLabel('Transaction amount').fill('14000')
  await page.getByLabel('Transaction type').selectOption('TRANSFER')
  await page.getByLabel('Transaction time step').fill('41')
  await page.getByLabel('Sender balance before transaction').fill('14000')
  await page.getByLabel('Recipient balance before transaction').fill('0')
  const createdResponse = page.waitForResponse(r => r.url() === `${apiBase}/predictions/predict` && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Analyse transaction' }).click()
  const prediction = await createdResponse
  expect(prediction.status()).toBe(200)
  const txRef = (await prediction.json()).transaction_id as string

  await page.getByRole('button', { name: 'Transactions' }).click()
  await page.getByLabel('Search transaction reference').fill(txRef)
  const openDetails = page.getByRole('button', { name: `View transaction ${txRef}` })
  await expect(openDetails).toBeVisible()
  await openDetails.click()
  const dialog = page.getByRole('dialog', { name: txRef })
  await expect(dialog.getByRole('button', { name: 'Close dialog' })).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()
  await openDetails.click()
  await page.getByRole('button', { name: /Open investigation/ }).click()
  const createCaseResponse = page.waitForResponse(r => r.url() === `${apiBase}/investigations` && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Create case' }).click()
  const caseResponse = await createCaseResponse
  expect(caseResponse.status()).toBe(201)
  const caseRef = (await caseResponse.json()).investigation_reference as string
  await expect(page.getByText('Investigation notes')).toBeVisible()
  const updateCase = async (label: string, value: string | { index: number }) => {
    const response = page.waitForResponse(r => r.url() === `${apiBase}/investigations/${caseRef}` && r.request().method() === 'PATCH')
    await page.getByLabel(label).selectOption(value)
    expect((await response).status()).toBe(200)
  }
  await updateCase('Investigation status', 'Under Review')
  await updateCase('Assign analyst', { index: 1 })
  await updateCase('Investigation priority', 'Critical')
  await page.getByLabel('New investigation note').fill('Reviewed transfer velocity with the payment operations team.')
  await page.getByRole('button', { name: 'Save note' }).click()
  await expect(page.getByText('Reviewed transfer velocity with the payment operations team.')).toBeVisible()
  await updateCase('Investigation outcome', 'Confirmed Fraud')
  await updateCase('Investigation status', 'Resolved')
  const persisted = await request.get(`${apiBase}/investigations`, { headers: { Authorization: `Bearer ${adminToken}` }, params: { transaction_id: txRef } })
  expect(persisted.status()).toBe(200)
  expect((await persisted.json()).items[0].status).toBe('Resolved')
  await updateCase('Investigation status', 'Closed')
  const closed = await request.get(`${apiBase}/investigations`, { headers: { Authorization: `Bearer ${adminToken}` }, params: { transaction_id: txRef } })
  expect((await closed.json()).items[0].status).toBe('Closed')

  await page.getByRole('button', { name: 'Analytics & reports' }).click()
  await page.getByLabel('Analytics transaction type').selectOption('TRANSFER')
  await expect(page.getByText('Report period: all available dates to present')).toBeVisible()
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download CSV report' }).click()
  expect((await download).suggestedFilename()).toBe('fraudshield_transactions.csv')

  await page.getByRole('button', { name: 'Team & system' }).click()
  await page.getByRole('button', { name: 'Create user' }).click()
  await page.getByLabel('Full name').fill('Phase Three Viewer')
  await page.getByLabel('Email').fill(viewerEmail)
  await page.getByLabel('Initial password').fill('Phase3#ViewerPass123')
  await page.locator('form select[name="role"]').selectOption('bi_analyst')
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByText(viewerEmail, { exact: true })).toBeVisible()
  const viewerLogin = await request.post(`${apiBase}/auth/login`, { data: { email: viewerEmail, password: 'Phase3#ViewerPass123' } })
  expect(viewerLogin.status()).toBe(200)
  const viewerToken = (await viewerLogin.json()).access_token as string
  expect((await request.get(`${apiBase}/users`, { headers: { Authorization: `Bearer ${viewerToken}` } })).status()).toBe(403)
  expect((await request.get(`${apiBase}/analytics/overview`, { headers: { Authorization: `Bearer ${viewerToken}` } })).status()).toBe(200)
  await page.getByRole('button', { name: 'Sign out' }).click()
  await page.getByLabel('Work email').fill(viewerEmail)
  await page.getByLabel('Password').fill('Phase3#ViewerPass123')
  await page.getByRole('button', { name: 'Sign in securely' }).click()
  await expect(page.getByRole('heading', { name: 'FraudShield overview' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Team & system' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Sign out' }).click()
  adminToken = await signIn(page)
  await page.getByRole('button', { name: 'Team & system' }).click()
  const viewerRow = page.locator('.person').filter({ hasText: viewerEmail })
  await viewerRow.locator('select').selectOption('fraud_analyst')
  await viewerRow.getByRole('button', { name: 'Deactivate' }).click()
  const users = await request.get(`${apiBase}/users`, { headers: { Authorization: `Bearer ${adminToken}` } })
  expect(users.status()).toBe(200)
  expect((await users.json()).items.some((user: {email:string;is_active:boolean}) => user.email === viewerEmail && !user.is_active)).toBe(true)
  expect((await request.post(`${apiBase}/auth/login`, { data: { email: viewerEmail, password: 'Phase3#ViewerPass123' } })).status()).toBe(401)
})

test('invalid prediction input and backend failure are announced', async ({ page }) => {
  await signIn(page)
  await page.getByRole('button', { name: 'Fraud detection' }).click()
  await page.getByLabel('Transaction amount').fill('-1')
  await page.getByLabel('Transaction time step').fill('1.5')
  expect(await page.getByLabel('Transaction amount').evaluate((e: HTMLInputElement) => e.validity.valid)).toBe(false)
  await page.getByLabel('Transaction amount').fill('100')
  await page.route(`${apiBase}/predictions/predict`, route => route.abort())
  await page.getByLabel('Transaction time step').fill('2')
  await page.getByLabel('Sender balance before transaction').fill('100')
  await page.getByLabel('Recipient balance before transaction').fill('0')
  await page.getByRole('button', { name: 'Analyse transaction' }).click()
  await expect(page.getByRole('alert')).toContainText('Could not reach the FraudShield API')
})

test('all primary pages show backend-connected states and pass axe scan', async ({ page }) => {
  test.setTimeout(90_000)
  const violations: string[] = []
  const scan = async (heading: string) => {
    const result = await new AxeBuilder({ page }).analyze()
    for (const violation of result.violations) {
      violations.push(`${heading}: ${violation.id} (${violation.impact}) - ${violation.nodes.map(node => node.target.join(' ')).join(', ')}`)
    }
  }
  await page.goto('/')
  await scan('Sign in')
  await signIn(page)
  await scan('Overview')
  const pages = [
    ['Transactions', 'Transaction stream'],
    ['Fraud detection', 'Fraud detection lab'],
    ['Investigations', 'Investigation workspace'],
    ['Analytics & reports', 'Risk intelligence'],
    ['Model intelligence', 'Model intelligence'],
    ['Team & system', 'Team & system'],
  ] as const
  for (const [navLabel, heading] of pages) {
    await page.getByRole('button', { name: navLabel }).click()
    await expect(page.getByRole('heading', { name: heading })).toBeVisible()
    const result = await new AxeBuilder({ page }).analyze()
    for (const violation of result.violations) {
      violations.push(`${heading}: ${violation.id} (${violation.impact}) - ${violation.nodes.map(node => node.target.join(' ')).join(', ')}`)
    }
  }
  await page.screenshot({ path: '../reports/quality_audit/screenshots/connected-pages.png', fullPage: true })
  expect(violations, violations.join('\n')).toEqual([])
})

test('keyboard focus reaches the sign-in controls visibly', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')
  await expect(page.getByLabel('Work email')).toBeFocused()
  const outline = await page.getByLabel('Work email').evaluate(e => getComputedStyle(e).outlineWidth)
  expect(outline).toBe('3px')
  await page.keyboard.press('Tab')
  await expect(page.getByLabel('Password')).toBeFocused()
})

test('mobile navigation remains operable at a narrow viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 })
  await signIn(page)
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeHidden()
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible()
  await page.getByRole('button', { name: 'Analytics & reports' }).click()
  await expect(page.getByRole('heading', { name: 'Risk intelligence' })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeHidden()
})
