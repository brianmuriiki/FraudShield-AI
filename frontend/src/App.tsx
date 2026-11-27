import { FormEvent, ReactNode, useMemo, useState } from 'react'
import { api, PredictionRequest, PredictionResponse, TransactionType } from './api'

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

const transactions = [
  { id: 'TXN-8942031', party: 'Kofi Mensah', type: 'Cash out', amount: 'GH₵ 18,450.00', time: 'Today, 10:42', score: 94, status: 'Critical', initials: 'KM' },
  { id: 'TXN-8942018', party: 'Amina Diallo', type: 'Transfer', amount: '₦ 2,890,000', time: 'Today, 10:31', score: 87, status: 'Suspicious', initials: 'AD' },
  { id: 'TXN-8941997', party: 'Lagos Meridian Ltd', type: 'Payment', amount: '₦ 645,500', time: 'Today, 10:08', score: 72, status: 'Suspicious', initials: 'LM' },
  { id: 'TXN-8941984', party: 'Zuri Market', type: 'Cash in', amount: 'KES 74,200', time: 'Today, 09:56', score: 24, status: 'Low risk', initials: 'ZM' },
  { id: 'TXN-8941951', party: 'Thabo Nkosi', type: 'Payment', amount: 'ZAR 9,850', time: 'Today, 09:21', score: 8, status: 'Not flagged', initials: 'TN' },
  { id: 'TXN-8941926', party: 'Fatou Ndiaye', type: 'Transfer', amount: 'CFA 980,000', time: 'Today, 08:47', score: 65, status: 'Suspicious', initials: 'FN' },
]

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

function TrendChart({ analytics = false }: { analytics?: boolean }) {
  return <div className={`chart-wrap ${analytics ? 'tall' : ''}`}>
    <div className="chart-y"><span>1.2k</span><span>800</span><span>400</span><span>0</span></div>
    <svg viewBox="0 0 720 220" preserveAspectRatio="none" role="img" aria-label="Fraud trend line chart">
      <defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ff6b4a" stopOpacity=".26"/><stop offset="100%" stopColor="#ff6b4a" stopOpacity="0"/></linearGradient></defs>
      <g className="gridlines"><path d="M0 20H720M0 80H720M0 140H720M0 200H720"/></g>
      <path className="area" d="M0 170 C60 165 72 120 130 138 S215 115 260 126 S330 56 390 85 S472 104 520 58 S590 86 640 44 S690 52 720 26 V220H0Z"/>
      <path className="line" d="M0 170 C60 165 72 120 130 138 S215 115 260 126 S330 56 390 85 S472 104 520 58 S590 86 640 44 S690 52 720 26"/>
      <circle cx="640" cy="44" r="5"/><circle cx="640" cy="44" r="10" opacity=".18"/>
    </svg>
    <div className="chart-x"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div>
  </div>
}

function Donut() {
  return <div className="donut-area"><div className="donut"><div><strong>8.4%</strong><span>at risk</span></div></div><div className="legend">
    <div><i className="critical-bg"/><span>Critical</span><b>2.1%</b></div>
    <div><i className="warning-bg"/><span>Elevated</span><b>6.3%</b></div>
    <div><i className="safe-bg"/><span>Low risk</span><b>91.6%</b></div>
  </div></div>
}

function TransactionTable({ compact = false, onSelect, items = transactions }: { compact?: boolean; onSelect?: (id: string) => void; items?: typeof transactions }) {
  return <div className="table-scroll"><table>
    <thead><tr><th>Transaction / customer</th><th>Type</th><th>Amount</th><th>Timestamp</th><th>Sample score</th><th>Model prediction</th><th /></tr></thead>
    <tbody>{items.slice(0, compact ? 4 : 6).map(t => <tr key={t.id} onClick={() => onSelect?.(t.id)} className={onSelect ? 'clickable' : ''}>
      <td><div className="customer"><span className="avatar sm">{t.initials}</span><span><b>{t.id}</b><small>{t.party}</small></span></div></td>
      <td>{t.type}</td><td className="amount">{t.amount}</td><td>{t.time}</td>
      <td><div className={`score ${riskClass(t.score)}`}><b>{t.score}</b><span><i style={{ width: `${t.score}%` }}/></span></div></td>
      <td><Badge tone={riskClass(t.score)}>{t.status}</Badge></td><td><button className="icon-btn" aria-label="More actions"><Icon name="more"/></button></td>
    </tr>)}</tbody>
  </table></div>
}

