import { FormEvent, ReactNode, useEffect, useState } from 'react'
import { api, setAccessToken, PredictionRequest, PredictionResponse, TransactionType, LoginResponse, ApiTransaction, Investigation as InvestigationRecord, ModelMetadata } from './api'

type IconName =
  | 'grid' | 'pulse' | 'scan' | 'case' | 'chart' | 'brain' | 'users' | 'settings'
  | 'search' | 'bell' | 'chevron' | 'arrow' | 'shield' | 'trend' | 'wallet'
  | 'alert' | 'check' | 'clock' | 'filter' | 'download' | 'more' | 'menu'
  | 'close' | 'eye' | 'lock' | 'plus' | 'file' | 'logout'

const paths: Record<IconName, ReactNode> = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
  pulse: <><path d="M3 12h4l2-6 4 12 2-6h6"/><circle cx="19" cy="5" r="2"/></>,
  scan: <><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><path d="M8 12h8M12 8v8"/></>,
  case: <><path d="M8 6V4h8v2"/><rect x="3" y="6" width="18" height="14" rx="3"/><path d="M3 12h18M10 12v2h4v-2"/></>,
  chart: <><path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/></>,
  brain: <><path d="M9 4a3 3 0 0 0-5 2 3 3 0 0 0 0 5 3 3 0 0 0 2 5 3 3 0 0 0 3 4M15 4a3 3 0 0 1 5 2 3 3 0 0 1 0 5 3 3 0 0 1-2 5 3 3 0 0 1-3 4M9 4v16M15 4v16M9 8H7M15 8h2M9 15H6M15 15h3"/></>,
  users: <><circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6M17 14a5 5 0 0 1 4 5v1"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a2 2 0 0 0 .4 2.2l.1.1-2.6 2.6-.1-.1a2 2 0 0 0-2.2-.4 2 2 0 0 0-1.2 1.8V21h-3.6v-.2A2 2 0 0 0 9 19a2 2 0 0 0-2.2.4l-.1.1-2.6-2.6.1-.1A2 2 0 0 0 4.6 15a2 2 0 0 0-1.8-1.2H2.6v-3.6h.2A2 2 0 0 0 4.6 9a2 2 0 0 0-.4-2.2l-.1-.1 2.6-2.6.1.1A2 2 0 0 0 9 4.6a2 2 0 0 0 1.2-1.8v-.2h3.6v.2A2 2 0 0 0 15 4.6a2 2 0 0 0 2.2-.4l.1-.1 2.6 2.6-.1.1a2 2 0 0 0-.4 2.2 2 2 0 0 0 1.8 1.2h.2v3.6h-.2A2 2 0 0 0 19.4 15Z"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>,
  chevron: <path d="m9 18 6-6-6-6"/>, arrow: <path d="M5 12h14M13 6l6 6-6 6"/>,
  shield: <><path d="M12 22S20 18 20 11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-5"/></>,
  trend: <><path d="m3 17 6-6 4 4 8-9"/><path d="M15 6h6v6"/></>,
  wallet: <><path d="M3 6h16a2 2 0 0 1 2 2v11H5a2 2 0 0 1-2-2V6Z"/><path d="M3 7V5a2 2 0 0 1 2-2h12v3M16 12h5"/></>,
  alert: <><path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5M12 18h.01"/></>,
  check: <path d="m5 12 4 4L19 6"/>, clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  filter: <path d="M3 5h18l-7 8v6l-4 2v-8L3 5Z"/>, download: <><path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 21h16"/></>,
  more: <><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>,
  menu: <path d="M4 6h16M4 12h16M4 18h16"/>, close: <path d="m5 5 14 14M19 5 5 19"/>,
  eye: <><path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2"/></>,
  lock: <><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></>,
  plus: <path d="M12 5v14M5 12h14"/>, file: <><path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5M9 13h6M9 17h6"/></>,
  logout: <><path d="M10 4H5v16h5M14 8l4 4-4 4M18 12H9"/></>,
}

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}

const nav = [
  { id: 'dashboard', label: 'Overview', icon: 'grid' },
  { id: 'transactions', label: 'Transactions', icon: 'pulse' },
  { id: 'detection', label: 'Fraud detection', icon: 'scan' },
  { id: 'investigations', label: 'Investigations', icon: 'case' },
  { id: 'analytics', label: 'Analytics & reports', icon: 'chart' },
  { id: 'models', label: 'Model intelligence', icon: 'brain' },
  { id: 'management', label: 'Team & system', icon: 'users' },
] as const

const riskClass = (score: number) => score >= 85 ? 'critical' : score >= 60 ? 'warning' : 'safe'

function Logo({ compact = false }: { compact?: boolean }) {
  return <div className="logo"><div className="logo-mark"><Icon name="shield" size={20}/></div>{!compact && <div><b>FRAUDSHIELD</b><span>AI</span></div>}</div>
}

function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}><i />{children}</span>
}

function PageTitle({ eyebrow, title, subtitle, action }: { eyebrow: string; title: string; subtitle: string; action?: ReactNode }) {
  return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>
}