function Dashboard({ go }: { go: (id: string) => void }) {
  return <>
    <PageTitle eyebrow="Risk command" title="Good morning, Nia." subtitle="Operational metrics will appear here when connected to the FraudShield backend." action={<Badge>Backend data unavailable</Badge>}/>
    <div className="demo-banner"><Icon name="alert"/><span><b>Demonstration data</b> — Figures and transaction records below are illustrative and are not live operational statistics.</span></div>
    <div className="metrics">
      <Metric icon="pulse" label="Transactions analysed" value="248,921" note="+12.4% vs last week" tone="blue"/>
      <Metric icon="alert" label="Suspicious (sample)" value="1,284" note="Illustrative model flags" tone="orange"/>
      <Metric icon="shield" label="Confirmed fraud cases" value="Unavailable" note="Requires investigator outcome data" tone="red"/>
      <Metric icon="wallet" label="Value monitored" value="Unavailable" note="Connect backend for totals" tone="green"/>
    </div>
    <div className="dashboard-grid">
      <section className="card span-2"><CardHead title="Fraud signal trend" subtitle="Detected suspicious transactions, last 7 days" right={<select aria-label="Chart period"><option>Last 7 days</option><option>Last 30 days</option></select>}/><TrendChart/></section>
      <section className="card"><CardHead title="Risk distribution" subtitle="Current transaction mix"/><Donut/></section>
      <section className="card span-2"><CardHead title="Priority signal queue" subtitle="Ranked by model risk and potential exposure" right={<button className="text-btn" onClick={() => go('transactions')}>View all <Icon name="arrow" size={15}/></button>}/><TransactionTable compact onSelect={() => go('investigations')}/></section>
      <section className="card intelligence"><div className="ai-icon"><Icon name="brain" size={24}/></div><div className="eyebrow">Model scope</div><h3>Nine transaction features</h3><p>The trained model evaluates transaction step, amount, sender and recipient balances, and transaction type.</p><div className="intel-stat"><span>Decision threshold</span><b>0.468 risk score</b></div><button className="dark-btn" onClick={() => go('models')}>View model details <Icon name="arrow" size={16}/></button></section>
    </div>
  </>
}

function Metric({ icon, label, value, note, tone }: { icon: IconName; label: string; value: string; note: string; tone: string }) {
  return <div className="metric card"><div className={`metric-icon ${tone}`}><Icon name={icon}/></div><span>{label}</span><strong>{value}</strong><small className={tone === 'red' || tone === 'orange' ? 'hot' : ''}><Icon name="trend" size={13}/>{note}</small></div>
}