function Dashboard({ go }: { go: (id: string) => void }) {
  const [data, setData] = useState<Record<string, any> | null>(null)
  const [rows, setRows] = useState<ApiTransaction[]>([])
  const [error, setError] = useState('')
  useEffect(() => { Promise.all([api.dashboard(), api.transactions('page_size=5&sort_by=fraud_score')]).then(([summary, page]) => { setData(summary); setRows(page.items) }).catch(e => setError(e.message)) }, [])
  const count = (key: string) => data ? Number(data[key] ?? 0).toLocaleString() : '—'
  const money = (v: unknown) => typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'
  const riskTotal = Object.values(data?.risk_level_distribution || {}).reduce((sum: number, value: any) => sum + Number(value), 0)
  return <>
    <PageTitle eyebrow="Risk command" title="FraudShield overview" subtitle="Live transaction and investigation totals from the backend." action={<Badge tone={data ? 'safe' : 'warning'}>{data ? 'Connected data' : 'Loading data'}</Badge>}/>
    {error && <p className="api-message error" role="alert">{error}</p>}
    <div className="metrics">
      <Metric icon="pulse" label="Transactions analysed" value={count('total_transactions')} note="Stored predictions" tone="blue"/>
      <Metric icon="alert" label="Model flagged" value={count('suspicious_transactions')} note="Requires human review" tone="orange"/>
      <Metric icon="shield" label="Confirmed fraud cases" value={count('confirmed_fraud_cases')} note="Analyst verified" tone="red"/>
      <Metric icon="wallet" label="Value monitored" value={money(data?.total_amount)} note="Summed transaction amount" tone="green"/>
    </div>
    <div className="dashboard-grid">
      <section className="card"><CardHead title="Risk distribution" subtitle="Stored transaction risk categories"/>{Object.entries(data?.risk_level_distribution || {}).map(([name,value])=><Bar key={name} label={name} value={riskTotal?100*Number(value)/riskTotal:0} count={String(value)}/>)}</section>
      <section className="card"><CardHead title="Investigation queue"/><div className="case-meta"><Detail label="Pending" value={count('pending_investigations')}/><Detail label="Open" value={count('open_investigations')}/><Detail label="Resolved or closed" value={count('resolved_investigations')}/></div><button className="text-btn" onClick={() => go('investigations')}>Open investigations <Icon name="arrow" size={15}/></button></section>
      <section className="card span-2"><CardHead title="Recent transactions" subtitle="Stored backend records" right={<button className="text-btn" onClick={() => go('transactions')}>View all <Icon name="arrow" size={15}/></button>}/>{rows.length ? <div className="table-scroll"><table><thead><tr><th>Reference</th><th>Type</th><th>Amount</th><th>Score</th><th>Prediction</th></tr></thead><tbody>{rows.map(t=><tr key={t.id}><td><button className="transaction-open" onClick={()=>go('transactions')}>{t.transaction_id}</button></td><td>{t.transaction_type}</td><td>{money(t.amount)}</td><td>{(t.fraud_score*100).toFixed(1)}%</td><td>{t.prediction}</td></tr>)}</tbody></table></div>:<p className="unavailable">No transaction records available.</p>}</section>
      <section className="card intelligence"><div className="ai-icon"><Icon name="brain" size={24}/></div><div className="eyebrow">Model status</div><h3>Model details</h3><p>View metadata and offline evaluation supplied by the loaded model artifacts.</p><button className="dark-btn" onClick={() => go('models')}>View model details <Icon name="arrow" size={16}/></button></section>
    </div>
  </>
}

function Metric({ icon, label, value, note, tone }: { icon: IconName; label: string; value: string; note: string; tone: string }) {
  return <div className="metric card"><div className={`metric-icon ${tone}`}><Icon name={icon}/></div><span>{label}</span><strong>{value}</strong><small className={tone === 'red' || tone === 'orange' ? 'hot' : ''}><Icon name="trend" size={13}/>{note}</small></div>
}

function CardHead({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return <div className="card-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{right}</div>
}

function Transactions({ openDetail }: { openDetail: (id: string) => void }) {
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('All types')
  const [statusFilter, setStatusFilter] = useState('All predictions')
  const [data, setData] = useState<{items: ApiTransaction[]; total: number}>({items:[],total:0})
  const [error, setError] = useState('')
  const load = () => {
    const params = new URLSearchParams({ page_size: '100' })
    if (query) params.set('search', query)
    if (typeFilter !== 'All types') params.set('transaction_type', typeFilter.toUpperCase().replace(/ /g, '_'))
    if (statusFilter !== 'All predictions') params.set('prediction', statusFilter === 'Suspicious' ? 'Suspicious' : 'Not Flagged')
    api.transactions(params.toString()).then(page => { setData({items:page.items,total:page.total}); setError('') }).catch(e => setError(e.message))
  }
  useEffect(() => { load() }, [query, typeFilter, statusFilter])
  return <>
    <PageTitle eyebrow="Transaction monitoring" title="Transaction stream" subtitle="Search persisted transactions and review model decisions." action={<Badge>Backend records</Badge>}/>
    <div className="filter-bar card"><div className="search-field"><Icon name="search"/><input aria-label="Search transaction reference" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search transaction reference"/></div><select aria-label="Filter by transaction type" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}><option>All types</option>{['Cash in','Cash out','Debit','Payment','Transfer'].map(t=><option key={t}>{t}</option>)}</select><select aria-label="Filter by prediction status" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}><option>All predictions</option><option>Suspicious</option><option>Not Flagged</option></select></div>
    {error && <p className="api-message error" role="alert">{error}</p>}
    <section className="card table-card"><div className="table-summary"><div><b>{data.total} transactions</b><span>Persisted records · model flags are not verified outcomes</span></div></div>{data.items.length ? <div className="table-scroll"><table><thead><tr><th>Reference</th><th>Type</th><th>Amount</th><th>Created</th><th>Risk score</th><th>Prediction</th></tr></thead><tbody>{data.items.map(t=><tr key={t.id}><td><button className="transaction-open" aria-label={`View transaction ${t.transaction_id}`} onClick={()=>openDetail(t.transaction_id)}>{t.transaction_id}</button></td><td>{t.transaction_type}</td><td>{t.amount.toLocaleString()}</td><td>{new Date(t.created_at).toLocaleString()}</td><td>{(t.fraud_score*100).toFixed(1)}%</td><td><Badge tone={t.prediction==='Suspicious'?'critical':'safe'}>{t.prediction}</Badge></td></tr>)}</tbody></table></div>:<p className="unavailable">No backend transactions match these filters.</p>}<div className="pagination"><span>Showing {data.items.length} of {data.total} records</span></div></section>
  </>
}

function DetailDrawer({ id, close, investigate }: { id: string; close: () => void; investigate: () => void }) {
  const [t,setT]=useState<ApiTransaction|null>(null)
  const [error,setError]=useState('')
  useEffect(()=>{api.transaction(id).then(setT).catch(e=>setError(e.message))},[id])
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    const focusable = () => dialog?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')
    focusable()?.[0]?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { close(); return }
      if (event.key !== 'Tab') return
      const items = focusable()
      if (!items?.length) { event.preventDefault(); dialog?.focus(); return }
      const first = items[0], last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => { document.removeEventListener('keydown', onKeyDown); previous?.focus() }
  }, [])
  return <div className="drawer-layer" onMouseDown={e => e.target === e.currentTarget && close()}><aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="transaction-detail-title">
    <div className="drawer-head"><div><div className="eyebrow">Transaction detail</div><h2 id="transaction-detail-title">{t?.transaction_id||id}</h2></div><button className="icon-btn" onClick={close} aria-label="Close dialog"><Icon name="close"/></button></div>
    {error&&<p role="alert" className="api-message error">{error}</p>}{!t?<p>Loading transaction…</p>:<>
    <div className={`risk-hero ${riskClass(t.fraud_score*100)}`}><div className="risk-ring"><strong>{(t.fraud_score*100).toFixed(1)}</strong><span>/ 100</span></div><div><Badge tone={riskClass(t.fraud_score*100)}>{t.prediction}</Badge><h3>{t.risk_level} model risk</h3><p>This is a model estimate, not a confirmed fraud outcome.</p></div></div>
    <div className="detail-section"><h3>Transaction information</h3><div className="detail-grid"><Detail label="Reference" value={t.transaction_id}/><Detail label="Amount" value={t.amount.toLocaleString()}/><Detail label="Type" value={t.transaction_type}/><Detail label="Timestamp" value={new Date(t.created_at).toLocaleString()}/><Detail label="Investigation status" value={t.investigation_status}/><Detail label="Threshold" value={t.threshold.toFixed(3)}/></div></div>
    <div className="detail-section"><h3>Investigation outcome</h3><p className="unavailable">Model prediction and investigator-confirmed outcome are separate records.</p></div>
    </>}
    <div className="drawer-actions"><button className="secondary-btn" onClick={close}>Close details</button><button className="primary-btn" onClick={investigate}>Open investigation <Icon name="arrow"/></button></div>
  </aside></div>
}