function CardHead({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return <div className="card-head"><div><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</div>{right}</div>
}

function Transactions({ openDetail }: { openDetail: (id: string) => void }) {
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('All types')
  const [statusFilter, setStatusFilter] = useState('All predictions')
  const [minimumScore, setMinimumScore] = useState('')
  const filtered = useMemo(() => transactions.filter(t => {
    const matchQuery = `${t.id} ${t.party}`.toLowerCase().includes(query.toLowerCase())
    const matchType = typeFilter === 'All types' || t.type === typeFilter
    const matchStatus = statusFilter === 'All predictions' || (statusFilter === 'Suspicious' ? t.score >= 46.8 : t.score < 46.8)
    const matchScore = minimumScore === '' || t.score >= Number(minimumScore)
    return matchQuery && matchType && matchStatus && matchScore
  }), [query, typeFilter, statusFilter, minimumScore])
  const count = filtered.length
  return <>
    <PageTitle eyebrow="Transaction monitoring" title="Transaction stream" subtitle="Demonstration records only. Connect the backend to search and review operational transactions." action={<Badge>Sample records</Badge>}/>
    <div className="filter-bar card"><div className="search-field"><Icon name="search"/><input aria-label="Search transaction reference" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search reference or customer (sample)"/></div><select aria-label="Filter by transaction type" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}><option>All types</option>{Array.from(new Set(transactions.map(t=>t.type))).map(t=><option key={t}>{t}</option>)}</select><select aria-label="Filter by prediction status" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}><option>All predictions</option><option>Suspicious</option><option>Not flagged</option></select><label className="score-filter">Minimum score<input aria-label="Minimum risk score" type="number" min="0" max="100" value={minimumScore} onChange={e=>setMinimumScore(e.target.value)}/></label></div>
    <section className="card table-card"><div className="table-summary"><div><b>{count} sample transactions</b><span>Demonstration records · not a live feed</span></div></div>{filtered.length ? <TransactionTable items={filtered} onSelect={openDetail}/> : <p className="unavailable">No sample transactions match these filters.</p>}<div className="pagination"><span>Showing {filtered.length} of {transactions.length} sample records</span></div></section>
  </>
}

function DetailDrawer({ id, close, investigate }: { id: string; close: () => void; investigate: () => void }) {
  const t = transactions.find(x => x.id === id) || transactions[0]
  return <div className="drawer-layer" onMouseDown={e => e.target === e.currentTarget && close()}><aside className="drawer">
    <div className="drawer-head"><div><div className="eyebrow">Transaction detail</div><h2>{t.id}</h2></div><button className="icon-btn" onClick={close} aria-label="Close"><Icon name="close"/></button></div>
    <div className="demo-banner"><Icon name="alert"/><span>Illustrative sample record. Risk figures and customer details are not live backend data.</span></div>
    <div className={`risk-hero ${riskClass(t.score)}`}><div className="risk-ring"><strong>{t.score}</strong><span>/ 100</span></div><div><Badge tone={riskClass(t.score)}>Sample model flag</Badge><h3>Suspicious · sample only</h3><p>Score represents an illustrative record, not a confirmed fraud outcome.</p></div></div>
    <div className="detail-section"><h3>Transaction information</h3><div className="detail-grid"><Detail label="Reference" value={t.id}/><Detail label="Amount" value={t.amount}/><Detail label="Type" value={t.type}/><Detail label="Timestamp" value={t.time}/></div></div>
    <div className="detail-section"><h3>Investigation outcome</h3><p className="unavailable">No investigation record is linked. Model prediction, investigation status and final outcome are separate fields.</p></div>
    <div className="drawer-actions"><button className="secondary-btn" onClick={close}>Mark as reviewed</button><button className="primary-btn" onClick={investigate}>Open investigation <Icon name="arrow"/></button></div>
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
      if (!Number.isFinite(prediction.risk_score) || prediction.risk_score < 0 || prediction.risk_score > 1) throw new Error('The API returned an invalid risk score. No prediction is displayed.')
      setResult(prediction)
      setNotice('Prediction received from the backend.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed. Please try again.')
      setSubmitted(null)
    } finally { setLoading(false) }
  }
  const score = result?.risk_score ?? 0
  const suspicious = score >= (result?.threshold ?? 0.468)
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
        <div className="confidence"><span><b>Fraud-risk score · threshold 0.468</b><b>{score.toFixed(4)}</b></span><i><em style={{ width: `${score * 100}%` }}/></i></div>
        <div className="detail-grid"><Detail label="Amount" value={submitted ? submitted.amount.toLocaleString() : '—'}/><Detail label="Type" value={submitted ? typeLabels[submitted.type] : '—'}/><Detail label="Time step" value={String(submitted?.step ?? '—')}/><Detail label="Sender balance" value={String(submitted?.oldbalanceOrg ?? '—')}/><Detail label="Recipient balance" value={String(submitted?.oldbalanceDest ?? '—')}/></div>
        <div className="explanation"><h3>Model explanation</h3><p>SHAP contributions explain how model inputs influenced this score; they do not prove fraud.</p>{result.explanation?.length ? result.explanation.map(item => <div className="shap-row" key={item.feature}><b>{item.feature}</b><span>Value: {item.value}</span><strong className={item.contribution >= 0 ? 'positive' : 'negative'}>{item.contribution >= 0 ? '+' : ''}{item.contribution.toFixed(4)} · {item.contribution >= 0 ? 'increased' : 'decreased'} score</strong>{item.relative_influence !== undefined && <small>{(item.relative_influence * 100).toFixed(1)}% relative influence</small>}</div>) : <span>SHAP explanation is not available in the prediction response.</span>}</div>
        <div className="recommendation"><Icon name="alert"/><div><b>Investigation status</b><p>{suspicious ? 'Review the transaction with an authorized investigator. This result is not a confirmed fraud outcome.' : 'This transaction was not flagged by the model.'}</p></div></div>
      </>}</section>
    </div>
  </>
}

function Investigations() {
  return <>
    <PageTitle eyebrow="Case workspace" title="Investigation workspace" subtitle="Investigation records will load here when the backend is connected." action={<Badge>Backend data unavailable</Badge>}/>
    <div className="demo-banner"><Icon name="alert"/><span><b>No investigation selected</b> — Assignments, notes, history and outcomes must be persisted by the backend before they can be edited here.</span></div>
    <div className="case-layout">
      <div className="case-main">
        <section className="card"><div className="empty-result"><div><Icon name="case" size={34}/></div><h3>No investigation selected</h3><p>Open an investigation from a backend transaction record to review its model prediction separately from investigation status and outcome.</p></div></section>
        <section className="card"><CardHead title="Activity timeline" subtitle="Events and analyst actions in chronological order"/>
          <p className="unavailable">Investigation history is unavailable until backend records are connected.</p>
        </section>
      </div>
      <aside className="case-side"><section className="card"><CardHead title="Investigation notes" subtitle="Internal · visible to assigned team"/><p className="unavailable">Select a persisted investigation to view or save notes.</p></section>
        <section className="card"><CardHead title="Case ownership"/><div className="assignee"><span className="avatar">NA</span><div><b>Nia Adebayo</b><span>Senior fraud analyst</span></div><Icon name="chevron"/></div><div className="case-meta"><Detail label="Priority" value="P1 · Critical"/><Detail label="SLA remaining" value="01h 42m"/><Detail label="Queue" value="Account takeover"/><Detail label="Last updated" value="2 min ago"/></div></section>
        <button className="danger-outline" disabled title="Select an investigation before recording an outcome"><Icon name="shield"/>Record confirmed fraud outcome</button>
      </aside>
    </div>
  </>
}

function Timeline({ time, icon, title, text, tone }: { time: string; icon: IconName; title: string; text: string; tone: string }) {
  return <div className="timeline-item"><time>{time}</time><div className={`timeline-icon ${tone}`}><Icon name={icon}/></div><div><b>{title}</b><p>{text}</p></div></div>
}