function Detail({ label, value }: { label: string; value: string }) { return <div><span>{label}</span><b>{value}</b></div> }
function Indicator({ value, title, text }: { value: number; title: string; text: string }) { return <div className="indicator"><strong>{value}</strong><div><b>{title}</b><span>{text}</span></div></div> }

function Detection() {
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [submitted, setSubmitted] = useState<{ amount: number; type: TransactionType; step: number; oldbalanceOrg: number; oldbalanceDest: number } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const type = String(form.get('type')) as TransactionType
    const amount = Number(form.get('amount'))
    const step = Number(form.get('step'))
    const oldbalanceOrg = Number(form.get('oldbalanceOrg'))
    const oldbalanceDest = Number(form.get('oldbalanceDest'))
    if (![amount, step, oldbalanceOrg, oldbalanceDest].every(Number.isFinite) || amount < 0 || step < 0 || !Number.isInteger(step) || oldbalanceOrg < 0 || oldbalanceDest < 0) {
      setError('Enter a non-negative amount and balances, and a non-negative whole-number time step.')
      return
    }
    const payload: PredictionRequest = { step, amount, oldbalanceOrg, oldbalanceDest, type_CASH_IN: 0, type_CASH_OUT: 0, type_DEBIT: 0, type_PAYMENT: 0, type_TRANSFER: 0 }
    payload[`type_${type}`] = 1
    setLoading(true); setError(''); setNotice(''); setResult(null); setSubmitted({ amount, type, step, oldbalanceOrg, oldbalanceDest })
    try {
      const prediction = await api.predict(payload)
      if (!Number.isFinite(prediction.fraud_score) || prediction.fraud_score < 0 || prediction.fraud_score > 1) throw new Error('The API returned an invalid risk score. No prediction is displayed.')
      let features: PredictionResponse['features']
      try { features = (await api.explain(prediction.transaction_id)).features }
      catch { features = undefined }
      setResult({ ...prediction, features })
      setNotice('Prediction received from the backend.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed. Please try again.')
      setSubmitted(null)
    } finally { setLoading(false) }
  }
  const score = result?.fraud_score ?? 0
  const suspicious = result?.prediction === 'Suspicious'
  const typeLabels: Record<TransactionType, string> = { CASH_IN: 'Cash in', CASH_OUT: 'Cash out', DEBIT: 'Debit', PAYMENT: 'Payment', TRANSFER: 'Transfer' }
  return <>
    <PageTitle eyebrow="On-demand analysis" title="Fraud detection lab" subtitle="Evaluate an individual transaction with the active machine learning model."/>
    <div className="detection-grid">
      <form className="card form-card" onSubmit={submit}><CardHead title="Transaction information" subtitle="These five values are encoded as the model’s nine expected features."/>
        <div className="form-grid"><label>Transaction amount<input name="amount" type="number" min="0" step="any" required placeholder="e.g. 18450.00"/></label><label>Transaction type<select name="type" defaultValue="CASH_OUT">{(['CASH_IN','CASH_OUT','DEBIT','PAYMENT','TRANSFER'] as TransactionType[]).map(t => <option key={t} value={t}>{typeLabels[t]}</option>)}</select></label><label>Transaction time step<input name="step" type="number" min="0" step="1" required placeholder="Non-negative whole number"/></label><label>Sender balance before transaction<input name="oldbalanceOrg" type="number" min="0" step="any" required placeholder="e.g. 50000.00"/></label><label>Recipient balance before transaction<input name="oldbalanceDest" type="number" min="0" step="any" required placeholder="e.g. 12000.00"/></label></div>
        <div className="privacy-note"><Icon name="lock"/><span><b>Model input</b> Only the supported transaction values are sent to the prediction endpoint.</span></div>
        {error && <p className="api-message error" role="alert">{error}</p>}
        {notice && <p className="api-message success" role="status">{notice}</p>}
        <button className="primary-btn wide" type="submit" disabled={loading}><Icon name="scan"/>{loading ? 'Requesting prediction…' : 'Analyse transaction'}</button>
      </form>
      <section className={`card result-card ${result ? 'has-result' : ''}`}>{!result ? <div className="empty-result"><div><Icon name="brain" size={34}/></div><h3>{loading ? 'Requesting prediction' : 'Ready to analyse'}</h3><p>{loading ? 'Waiting for the calibrated model response.' : 'Submit the five transaction values to request a risk score from the backend.'}</p><span>Risk score is an estimate, not confirmation of fraud.</span></div> : <>
        <div className="result-top"><span>Backend prediction</span><Badge tone={suspicious ? 'critical' : 'safe'}>{suspicious ? 'Suspicious · requires investigation' : 'Not flagged by the model'}</Badge></div><div className="big-score"><div><strong>{(score * 100).toFixed(1)}</strong><span>/100</span></div><p>{suspicious ? 'Elevated risk' : 'Below decision threshold'}</p></div>
        <div className="confidence"><span><b>Fraud-risk score · threshold {(result.threshold ?? 0.468).toFixed(3)}</b><b>{score.toFixed(6)}</b></span><i><em style={{ width: `${score * 100}%` }}/></i></div>
        <div className="detail-grid"><Detail label="Amount" value={submitted ? submitted.amount.toLocaleString() : '—'}/><Detail label="Type" value={submitted ? typeLabels[submitted.type] : '—'}/><Detail label="Time step" value={String(submitted?.step ?? '—')}/><Detail label="Sender balance" value={String(submitted?.oldbalanceOrg ?? '—')}/><Detail label="Recipient balance" value={String(submitted?.oldbalanceDest ?? '—')}/></div>
        <div className="explanation"><h3>Model explanation</h3><p>SHAP contributions explain model behavior in raw XGBoost score space; they do not prove fraud.</p>{result.features?.length ? result.features.map(item => <div className="shap-row" key={item.feature}><b>{item.feature}</b><span>Value: {item.value}</span><strong className={item.contribution >= 0 ? 'positive' : 'negative'}>{item.contribution >= 0 ? '+' : ''}{item.contribution.toFixed(4)} · {item.influence.toLowerCase()}</strong><small>{item.description}</small></div>) : <span>SHAP explanation is unavailable. The backend prediction is still valid.</span>}</div>
        <div className="recommendation"><Icon name="alert"/><div><b>Investigation status</b><p>{suspicious ? 'Review the transaction with an authorized investigator. This result is not a confirmed fraud outcome.' : 'This transaction was not flagged by the model.'}</p></div></div>
      </>}</section>
    </div>
  </>
}