function Analytics() {
  return <>
    <PageTitle eyebrow="Analytics & reporting" title="Risk intelligence" subtitle="Operational analytics will be populated from backend transaction and investigation records." action={<Badge>Data unavailable</Badge>}/>
    <div className="demo-banner"><Icon name="alert"/><span><b>Analytics not connected</b> — No live trend, volume, fraud outcome, false positive, false negative, or amount-distribution data is currently available.</span></div>
    <div className="analytics-grid"><section className="card span-2"><CardHead title="Transaction and suspicious volume over time" subtitle="Awaiting backend-generated time series"/><p className="unavailable">No operational data available.</p></section><section className="card"><CardHead title="Transaction distribution by type" subtitle="Awaiting backend data"/><p className="unavailable">No operational data available.</p></section><section className="card"><CardHead title="Investigation outcomes" subtitle="Awaiting investigator records"/><p className="unavailable">No operational data available.</p></section><section className="card span-2"><CardHead title="Detection quality" subtitle="Precision, recall, false positives and false negatives from labeled outcomes"/><p className="unavailable">Operational metrics are unavailable until predictions are linked to investigation outcomes.</p></section></div>
  </>
}
function Bar({ label, value, count }: { label: string; value: number; count: string }) { return <div className="bar-row"><span>{label}</span><div><i style={{width:`${value}%`}}/></div><b>{count}</b></div> }
function Region({ name, count, value }: { name: string; count: string; value: number }) { return <div className="region"><div><b>{name}</b><span>{count}</span></div><strong>{value}</strong><div className="region-bar"><i style={{width:`${value}%`}}/></div></div> }

function Models() {
  return <>
    <PageTitle eyebrow="Machine learning operations" title="Model intelligence" subtitle="Historical offline evaluation of the trained and calibrated XGBoost model." action={<Badge>Offline results</Badge>}/>
    <div className="demo-banner"><Icon name="alert"/><span><b>Monitoring warning</b> — Calibration drift was observed between validation and test periods. Risk scores require ongoing monitoring and recalibration assessment.</span></div>
    <section className="card model-head"><div className="model-identity"><div className="ai-icon"><Icon name="brain" size={26}/></div><div><span>Trained model</span><h2>Calibrated XGBoost</h2><p>Sigmoid calibration · PaySim Synthetic Mobile Money Dataset</p></div></div><div className="model-status"><Badge tone="neutral">Offline evaluation</Badge></div></section>
    <div className="model-grid"><section className="card span-2"><CardHead title="Historical chronological offline test results" subtitle="Not live production performance"/><div className="model-metrics"><ModelMetric label="Precision" value="96.76%" change="offline"/><ModelMetric label="Recall" value="68.65%" change="offline"/><ModelMetric label="F1-score" value="80.32%" change="offline"/><ModelMetric label="ROC-AUC" value="99.93%" change="offline"/><ModelMetric label="PR-AUC" value="90.87%" change="offline"/><ModelMetric label="Brier score" value="0.001875" change="offline"/></div></section>
      <section className="card"><CardHead title="Model configuration"/><div className="case-meta"><Detail label="Input features" value="9"/><Detail label="Decision threshold" value="0.468"/><Detail label="Flagged at or above" value="0.468"/><Detail label="Score meaning" value="Model risk estimate"/></div></section>
    </div>
  </>
}
function ModelMetric({label,value,change}:{label:string;value:string;change:string}) { return <div><span>{label}</span><strong>{value}</strong><small>{change === 'offline' ? 'Historical offline test' : change}</small></div> }
function Version({version,date,f1,auc,status}:{version:string;date:string;f1:string;auc:string;status:string}) { return <div className="version-row"><b>{version}</b><span>{date}</span><span>F1 <b>{f1}</b></span><span>ROC-AUC <b>{auc}</b></span><Badge tone={status==='Production'?'safe':'neutral'}>{status}</Badge><Icon name="chevron"/></div> }

function Management() {
  return <>
    <PageTitle eyebrow="Administration" title="Team & system" subtitle="Manage access, roles, auditability and organization configuration." action={<button className="primary-btn"><Icon name="plus"/>Invite team member</button>}/>
    <div className="admin-tabs"><button className="active">Team members</button><button>Roles & permissions</button><button>Audit log</button><button>Configuration</button></div>
    <div className="admin-grid"><section className="card span-2"><CardHead title="Team members" subtitle="8 active users · 2 invitations pending" right={<div className="search-mini"><Icon name="search"/><span>Search people</span></div>}/><div className="people"><Person initials="NA" name="Nia Adebayo" email="nia@meridianpay.com" role="Senior fraud analyst" status="Active"/><Person initials="KO" name="Kwame Osei" email="kwame@meridianpay.com" role="Risk administrator" status="Active"/><Person initials="AM" name="Amara Mbeki" email="amara@meridianpay.com" role="Fraud analyst" status="Active"/><Person initials="JK" name="Jelani Kimani" email="jelani@meridianpay.com" role="BI viewer" status="Invited"/></div></section>
      <section className="card security-card"><div className="security-icon"><Icon name="lock"/></div><h3>Security posture</h3><div className="security-score"><strong>92</strong><span>/100</span></div><p>Your workspace has strong access controls.</p><ul><li><Icon name="check"/>MFA enforced</li><li><Icon name="check"/>SSO configured</li><li><Icon name="alert"/>2 API keys expire soon</li></ul><button className="secondary-btn wide">Review security</button></section>
      <section className="card span-2"><CardHead title="Recent audit activity" subtitle="Immutable record of sensitive actions"/><div className="audit"><div><Icon name="users"/><p><b>Kwame Osei</b> changed Amara Mbeki’s role to Fraud analyst</p><time>Today, 09:18</time></div><div><Icon name="settings"/><p><b>System</b> promoted model v3.4.1 to production</p><time>05 Jun, 14:32</time></div><div><Icon name="download"/><p><b>Nia Adebayo</b> exported 286 transaction records</p><time>04 Jun, 16:05</time></div></div></section>
    </div>
  </>
}
function Person({initials,name,email,role,status}:{initials:string;name:string;email:string;role:string;status:string}) { return <div className="person"><span className="avatar">{initials}</span><div><b>{name}</b><span>{email}</span></div><Badge tone={status==='Active'?'safe':'warning'}>{status}</Badge><select defaultValue={role}><option>{role}</option><option>Senior fraud analyst</option><option>Risk administrator</option><option>BI viewer</option></select><button className="icon-btn"><Icon name="more"/></button></div> }