function Investigations({ initialTransactionId, role }: { initialTransactionId?: string | null; role: string }) {
  const canManage = role === 'administrator' || role === 'senior_analyst'
  const [records, setRecords] = useState<InvestigationRecord[]>([])
  const [selected, setSelected] = useState<InvestigationRecord | null>(null)
  const [analysts, setAnalysts] = useState<Array<{id:number;full_name:string;role:string}>>([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [refresh, setRefresh] = useState(0)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [transactionId, setTransactionId] = useState(initialTransactionId || '')
  const load = () => api.investigations(new URLSearchParams({page_size:'100', ...(search?{search}:{})}).toString()).then(p=>setRecords(p.items)).catch(e=>setError(e.message))
  useEffect(() => { load() }, [search, refresh])
  useEffect(() => { api.analysts().then(setAnalysts).catch(()=>setAnalysts([])) }, [])
  useEffect(() => { if(initialTransactionId) setTransactionId(initialTransactionId) }, [initialTransactionId])
  const select = (id: string) => api.investigation(id).then(setSelected).catch(e=>setError(e.message))
  const create = async (e: FormEvent) => { e.preventDefault(); try { const created=await api.createInvestigation({transaction_id:transactionId}); setSelected(created); setTransactionId(''); setRefresh(x=>x+1); setError('') } catch(e) { setError(e instanceof Error?e.message:'Could not create investigation') } }
  const update = async (payload: Record<string, unknown>) => { if(!selected||saving) return; setSaving(true); try { setSelected(await api.updateInvestigation(selected.investigation_reference,payload)); setRefresh(x=>x+1); setError('') } catch(e) { setError(e instanceof Error?e.message:'Update failed') } finally { setSaving(false) } }
  const addNote = async (e: FormEvent) => { e.preventDefault(); if(!selected) return; try { await api.addInvestigationNote(selected.investigation_reference,note); setNote(''); await select(selected.investigation_reference); setError('') } catch(e) { setError(e instanceof Error?e.message:'Could not save note') } }
  const statusChoices = selected ? (canManage ? ['New','Under Review','Escalated','Resolved','Closed'] : ['New','Under Review','Escalated'].includes(selected.status) ? ['New','Under Review','Escalated'] : [selected.status]) : []
  return <>
    <PageTitle eyebrow="Case workspace" title="Investigation workspace" subtitle="Persisted cases, analyst notes, assignments, statuses, and outcomes." action={<Badge>Backend records</Badge>}/>
    {error && <p className="api-message error" role="alert">{error}</p>}
    <div className="case-layout">
      <div className="case-main">
        <section className="card"><CardHead title="Investigation queue" subtitle={`${records.length} records`} right={<input aria-label="Search investigations" placeholder="Search reference" value={search} onChange={e=>setSearch(e.target.value)}/>}/>{records.length?<div className="table-scroll"><table><thead><tr><th>Case</th><th>Transaction</th><th>Status</th><th>Priority</th><th>Assignee</th></tr></thead><tbody>{records.map(r=><tr key={r.id}><td><button className="transaction-open" onClick={()=>select(r.investigation_reference)}>{r.investigation_reference}</button></td><td>{r.transaction_id}</td><td>{r.status}</td><td>{r.priority}</td><td>{r.assigned_analyst?.full_name||'Unassigned'}</td></tr>)}</tbody></table></div>:<p className="unavailable">No investigations found.</p>}</section>
        <form className="card form-card" onSubmit={create}><CardHead title="Create investigation" subtitle="Enter a persisted transaction reference"/><div className="search-field"><input aria-label="Transaction reference for investigation" required value={transactionId} onChange={e=>setTransactionId(e.target.value)} placeholder="TXN-…"/><button className="primary-btn" type="submit">Create case</button></div></form>
        {selected && <><section className="card"><CardHead title={selected.investigation_reference} subtitle={`Transaction ${selected.transaction_id}`}/><div className="case-meta"><Detail label="Status" value={selected.status}/><Detail label="Outcome" value={selected.outcome}/><Detail label="Priority" value={selected.priority}/><Detail label="Assigned analyst" value={selected.assigned_analyst?.full_name||'Unassigned'}/></div><div className="form-grid">
          <label>Status<select aria-label="Investigation status" disabled={saving||(!canManage&&['Resolved','Closed'].includes(selected.status))} value={selected.status} onChange={e=>update({status:e.target.value})}>{statusChoices.map(x=><option key={x}>{x}</option>)}</select></label>
          {canManage&&<><label>Outcome<select aria-label="Investigation outcome" disabled={saving} value={selected.outcome} onChange={e=>update({outcome:e.target.value})}>{['Pending','Confirmed Fraud','Legitimate Transaction','Inconclusive'].map(x=><option key={x}>{x}</option>)}</select></label><label>Priority<select aria-label="Investigation priority" disabled={saving} value={selected.priority} onChange={e=>update({priority:e.target.value})}>{['Low','Medium','High','Critical'].map(x=><option key={x}>{x}</option>)}</select></label><label>Assign analyst<select aria-label="Assign analyst" disabled={saving} value={selected.assigned_analyst_id||''} onChange={e=>update({assigned_analyst_id:e.target.value?Number(e.target.value):null})}><option value="">Unassigned</option>{analysts.map(a=><option value={a.id} key={a.id}>{a.full_name}</option>)}</select></label></>}
        </div>{saving&&<p role="status">Saving case update…</p>}</section>
          <section className="card"><CardHead title="Investigation notes" subtitle="Persisted internal case notes"/>{selected.notes.map(n=><p key={n.id}><b>{n.author_name||'Analyst'}</b> · {new Date(n.created_at).toLocaleString()}<br/>{n.content}</p>)}<form onSubmit={addNote}><label>Add note<textarea aria-label="New investigation note" required maxLength={5000} value={note} onChange={e=>setNote(e.target.value)}/></label><button className="primary-btn" type="submit">Save note</button></form></section><section className="card"><CardHead title="Activity history"/>{(selected.history||[]).map(h=><p key={h.id}>{new Date(h.created_at).toLocaleString()} · {h.user_name||'System'} · {h.description}</p>)}</section></>}
      </div>
      <aside className="case-side"><section className="card"><CardHead title="Case controls"/><p>Outcome and assignment permissions are enforced by the backend role policy.</p><button className="secondary-btn" disabled={!selected} onClick={()=>setSelected(null)}>Clear selection</button></section></aside>
    </div>
  </>
}

function Timeline({ time, icon, title, text, tone }: { time: string; icon: IconName; title: string; text: string; tone: string }) {
  return <div className="timeline-item"><time>{time}</time><div className={`timeline-icon ${tone}`}><Icon name={icon}/></div><div><b>{title}</b><p>{text}</p></div></div>
}

function Analytics() {
  const [dates, setDates] = useState({from:'',to:''})
  const [data, setData] = useState<Record<string,any>>({})
  const [typeFilter, setTypeFilter] = useState('All types')
  const [error, setError] = useState('')
  const query = new URLSearchParams({...(dates.from?{date_from:dates.from}:{}),...(dates.to?{date_to:dates.to}:{})}).toString()
  const load = () => Promise.all([...['overview','transactions','fraud-trends','transaction-types','investigations'].map(n=>api.analytics(n,query)),api.reportSummary(query)]).then(([overview,transactions,trends,types,investigations,report])=>setData({overview,transactions,trends,types,investigations,report})).catch(e=>setError(e.message))
  useEffect(()=>{ load() },[dates.from,dates.to])
  const download = async () => { try { const blob=await api.exportTransactions(query); const href=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=href; a.download='fraudshield_transactions.csv'; a.click(); URL.revokeObjectURL(href); setError('') } catch(e) { setError(e instanceof Error?e.message:'Report export failed') } }
  const types = (data.types?.types||[]).filter((x:any)=>typeFilter==='All types'||x.transaction_type===typeFilter)
  return <>
    <PageTitle eyebrow="Analytics & reporting" title="Risk intelligence" subtitle="Date-filtered aggregates computed from persisted transactions and investigations." action={<Badge>Backend analytics</Badge>}/>
    {error && <p className="api-message error" role="alert">{error}</p>}
    <section className="card form-grid"><label>From<input aria-label="Analytics start date" type="date" value={dates.from} onChange={e=>setDates({...dates,from:e.target.value})}/></label><label>To<input aria-label="Analytics end date" type="date" value={dates.to} onChange={e=>setDates({...dates,to:e.target.value})}/></label><label>Transaction type<select aria-label="Analytics transaction type" value={typeFilter} onChange={e=>setTypeFilter(e.target.value)}><option>All types</option>{(data.types?.types||[]).map((x:any)=><option key={x.transaction_type}>{x.transaction_type}</option>)}</select></label><button className="primary-btn" onClick={download}><Icon name="download"/>Download CSV report</button><span>Report period: {data.report?.period?.date_from||'all available dates'} to {data.report?.period?.date_to||'present'}</span></section>
    <div className="metrics"><Metric icon="pulse" label="Transactions" value={String(data.overview?.total_transactions??'—')} note="Filtered period" tone="blue"/><Metric icon="alert" label="Model flagged" value={String(data.overview?.suspicious_transactions??'—')} note="Not verified fraud" tone="orange"/><Metric icon="shield" label="Confirmed fraud" value={String(data.overview?.confirmed_fraud_cases??'—')} note="Analyst outcomes" tone="red"/><Metric icon="wallet" label="Average amount" value={data.overview?.average_amount==null?'—':Number(data.overview.average_amount).toLocaleString()} note="Filtered period" tone="green"/></div>
    <div className="analytics-grid"><section className="card span-2"><CardHead title="Transaction and model-flag counts by day" subtitle="Source: persisted transaction timestamps"/>{(data.transactions?.volume_over_time||[]).map((x:any)=><Bar key={x.date} label={`${x.date} · ${x.suspicious} flagged`} value={data.overview?.total_transactions?100*x.total/data.overview.total_transactions:0} count={String(x.total)}/>)}{!data.transactions&&<p className="unavailable">Loading analytics…</p>}</section><section className="card"><CardHead title="Transaction type" subtitle="Counts and values in selected period"/>{types.map((x:any)=><div key={x.transaction_type}><Bar label={x.transaction_type} value={data.overview?.total_transactions?100*x.total/data.overview.total_transactions:0} count={String(x.total)}/><small>{x.suspicious} flagged · {x.confirmed_fraud} confirmed</small></div>)}</section><section className="card"><CardHead title="Investigation outcomes"/>{Object.entries(data.investigations?.by_outcome||{}).map(([name,value])=><Bar key={name} label={name} value={Number(value)} count={String(value)}/>)}<p>Average resolution: {data.investigations?.average_resolution_hours==null?'Unavailable':`${Number(data.investigations.average_resolution_hours).toFixed(1)} hours`}</p></section><section className="card span-2"><CardHead title="Verified operational performance" subtitle="Only cases with analyst-confirmed or legitimate outcomes"/>{data.overview?.verified_performance&&<><p>{data.overview.verified_performance.caveat}</p><div className="model-metrics">{['verified_cases','true_positives','false_positives','false_negatives','precision','recall'].map(k=><ModelMetric key={k} label={k.replace(/_/g,' ')} value={data.overview.verified_performance[k]==null?'—':String(data.overview.verified_performance[k])} change="verified cases"/>)}</div></>}</section></div>
  </>
}
function Bar({ label, value, count }: { label: string; value: number; count: string }) { return <div className="bar-row"><span>{label}</span><div><i style={{width:`${value}%`}}/></div><b>{count}</b></div> }
function Region({ name, count, value }: { name: string; count: string; value: number }) { return <div className="region"><div><b>{name}</b><span>{count}</span></div><strong>{value}</strong><div className="region-bar"><i style={{width:`${value}%`}}/></div></div> }

function Models() {
  const [model, setModel] = useState<ModelMetadata | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { api.model().then(setModel).catch(e=>setError(e.message)) }, [])
  const labels: Record<string,string> = {precision:'Precision',recall:'Recall',f1_score:'F1 score',roc_auc:'ROC-AUC',pr_auc:'PR-AUC',brier_score:'Brier score',log_loss:'Log loss'}
  return <>
    <PageTitle eyebrow="Machine learning operations" title="Model intelligence" subtitle="Metadata read from the loaded model artifacts." action={<Badge tone={model?'safe':'warning'}>{model?'Loaded':'Loading or unavailable'}</Badge>}/>
    {error && <p className="api-message error" role="alert">{error}</p>}
    {model && <><section className="card model-head"><div className="model-identity"><div className="ai-icon"><Icon name="brain" size={26}/></div><div><span>{model.algorithm} · version {model.model_version}</span><h2>{model.model_name}</h2><p>{model.calibrated?'Calibrated model':'Calibration status unavailable'} · {model.dataset||'Training dataset not recorded'}</p></div></div><div className="model-status"><Badge tone="safe">Backend loaded</Badge></div></section>
    {model.calibration_warning&&<div className="demo-banner"><Icon name="alert"/><span><b>Artifact note</b> — {model.calibration_warning}</span></div>}
    <div className="model-grid"><section className="card span-2"><CardHead title="Verified offline evaluation" subtitle={model.metrics_note}/>{model.metrics&&Object.entries(model.metrics).length?<div className="model-metrics">{Object.entries(model.metrics).map(([key,value])=><ModelMetric key={key} label={labels[key]||key} value={['brier_score','log_loss'].includes(key)?Number(value).toFixed(6):`${(Number(value)*100).toFixed(2)}%`} change="offline metadata"/>)}</div>:<p className="unavailable">No evaluation metrics were found in the model metadata.</p>}</section>
      <section className="card"><CardHead title="Model configuration"/><div className="case-meta"><Detail label="Status" value="Loaded"/><Detail label="Input features" value={String(model.feature_count)}/><Detail label="Decision threshold" value={model.threshold.toFixed(3)}/><Detail label="Scoring rule" value={`Flag at or above ${model.threshold.toFixed(3)}`}/></div></section>
      <section className="card"><CardHead title="Supported features"/><ul>{model.features.map(f=><li key={f}>{f}</li>)}</ul><p>Supported transaction types: {model.supported_transaction_types.join(', ')}</p></section>
      <section className="card"><CardHead title="Training artifact versions"/><pre>{JSON.stringify(model.training_versions,null,2)}</pre><p>{model.metrics_source==='model metadata'?'Metrics source: trusted model metadata':'Verified metrics unavailable'}</p></section>
    </div>
    </>}
  </>
}
function ModelMetric({label,value,change}:{label:string;value:string;change:string}) { return <div><span>{label}</span><strong>{value}</strong><small>{change === 'offline' ? 'Historical offline test' : change}</small></div> }
function Version({version,date,f1,auc,status}:{version:string;date:string;f1:string;auc:string;status:string}) { return <div className="version-row"><b>{version}</b><span>{date}</span><span>F1 <b>{f1}</b></span><span>ROC-AUC <b>{auc}</b></span><Badge tone={status==='Production'?'safe':'neutral'}>{status}</Badge><Icon name="chevron"/></div> }

function Management() {
  const [users,setUsers]=useState<Array<{id:number;email:string;full_name:string;role:string;is_active:boolean}>>([])
  const [logs,setLogs]=useState<Array<{id:number;action:string;description:string;created_at:string;user_name?:string|null}>>([])
  const [error,setError]=useState('')
  const [showForm,setShowForm]=useState(false)
  const [refresh,setRefresh]=useState(0)
  useEffect(()=>{ Promise.all([api.users(),api.auditLogs()]).then(([u,a])=>{setUsers(u.items);setLogs(a.items)}).catch(e=>setError(e.message)) },[refresh])
  const create=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();const d=new FormData(e.currentTarget);try{await api.createUser({email:d.get('email'),full_name:d.get('full_name'),password:d.get('password'),role:d.get('role')});setShowForm(false);setRefresh(x=>x+1);setError('')}catch(e){setError(e instanceof Error?e.message:'User creation failed')}}
  const update=async(id:number,payload:Record<string,unknown>)=>{try{await api.updateUser(id,payload);setRefresh(x=>x+1);setError('')}catch(e){setError(e instanceof Error?e.message:'User update failed')}}
  return <>
    <PageTitle eyebrow="Administration" title="Team & system" subtitle="Administrator-only user creation, role changes, deactivation, and audit history." action={<button className="primary-btn" onClick={()=>setShowForm(!showForm)}><Icon name="plus"/>Create user</button>}/>
    {error && <p className="api-message error" role="alert">{error}</p>}
    {showForm&&<form className="card form-grid" onSubmit={create}><label>Full name<input name="full_name" required maxLength={255}/></label><label>Email<input name="email" type="email" required/></label><label>Initial password<input name="password" type="password" required minLength={12}/></label><label>Role<select name="role" defaultValue="bi_analyst">{['administrator','senior_analyst','fraud_analyst','bi_analyst'].map(r=><option key={r}>{r}</option>)}</select></label><button className="primary-btn" type="submit">Create account</button></form>}
    <div className="admin-grid"><section className="card span-2"><CardHead title="Team members" subtitle={`${users.filter(u=>u.is_active).length} active · ${users.length} total`}/><div className="people">{users.map(u=><div className="person" key={u.id}><span className="avatar">{u.full_name.split(/\s+/).map(s=>s[0]).slice(0,2).join('')}</span><div><b>{u.full_name}</b><span>{u.email}</span></div><Badge tone={u.is_active?'safe':'warning'}>{u.is_active?'Active':'Inactive'}</Badge><select aria-label={`Role for ${u.full_name}`} value={u.role} onChange={e=>update(u.id,{role:e.target.value})}>{['administrator','senior_analyst','fraud_analyst','bi_analyst'].map(r=><option key={r}>{r}</option>)}</select><button className="secondary-btn" disabled={!u.is_active} onClick={()=>update(u.id,{is_active:false})}>Deactivate</button></div>)}</div></section>
      <section className="card security-card"><div className="security-icon"><Icon name="lock"/></div><h3>Access controls</h3><p>Backend authorization controls who can view this page and perform user changes. Password hashes are excluded from responses.</p><ul><li><Icon name="check"/>Role restrictions enforced by API</li><li><Icon name="check"/>Changes written to audit log</li></ul></section>
      <section className="card span-2"><CardHead title="Recent audit activity" subtitle="Persisted security and administration events"/>{logs.length?logs.map(a=><div className="audit" key={a.id}><div><Icon name="users"/><p><b>{a.user_name||'System'}</b> · {a.action}: {a.description}</p><time>{new Date(a.created_at).toLocaleString()}</time></div></div>):<p className="unavailable">No audit records.</p>}</section>
    </div>
  </>
}