function Auth({ mode, setMode, signIn }: { mode: 'signin'|'register'|'recover'; setMode: (m:'signin'|'register'|'recover')=>void; signIn:()=>void }) {
  const titles = { signin: ['Welcome back', 'Sign in to your secure workspace'], register: ['Create your workspace', 'Start protecting every transaction'], recover: ['Recover access', 'We’ll send a secure reset link'] }
  return <div className="auth">
    <section className="auth-brand"><Logo/><div className="auth-copy"><div className="signal-orbit"><div><Icon name="shield" size={38}/></div><i/><i/><i/></div><div className="eyebrow">Decision intelligence for financial trust</div><h1>See the signal.<br/>Support investigation.</h1><p>A calibrated XGBoost model estimates transaction risk from nine supported transaction features. Investigators determine final outcomes.</p><div className="auth-proof"><span><Icon name="brain"/><b>9</b><small>model input features</small></span><span><Icon name="alert"/><b>0.468</b><small>selected score threshold</small></span></div></div><span className="auth-foot">© 2025 FraudShield AI · Built for responsible decisions</span></section>
    <section className="auth-form-wrap"><div className="auth-form"><div className="mobile-logo"><Logo/></div><div className="eyebrow">Secure workspace access</div><h2>{titles[mode][0]}</h2><p>{titles[mode][1]}</p>
      <form onSubmit={e => {e.preventDefault(); mode==='recover' ? setMode('signin') : signIn()}}>
        {mode==='register' && <label>Full name<input placeholder="Your full name" required/></label>}
        <label>Work email<input type="email" defaultValue={mode==='signin'?'nia@meridianpay.com':''} placeholder="you@company.com" required/></label>
        {mode!=='recover' && <label>Password<div className="password"><input type="password" defaultValue={mode==='signin'?'fraudshield':''} placeholder="At least 8 characters" required/><Icon name="eye"/></div></label>}
        {mode==='signin' && <div className="form-between"><label className="checkbox"><input type="checkbox" defaultChecked/>Keep me signed in</label><button type="button" className="link-btn" onClick={()=>setMode('recover')}>Forgot password?</button></div>}
        {mode==='register' && <label className="checkbox consent"><input type="checkbox" required/>I agree to the Terms of Service and Privacy Policy</label>}
        <button className="primary-btn wide" type="submit">{mode==='signin'?'Sign in securely':mode==='register'?'Create account':'Send recovery link'}<Icon name="arrow"/></button>
      </form>
      <div className="auth-divider"><span>or continue with</span></div><button className="sso-btn"><span className="google">G</span>Google Workspace</button>
      <p className="auth-switch">{mode==='signin' ? <>New to FraudShield? <button onClick={()=>setMode('register')}>Create an account</button></> : <>Already have access? <button onClick={()=>setMode('signin')}>Sign in</button></>}</p>
      <div className="secure-line"><Icon name="lock"/>256-bit encryption · SOC 2 controls · MFA ready</div>
    </div></section>
  </div>
}

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [mobileNav, setMobileNav] = useState(false)
  const [drawer, setDrawer] = useState<string|null>(null)
  const [authed, setAuthed] = useState(true)
  const [authMode, setAuthMode] = useState<'signin'|'register'|'recover'>('signin')
  const go = (id:string) => { setPage(id); setMobileNav(false); window.scrollTo(0,0) }
  if (!authed) return <Auth mode={authMode} setMode={setAuthMode} signIn={()=>setAuthed(true)}/>
  const active = nav.find(n=>n.id===page)
  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav?'open':''}`}><div className="side-top"><Logo/><button className="mobile-close icon-btn" onClick={()=>setMobileNav(false)}><Icon name="close"/></button></div>
      <nav aria-label="Main navigation">{nav.map(n=><button key={n.id} className={page===n.id?'active':''} onClick={()=>go(n.id)}><Icon name={n.icon as IconName}/><span>{n.label}</span>{n.id==='investigations'&&<em>7</em>}</button>)}</nav>
      <div className="side-bottom"><button onClick={()=>go('management')}><Icon name="settings"/><span>Settings</span></button><div className="user-card"><span className="avatar">NA</span><div><b>Nia Adebayo</b><span>Senior fraud analyst</span></div><button onClick={()=>setAuthed(false)} aria-label="Sign out"><Icon name="logout"/></button></div></div>
    </aside>
    {mobileNav&&<div className="nav-scrim" onClick={()=>setMobileNav(false)}/>}
    <div className="main-wrap"><header><div className="header-left"><button className="menu-btn" onClick={()=>setMobileNav(true)}><Icon name="menu"/></button><span>{active?.label}</span><Icon name="chevron" size={13}/><b>Meridian Pay</b></div><div className="header-right"><div className="global-search"><Icon name="search"/><span>Search anything</span><kbd>⌘ K</kbd></div><button className="icon-btn notification"><Icon name="bell"/><i/></button><div className="network"><i/>All systems operational</div></div></header>
      <main>{page==='dashboard'&&<Dashboard go={go}/>} {page==='transactions'&&<Transactions openDetail={setDrawer}/>} {page==='detection'&&<Detection/>} {page==='investigations'&&<Investigations/>} {page==='analytics'&&<Analytics/>} {page==='models'&&<Models/>} {page==='management'&&<Management/>}</main>
    </div>
    {drawer&&<DetailDrawer id={drawer} close={()=>setDrawer(null)} investigate={()=>{setDrawer(null);go('investigations')}}/>}
  </div>
}