function Auth({ mode, setMode, signIn }: { mode: 'signin'|'recover'; setMode: (m:'signin'|'recover')=>void; signIn:(email:string,password:string)=>Promise<void> }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const titles = { signin: ['Welcome back', 'Sign in to your secure workspace'], recover: ['Recover access', 'Password recovery is not configured. Contact your workspace administrator.'] }
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (mode === 'recover') return
    const values = new FormData(e.currentTarget)
    setLoading(true); setError('')
    try { await signIn(String(values.get('email') || ''), String(values.get('password') || '')) }
    catch (err) { setError(err instanceof Error ? err.message : 'Sign-in failed. Please try again.') }
    finally { setLoading(false) }
  }
  return <div className="auth">
    <aside className="auth-brand" aria-label="FraudShield overview"><Logo/><div className="auth-copy"><div className="signal-orbit"><div><Icon name="shield" size={38}/></div><i/><i/><i/></div><div className="eyebrow">Decision intelligence for financial trust</div><h1>See the signal.<br/>Support investigation.</h1><p>A calibrated XGBoost model estimates transaction risk from nine supported transaction features. Investigators determine final outcomes.</p><div className="auth-proof"><span><Icon name="brain"/><b>9</b><small>model input features</small></span><span><Icon name="alert"/><b>0.468</b><small>selected score threshold</small></span></div></div><span className="auth-foot">© 2025 FraudShield AI · Built for responsible decisions</span></aside>
    <main className="auth-form-wrap"><div className="auth-form"><div className="mobile-logo"><Logo/></div><div className="eyebrow">Secure workspace access</div><h2>{titles[mode][0]}</h2><p>{titles[mode][1]}</p>
      <form onSubmit={submit}>
        {mode==='signin' && <><label>Work email<input name="email" type="email" autoComplete="username" placeholder="you@company.com" required/></label>
        <label>Password<div className="password"><input name="password" type="password" autoComplete="current-password" placeholder="Your password" required/><Icon name="eye"/></div></label></>}
        {mode==='signin' && <div className="form-between"><label className="checkbox"><input type="checkbox" defaultChecked/>Keep me signed in</label><button type="button" className="link-btn" onClick={()=>setMode('recover')}>Forgot password?</button></div>}
        {error && <p className="api-message error" role="alert">{error}</p>}
        {mode==='signin' && <button className="primary-btn wide" type="submit" disabled={loading}>{loading?'Signing in…':'Sign in securely'}<Icon name="arrow"/></button>}
      </form>
      {mode==='signin' ? <p className="auth-switch">Need access? Contact your workspace administrator.</p> : <p className="auth-switch"><button onClick={()=>setMode('signin')}>Return to sign in</button></p>}
      <div className="secure-line"><Icon name="lock"/>Credentials are verified by the FraudShield backend.</div>
    </div></main>
  </div>
}

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [mobileNav, setMobileNav] = useState(false)
  const [drawer, setDrawer] = useState<string|null>(null)
  const [investigateTx, setInvestigateTx] = useState<string|null>(null)
  const [authed, setAuthed] = useState(false)
  const [authMode, setAuthMode] = useState<'signin'|'recover'>('signin')
  const [currentUser, setCurrentUser] = useState<LoginResponse['user'] | null>(null)
  const signIn = async (email: string, password: string) => {
    const session = await api.login(email, password)
    setAccessToken(session.access_token)
    setCurrentUser(session.user)
    setAuthed(true)
  }
  const signOut = async () => {
    try { await api.logout() } catch { /* Clear the in-memory credential even if logging out cannot reach the API. */ }
    setAccessToken(null); setCurrentUser(null); setAuthed(false); setAuthMode('signin'); setPage('dashboard'); setDrawer(null)
  }
  const go = (id:string) => { setPage(id); setMobileNav(false); window.scrollTo(0,0) }
  if (!authed) return <Auth mode={authMode} setMode={setAuthMode} signIn={signIn}/>
  const role = currentUser?.role || ''
  const visibleNav = nav.filter(n => (n.id!=='management'||role==='administrator') && (n.id!=='analytics'||['administrator','senior_analyst','bi_analyst'].includes(role)) && (n.id!=='investigations'||['administrator','senior_analyst','fraud_analyst'].includes(role)) && (n.id!=='detection'||['administrator','senior_analyst','fraud_analyst'].includes(role)))
  const active = visibleNav.find(n=>n.id===page)
  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav?'open':''}`} aria-label="Primary"><div className="side-top"><Logo/><button className="mobile-close icon-btn" onClick={()=>setMobileNav(false)} aria-label="Close navigation"><Icon name="close"/></button></div>
      <nav aria-label="Main navigation">{visibleNav.map(n=><button key={n.id} className={page===n.id?'active':''} onClick={()=>go(n.id)}><Icon name={n.icon as IconName}/><span>{n.label}</span></button>)}</nav>
      <div className="side-bottom"><button onClick={()=>go('management')}><Icon name="settings"/><span>Settings</span></button><div className="user-card"><span className="avatar">{currentUser?.full_name.split(/\s+/).map(part=>part[0]).slice(0,2).join('') || 'U'}</span><div><b>{currentUser?.full_name || 'User'}</b><span>{currentUser?.role.replace(/_/g,' ') || 'Authenticated user'}</span></div><button onClick={signOut} aria-label="Sign out"><Icon name="logout"/></button></div></div>
    </aside>
    {mobileNav&&<div className="nav-scrim" onClick={()=>setMobileNav(false)}/>}
    <div className="main-wrap"><header><div className="header-left"><button className="menu-btn" onClick={()=>setMobileNav(true)} aria-label="Open navigation"><Icon name="menu"/></button><span>{active?.label}</span><Icon name="chevron" size={13}/><b>FraudShield workspace</b></div><div className="header-right"><div className="global-search"><Icon name="search"/><span>Search anything</span><kbd>⌘ K</kbd></div><button className="icon-btn notification" aria-label="Notifications"><Icon name="bell"/><i/></button><div className="network"><i/>API status unknown</div></div></header>
      <main>{page==='dashboard'&&<Dashboard go={go}/>} {page==='transactions'&&<Transactions openDetail={setDrawer}/>} {page==='detection'&&<Detection/>} {page==='investigations'&&<Investigations initialTransactionId={investigateTx} role={role}/>} {page==='analytics'&&<Analytics/>} {page==='models'&&<Models/>} {page==='management'&&role==='administrator'&&<Management/>}</main>
    </div>
    {drawer&&<DetailDrawer id={drawer} close={()=>setDrawer(null)} investigate={()=>{setInvestigateTx(drawer);setDrawer(null);go('investigations')}}/>}
  </div>
}
