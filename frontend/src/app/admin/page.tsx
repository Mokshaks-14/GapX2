'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity, AlertTriangle, BarChart3, CheckCircle2, Download, Eye, FileText, Loader2, Lock, LogOut,
  Mail, RefreshCw, Search, Server, ShieldAlert, ShieldCheck, UserX, Users, X, XCircle, Code2, Plus, Pencil, Trash2, MessageSquare,
} from 'lucide-react';
import GapXLogo from '../GapXLogo';

const API = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000') + '/api/v1';
const TOKEN_KEY = 'gapx_admin_token';   // sessionStorage: closes with the tab, separate from the student app

type Tab = 'overview' | 'integrity' | 'logs' | 'users' | 'problems' | 'questions' | 'system';

const EVENT_LABELS: Record<string, string> = {
  multiple_faces: 'Multiple faces', phone_detected: 'Phone detected', background_motion: 'Background motion',
  face_missing: 'Face missing', tab_switch: 'Switched tab/app', fullscreen_exit: 'Left full screen', paste_attempt: 'Paste attempt',
};

const SEV_STYLE: Record<string, string> = {
  info: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  critical: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
};

const fmt = (t?: string | null) => {
  if (!t) return '—';
  const d = new Date(t.endsWith('Z') || t.includes('+') ? t : t + 'Z');
  return d.toLocaleString(undefined, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

export default function AdminPanel() {
  const [token, setToken] = useState<string | null>(null);
  const [admin, setAdmin] = useState<{ email: string; name: string } | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let saved: string | null = null;
    try { saved = sessionStorage.getItem(TOKEN_KEY); } catch {}
    if (!saved) { setReady(true); return; }
    fetch(`${API}/admin/me`, { headers: { Authorization: `Bearer ${saved}` } })
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(me => { setToken(saved); setAdmin(me); })
      .catch(() => { try { sessionStorage.removeItem(TOKEN_KEY); } catch {} })
      .finally(() => setReady(true));
  }, []);

  const logout = () => {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch {}
    setToken(null); setAdmin(null);
  };

  if (!ready) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-zinc-500" /></div>;
  if (!token || !admin) return <AdminLogin onLogin={(t, me) => { try { sessionStorage.setItem(TOKEN_KEY, t); } catch {} setToken(t); setAdmin(me); }} />;
  return <Console token={token} admin={admin} onLogout={logout} />;
}

// ───────────────────────── login ─────────────────────────
function AdminLogin({ onLogin }: { onLogin: (token: string, me: { email: string; name: string }) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setBusy(true);
    try {
      const r = await fetch(`${API}/admin/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.detail || 'Sign-in failed');
      onLogin(data.access_token, { email: data.email, name: data.name });
    } catch (err: any) {
      setError(err.message === 'Failed to fetch' ? 'Cannot reach the backend. Is it running?' : err.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 opacity-[0.07]" style={{ backgroundImage: 'linear-gradient(#a1a1aa 1px, transparent 1px), linear-gradient(90deg, #a1a1aa 1px, transparent 1px)', backgroundSize: '44px 44px' }} />
      <div className="absolute w-[500px] h-[500px] rounded-full bg-rose-600/10 blur-3xl -top-40 -right-40" />
      <form onSubmit={submit} className="relative w-full max-w-sm bg-zinc-900/90 border border-zinc-800 rounded-2xl p-7 shadow-2xl backdrop-blur">
        <div className="flex items-center gap-3 mb-6">
          <GapXLogo size={36} />
          <div>
            <div className="font-bold text-lg leading-tight">GapX Admin</div>
            <div className="text-xs text-zinc-500">Restricted area — administrators only</div>
          </div>
        </div>
        <label className="block text-xs font-medium text-zinc-400 mb-1.5">Admin email</label>
        <div className="relative mb-4">
          <Mail className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input type="email" required autoComplete="username" value={email} onChange={e => setEmail(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-3 py-2.5 text-sm outline-none focus:border-rose-500/60" placeholder="admin@gapx.ai" />
        </div>
        <label className="block text-xs font-medium text-zinc-400 mb-1.5">Password</label>
        <div className="relative mb-5">
          <Lock className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input type="password" required autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-3 py-2.5 text-sm outline-none focus:border-rose-500/60" placeholder="••••••••••" />
        </div>
        {error && <div className="mb-4 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{error}</div>}
        <button disabled={busy} className="w-full bg-rose-600 hover:bg-rose-500 disabled:opacity-60 text-white font-semibold rounded-lg py-2.5 text-sm flex items-center justify-center gap-2">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Sign in to console
        </button>
        <p className="mt-5 text-[11px] text-zinc-500 leading-relaxed">
          Every sign-in attempt is recorded with its IP address. After 5 failed attempts the IP is locked out for 15 minutes.
          Student accounts cannot sign in here.
        </p>
      </form>
    </div>
  );
}

// ───────────────────────── console ─────────────────────────
function Console({ token, admin, onLogout }: { token: string; admin: { email: string; name: string }; onLogout: () => void }) {
  const [tab, setTab] = useState<Tab>('overview');

  const api = useCallback(async (path: string, init?: RequestInit) => {
    const r = await fetch(`${API}${path}`, { ...init, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...(init?.headers || {}) } });
    if (r.status === 401) { onLogout(); throw new Error('Session expired'); }
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || `Request failed (${r.status})`);
    return data;
  }, [token, onLogout]);

  const tabs: [Tab, string, React.ElementType][] = [
    ['overview', 'Overview', BarChart3], ['integrity', 'Integrity reviews', ShieldAlert], ['logs', 'Audit logs', FileText],
    ['users', 'Users', Users], ['problems', 'Coding problems', Code2], ['questions', 'Interview questions', MessageSquare], ['system', 'System', Server],
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex">
      <aside className="w-60 shrink-0 border-r border-zinc-800 bg-zinc-900/60 flex flex-col h-screen sticky top-0">
        <div className="flex items-center gap-2.5 px-5 h-16 border-b border-zinc-800">
          <GapXLogo size={28} />
          <div><div className="font-bold leading-tight">GapX</div><div className="text-[10px] uppercase tracking-widest text-rose-400 font-semibold">Admin console</div></div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {tabs.map(([id, label, Icon]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${tab === id ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20' : 'text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200 border border-transparent'}`}>
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-zinc-800">
          <div className="px-2 pb-2 text-xs text-zinc-500 truncate">{admin.email}</div>
          <button onClick={onLogout} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200">
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 min-w-0 p-6 lg:p-8">
        {tab === 'overview' && <Overview api={api} go={setTab} />}
        {tab === 'integrity' && <Integrity api={api} />}
        {tab === 'logs' && <Logs api={api} token={token} />}
        {tab === 'users' && <UsersTab api={api} />}
        {tab === 'problems' && <Problems api={api} />}
        {tab === 'questions' && <InterviewQuestions api={api} />}
        {tab === 'system' && <SystemTab api={api} />}
      </main>
    </div>
  );
}

type Api = (path: string, init?: RequestInit) => Promise<any>;

function useLoad<T>(fn: () => Promise<T>, deps: any[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const load = useCallback(() => {
    setLoading(true); setError('');
    fn().then(setData).catch(e => setError(e.message)).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { load(); }, [load]);
  return { data, error, loading, reload: load };
}

function Header({ title, sub, onRefresh, children }: { title: string; sub: string; onRefresh?: () => void; children?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-6">
      <div><h1 className="text-2xl font-bold">{title}</h1><p className="text-sm text-zinc-500 mt-1">{sub}</p></div>
      <div className="flex items-center gap-2">
        {children}
        {onRefresh && <button onClick={onRefresh} className="p-2 rounded-lg border border-zinc-800 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800" title="Refresh"><RefreshCw className="w-4 h-4" /></button>}
      </div>
    </div>
  );
}

const Card = ({ children, className = '' }: { children: React.ReactNode; className?: string }) =>
  <div className={`bg-zinc-900/60 border border-zinc-800 rounded-xl ${className}`}>{children}</div>;

const Status = ({ loading, error }: { loading: boolean; error: string }) =>
  loading ? <div className="py-16 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-zinc-500" /></div>
    : error ? <div className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-4 py-3">{error}</div> : null;

// ───────────────────────── overview ─────────────────────────
function Overview({ api, go }: { api: Api; go: (t: Tab) => void }) {
  const { data, error, loading, reload } = useLoad<any>(() => api('/admin/overview'), [api]);
  if (!data) return <><Header title="Overview" sub="Platform health at a glance" /><Status loading={loading} error={error} /></>;
  const max = Math.max(1, ...data.signups_last_7_days.map((d: any) => d.count));
  const stats: [string, any, string, Tab?][] = [
    ['Total users', data.users, `${data.new_this_week} new this week`, 'users'],
    ['Active today', data.active_today, `${data.disabled_users} disabled`, 'users'],
    ['Interviews', data.interviews, `${data.interviews_completed} completed · avg ${data.avg_interview_score}`],
    ['Flagged interviews', data.flagged_interviews, 'need integrity review', 'integrity'],
    ['Code submissions', data.submissions, `${data.acceptance_rate}% accepted`, 'problems'],
    ['Problems', data.problems, `${data.resumes} resumes built`, 'problems'],
    ['Warnings (24 h)', data.warnings_24h, 'warning + critical events', 'logs'],
    ['Failed logins (24 h)', data.failed_logins_24h, 'possible brute force', 'logs'],
  ];
  return (
    <>
      <Header title="Overview" sub="Platform health at a glance" onRefresh={reload} />
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        {stats.map(([label, value, sub, target]) => {
          const alert = (label.startsWith('Flagged') || label.startsWith('Failed')) && value > 0;
          return (
            <button key={label} onClick={() => target && go(target)} className={`text-left p-4 rounded-xl border transition ${alert ? 'bg-rose-500/5 border-rose-500/30 hover:border-rose-500/50' : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700'}`}>
              <div className="text-xs text-zinc-500">{label}</div>
              <div className={`text-3xl font-bold mt-1 ${alert ? 'text-rose-400' : ''}`}>{value}</div>
              <div className="text-xs text-zinc-500 mt-1">{sub}</div>
            </button>
          );
        })}
      </div>
      <Card className="p-5">
        <div className="text-sm font-semibold mb-4">Sign-ups, last 7 days</div>
        <div className="flex items-end gap-3 h-40">
          {data.signups_last_7_days.map((d: any) => (
            <div key={d.date} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
              <div className="text-xs text-zinc-400">{d.count}</div>
              <div className="w-full max-w-[48px] rounded-t-md bg-rose-500/70" style={{ height: `${Math.max(3, (d.count / max) * 100)}%` }} />
              <div className="text-[11px] text-zinc-500">{d.date}</div>
            </div>
          ))}
        </div>
      </Card>
    </>
  );
}

// ───────────────────────── integrity ─────────────────────────
function Integrity({ api }: { api: Api }) {
  const [onlyFlagged, setOnlyFlagged] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const { data, error, loading, reload } = useLoad<any[]>(() => api(`/admin/integrity?only_flagged=${onlyFlagged}`), [api, onlyFlagged]);
  return (
    <>
      <Header title="Integrity reviews" sub="Interviews where proctoring raised warnings (phones, extra people, tab switches…)" onRefresh={reload}>
        <label className="flex items-center gap-2 text-sm text-zinc-400 cursor-pointer select-none">
          <input type="checkbox" checked={onlyFlagged} onChange={e => setOnlyFlagged(e.target.checked)} className="accent-rose-500" /> Flagged only
        </label>
      </Header>
      <Status loading={loading} error={error} />
      {data && !data.length && <Card className="p-10 text-center text-sm text-zinc-500">No interviews with integrity events yet.</Card>}
      <div className="space-y-3">
        {data?.map(r => (
          <Card key={r.interview_id} className={`p-4 ${r.flagged ? 'border-rose-500/30' : ''}`}>
            <div className="flex flex-wrap items-center gap-3">
              {r.flagged ? <ShieldAlert className="w-5 h-5 text-rose-400" /> : <ShieldCheck className="w-5 h-5 text-emerald-400" />}
              <div className="min-w-0 flex-1">
                <div className="font-medium">{r.name || r.user} <span className="text-zinc-500 font-normal text-sm">· {r.user}</span></div>
                <div className="text-xs text-zinc-500">#{r.interview_id} · {r.role} · score {r.score || '—'} · {fmt(r.created_at)}</div>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(r.counts || {}).filter(([, n]) => (n as number) > 0).map(([k, n]) => (
                  <span key={k} className={`text-[11px] px-2 py-0.5 rounded-full border ${['phone_detected', 'multiple_faces'].includes(k) ? SEV_STYLE.critical : SEV_STYLE.warning}`}>{EVENT_LABELS[k] || k} ×{n as number}</span>
                ))}
              </div>
              <button onClick={() => setOpen(r.interview_id)} className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-zinc-700 hover:bg-zinc-800"><Eye className="w-4 h-4" /> Review</button>
            </div>
            {r.summary && <div className="text-xs text-zinc-400 mt-3 pl-8">{r.summary}</div>}
          </Card>
        ))}
      </div>
      {open !== null && <InterviewDrawer api={api} id={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function InterviewDrawer({ api, id, onClose }: { api: Api; id: number; onClose: () => void }) {
  const { data, error, loading } = useLoad<any>(() => api(`/admin/interviews/${id}`), [api, id]);
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={onClose}>
      <div className="w-full max-w-2xl h-full overflow-y-auto bg-zinc-950 border-l border-zinc-800 p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold">Interview #{id}</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-800"><X className="w-5 h-5" /></button>
        </div>
        <Status loading={loading} error={error} />
        {data && (
          <div className="space-y-5">
            <div className="text-sm text-zinc-400">{data.role} · {data.type} · score <b className="text-zinc-100">{data.score || '—'}</b> · {fmt(data.created_at)}</div>
            {data.integrity?.summary && <div className={`text-sm rounded-lg px-4 py-3 border ${data.integrity.flagged ? SEV_STYLE.critical : SEV_STYLE.info}`}>{data.integrity.summary}</div>}
            <div>
              <div className="text-sm font-semibold mb-2">Timeline of warnings</div>
              {data.integrity_events.length ? (
                <div className="border border-zinc-800 rounded-lg divide-y divide-zinc-800">
                  {data.integrity_events.map((e: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 px-3 py-2 text-sm">
                      <AlertTriangle className={`w-4 h-4 ${['phone_detected', 'multiple_faces'].includes(e.type) ? 'text-rose-400' : 'text-amber-400'}`} />
                      <span className="flex-1">{EVENT_LABELS[e.type] || e.type}</span>
                      <span className="text-xs text-zinc-500">Q{e.question ?? '?'} · {fmt(e.at)}</span>
                    </div>
                  ))}
                </div>
              ) : <div className="text-sm text-zinc-500">No live warnings recorded.</div>}
            </div>
            <div>
              <div className="text-sm font-semibold mb-2">Transcript</div>
              <div className="space-y-2">
                {data.transcript.map((m: any, i: number) => (
                  <div key={i} className={`text-sm rounded-lg px-3 py-2 ${m.role === 'user' || m.role === 'candidate' ? 'bg-zinc-800/60 ml-8' : 'bg-rose-500/5 border border-rose-500/10 mr-8'}`}>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{m.role === 'user' || m.role === 'candidate' ? 'Candidate' : 'Interviewer'}</div>
                    {m.content || m.text}
                  </div>
                ))}
                {!data.transcript.length && <div className="text-sm text-zinc-500">No transcript.</div>}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ───────────────────────── audit logs ─────────────────────────
function Logs({ api, token }: { api: Api; token: string }) {
  const [category, setCategory] = useState('');
  const [severity, setSeverity] = useState('');
  const [q, setQ] = useState('');
  const [query, setQuery] = useState('');
  const [days, setDays] = useState(7);
  const [page, setPage] = useState(0);
  const limit = 50;
  const params = `category=${category}&severity=${severity}&q=${encodeURIComponent(query)}&days=${days}`;
  const { data, error, loading, reload } = useLoad<any>(() => api(`/admin/logs?${params}&limit=${limit}&offset=${page * limit}`), [api, params, page]);

  const exportCsv = async () => {
    const r = await fetch(`${API}/admin/logs.csv?${params}`, { headers: { Authorization: `Bearer ${token}` } });
    const blob = await r.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = `gapx-audit-${new Date().toISOString().slice(0, 10)}.csv`; a.click();
    URL.revokeObjectURL(a.href);
  };

  const sel = 'bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:border-zinc-600';
  return (
    <>
      <Header title="Audit logs" sub="Every sign-in, sign-up, proctoring warning, submission and admin action" onRefresh={reload}>
        <button onClick={exportCsv} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg border border-zinc-800 text-zinc-300 hover:bg-zinc-800"><Download className="w-4 h-4" /> Export CSV</button>
      </Header>
      <div className="flex flex-wrap gap-2 mb-4">
        <select value={category} onChange={e => { setCategory(e.target.value); setPage(0); }} className={sel}>
          <option value="">All categories</option>
          {['auth', 'integrity', 'interview', 'coding', 'admin'].map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={severity} onChange={e => { setSeverity(e.target.value); setPage(0); }} className={sel}>
          <option value="">All severities</option>
          {['info', 'warning', 'critical'].map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={days} onChange={e => { setDays(+e.target.value); setPage(0); }} className={sel}>
          {[[1, 'Last 24 hours'], [7, 'Last 7 days'], [30, 'Last 30 days'], [0, 'All time']].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <form onSubmit={e => { e.preventDefault(); setQuery(q); setPage(0); }} className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search email or event, press Enter" className={`${sel} w-full pl-9`} />
        </form>
      </div>
      <Status loading={loading && !data} error={error} />
      {data && (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-zinc-500 border-b border-zinc-800">
              {['Time', 'Severity', 'Category', 'Event', 'User', 'IP', 'Details'].map(h => <th key={h} className="px-4 py-3 font-medium">{h}</th>)}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/70">
              {data.logs.map((l: any) => (
                <tr key={l.id} className="hover:bg-zinc-800/30">
                  <td className="px-4 py-2.5 whitespace-nowrap text-zinc-400">{fmt(l.time)}</td>
                  <td className="px-4 py-2.5"><span className={`text-[11px] px-2 py-0.5 rounded-full border ${SEV_STYLE[l.severity] || SEV_STYLE.info}`}>{l.severity}</span></td>
                  <td className="px-4 py-2.5 text-zinc-400">{l.category}</td>
                  <td className="px-4 py-2.5 font-medium whitespace-nowrap">{EVENT_LABELS[l.event] || l.event}</td>
                  <td className="px-4 py-2.5 text-zinc-300">{l.user || '—'}</td>
                  <td className="px-4 py-2.5 text-zinc-500 font-mono text-xs">{l.ip || '—'}</td>
                  <td className="px-4 py-2.5 text-zinc-500 text-xs max-w-[320px] truncate" title={JSON.stringify(l.details)}>
                    {Object.entries(l.details || {}).map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' · ') || '—'}
                  </td>
                </tr>
              ))}
              {!data.logs.length && <tr><td colSpan={7} className="px-4 py-10 text-center text-zinc-500">No log entries match these filters.</td></tr>}
            </tbody>
          </table>
          <div className="flex items-center justify-between px-4 py-3 border-t border-zinc-800 text-xs text-zinc-500">
            <span>{data.total} entries</span>
            <div className="flex gap-2">
              <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded border border-zinc-800 disabled:opacity-40 hover:bg-zinc-800">Previous</button>
              <button disabled={(page + 1) * limit >= data.total} onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded border border-zinc-800 disabled:opacity-40 hover:bg-zinc-800">Next</button>
            </div>
          </div>
        </Card>
      )}
    </>
  );
}

// ───────────────────────── users ─────────────────────────
function UsersTab({ api }: { api: Api }) {
  const [q, setQ] = useState('');
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState<number | null>(null);
  const { data, error, loading, reload } = useLoad<any>(() => api(`/admin/users?q=${encodeURIComponent(query)}&limit=100`), [api, query]);
  return (
    <>
      <Header title="Users" sub="Search students, see their progress, disable abusive accounts" onRefresh={reload} />
      <form onSubmit={e => { e.preventDefault(); setQuery(q); }} className="relative mb-4 max-w-md">
        <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search by name or email, press Enter" className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-3 py-2 text-sm outline-none focus:border-zinc-600" />
      </form>
      <Status loading={loading && !data} error={error} />
      {data && (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-zinc-500 border-b border-zinc-800">
              {['User', 'Target role', 'Level / XP', 'Joined', 'Last login', 'Status', ''].map(h => <th key={h} className="px-4 py-3 font-medium">{h}</th>)}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/70">
              {data.users.map((u: any) => (
                <tr key={u.id} className="hover:bg-zinc-800/30">
                  <td className="px-4 py-2.5"><div className="font-medium">{u.name} {u.is_admin && <span className="text-[10px] ml-1 px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300">ADMIN</span>}</div><div className="text-xs text-zinc-500">{u.email}</div></td>
                  <td className="px-4 py-2.5 text-zinc-400">{u.target_role || '—'}</td>
                  <td className="px-4 py-2.5 text-zinc-400">L{u.level} · {u.xp} XP</td>
                  <td className="px-4 py-2.5 text-zinc-400 whitespace-nowrap">{fmt(u.created_at)}</td>
                  <td className="px-4 py-2.5 text-zinc-400 whitespace-nowrap">{fmt(u.last_login_at)}</td>
                  <td className="px-4 py-2.5">{u.is_active ? <span className="text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Active</span> : <span className="text-rose-400 text-xs flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> Disabled</span>}</td>
                  <td className="px-4 py-2.5 text-right"><button onClick={() => setOpen(u.id)} className="text-sm px-3 py-1 rounded-lg border border-zinc-700 hover:bg-zinc-800">Details</button></td>
                </tr>
              ))}
              {!data.users.length && <tr><td colSpan={7} className="px-4 py-10 text-center text-zinc-500">No users found.</td></tr>}
            </tbody>
          </table>
          <div className="px-4 py-3 border-t border-zinc-800 text-xs text-zinc-500">{data.total} users</div>
        </Card>
      )}
      {open !== null && <UserDrawer api={api} id={open} onClose={() => setOpen(null)} onChanged={reload} />}
    </>
  );
}

function UserDrawer({ api, id, onClose, onChanged }: { api: Api; id: number; onClose: () => void; onChanged: () => void }) {
  const { data, error, loading, reload } = useLoad<any>(() => api(`/admin/users/${id}`), [api, id]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const toggle = async () => {
    const active = !data.is_active;
    const reason = active ? '' : (window.prompt('Reason for disabling this account (saved in the audit log):') ?? null);
    if (reason === null) return;
    setBusy(true); setMsg('');
    try {
      await api(`/admin/users/${id}/status`, { method: 'POST', body: JSON.stringify({ active, reason }) });
      reload(); onChanged();
    } catch (e: any) { setMsg(e.message); } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={onClose}>
      <div className="w-full max-w-xl h-full overflow-y-auto bg-zinc-950 border-l border-zinc-800 p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold">User details</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-800"><X className="w-5 h-5" /></button>
        </div>
        <Status loading={loading && !data} error={error} />
        {data && (
          <div className="space-y-5 text-sm">
            <div>
              <div className="text-xl font-semibold">{data.name}</div>
              <div className="text-zinc-500">{data.email}</div>
              <div className="text-zinc-400 mt-2">{data.target_role || 'No target role'} · L{data.level} · {data.xp} XP · {data.problems_solved} problems solved</div>
              {!!data.skills.length && <div className="flex flex-wrap gap-1.5 mt-3">{data.skills.map((s: string) => <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300">{s}</span>)}</div>}
            </div>
            <div className="flex items-center gap-3">
              <button disabled={busy || data.is_admin} onClick={toggle}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium disabled:opacity-40 ${data.is_active ? 'bg-rose-600 hover:bg-rose-500 text-white' : 'bg-emerald-600 hover:bg-emerald-500 text-white'}`}>
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : data.is_active ? <UserX className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                {data.is_active ? 'Disable account' : 'Re-enable account'}
              </button>
              {data.is_admin && <span className="text-xs text-zinc-500">Admin accounts can't be disabled here.</span>}
            </div>
            {msg && <div className="text-rose-400">{msg}</div>}
            <div>
              <div className="font-semibold mb-2">Interviews</div>
              {data.interviews.length ? data.interviews.map((i: any) => (
                <div key={i.id} className="flex items-center gap-3 py-2 border-b border-zinc-800/70">
                  {i.integrity?.flagged ? <ShieldAlert className="w-4 h-4 text-rose-400" /> : <ShieldCheck className="w-4 h-4 text-emerald-400" />}
                  <span className="flex-1">{i.role} · {i.type}</span>
                  <span className="text-zinc-400">score {i.score || '—'}</span>
                  <span className="text-xs text-zinc-500">{fmt(i.created_at)}</span>
                </div>
              )) : <div className="text-zinc-500">No interviews yet.</div>}
            </div>
            <div>
              <div className="font-semibold mb-2">Recent activity</div>
              {data.recent_activity.length ? data.recent_activity.map((l: any) => (
                <div key={l.id} className="flex items-center gap-3 py-1.5">
                  <Activity className="w-3.5 h-3.5 text-zinc-500" />
                  <span className="flex-1">{l.category} · {EVENT_LABELS[l.event] || l.event}</span>
                  <span className={`text-[11px] px-2 py-0.5 rounded-full border ${SEV_STYLE[l.severity] || SEV_STYLE.info}`}>{l.severity}</span>
                  <span className="text-xs text-zinc-500">{fmt(l.time)}</span>
                </div>
              )) : <div className="text-zinc-500">No recorded activity.</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ───────────────────────── problems ─────────────────────────
const TYPES = ['int', 'double', 'bool', 'string', 'int[]', 'string[]', 'int[][]'];
const field = 'w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:border-rose-500/60';
const lbl = 'block text-xs font-medium text-zinc-400 mb-1.5';

type TestRow = { input: string; output: string; is_hidden: boolean };
const blankProblem = () => ({
  title: '', difficulty: 'Easy', category: '', statement: '', constraints: '', explanation: '', fn: '',
  params: [['nums', 'int[]']] as string[][], returns: 'int',
  tests: [{ input: '', output: '', is_hidden: false }, { input: '', output: '', is_hidden: false }, { input: '', output: '', is_hidden: true }] as TestRow[],
  hints: '', company_tags: '', time_complexity: 'O(N)', space_complexity: 'O(1)', unordered: false, reference_solution: '', editorial: '',
});

function Problems({ api }: { api: Api }) {
  const { data, error, loading, reload } = useLoad<any[]>(() => api('/admin/problems'), [api]);
  const [editing, setEditing] = useState<{ id: number | null } | null>(null);
  const [filter, setFilter] = useState<'all' | 'custom'>('all');
  const diff: Record<string, string> = { Easy: 'text-emerald-400', Medium: 'text-amber-400', Hard: 'text-rose-400' };
  const remove = async (p: any) => {
    if (!window.confirm(`Delete "${p.title}"? Students will no longer see it.`)) return;
    try { await api(`/admin/problems/${p.id}`, { method: 'DELETE' }); reload(); } catch (e: any) { alert(e.message); }
  };
  const rows = (data || []).filter(p => filter === 'all' || p.is_custom);
  return (
    <>
      <Header title="Problems" sub="Add your own coding problems and see how students are doing on each one" onRefresh={reload}>
        <select value={filter} onChange={e => setFilter(e.target.value as any)} className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm">
          <option value="all">All problems</option><option value="custom">Added by admins</option>
        </select>
        <button onClick={() => setEditing({ id: null })} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold"><Plus className="w-4 h-4" /> Add problem</button>
      </Header>
      <Status loading={loading && !data} error={error} />
      {data && (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-zinc-500 border-b border-zinc-800">
              {['#', 'Title', 'Difficulty', 'Category', 'Tests', 'Attempts', 'Acceptance', ''].map(h => <th key={h} className="px-4 py-3 font-medium">{h}</th>)}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/70">
              {rows.map(p => (
                <tr key={p.id} className="hover:bg-zinc-800/30">
                  <td className="px-4 py-2.5 text-zinc-500">{p.id}</td>
                  <td className="px-4 py-2.5 font-medium">{p.title} {p.is_custom && <span className="text-[10px] ml-1 px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300">ADDED</span>}</td>
                  <td className={`px-4 py-2.5 ${diff[p.difficulty] || ''}`}>{p.difficulty}</td>
                  <td className="px-4 py-2.5 text-zinc-400">{p.category}</td>
                  <td className="px-4 py-2.5 text-zinc-400">{p.tests}</td>
                  <td className="px-4 py-2.5 text-zinc-400">{p.attempts}</td>
                  <td className="px-4 py-2.5">
                    {p.acceptance === null ? <span className="text-zinc-600">—</span> : (
                      <div className="flex items-center gap-2"><div className="w-20 h-1.5 rounded bg-zinc-800"><div className="h-full rounded bg-emerald-500" style={{ width: `${p.acceptance}%` }} /></div><span className="text-xs text-zinc-400">{p.acceptance}%</span></div>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-right whitespace-nowrap">
                    {p.is_custom && <>
                      <button onClick={() => setEditing({ id: p.id })} className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400" title="Edit"><Pencil className="w-4 h-4" /></button>
                      <button onClick={() => remove(p)} className="p-1.5 rounded hover:bg-zinc-800 text-rose-400" title="Delete"><Trash2 className="w-4 h-4" /></button>
                    </>}
                  </td>
                </tr>
              ))}
              {!rows.length && <tr><td colSpan={8} className="px-4 py-10 text-center text-zinc-500">No problems added yet. Click &ldquo;Add problem&rdquo;.</td></tr>}
            </tbody>
          </table>
        </Card>
      )}
      {editing && <ProblemEditor api={api} id={editing.id} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); }} />}
    </>
  );
}

function ProblemEditor({ api, id, onClose, onSaved }: { api: Api; id: number | null; onClose: () => void; onSaved: () => void }) {
  const [f, setF] = useState(blankProblem());
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [loadingExisting, setLoadingExisting] = useState(id !== null);
  const set = (k: string, v: any) => setF(prev => ({ ...prev, [k]: v }));

  useEffect(() => {
    if (id === null) return;
    api(`/admin/problems/${id}`).then(p => {
      setF({
        ...blankProblem(), title: p.title, difficulty: p.difficulty, category: p.category, statement: p.statement,
        constraints: p.constraints, explanation: p.explanation, fn: p.signature?.fn || '', params: p.signature?.params || [],
        returns: p.signature?.returns || 'int', unordered: !!p.signature?.unordered,
        tests: p.tests.map((t: any) => ({ input: t.input, output: t.output, is_hidden: !!t.is_hidden })),
        hints: p.hints.join('\n'), company_tags: p.company_tags.join(', '), time_complexity: p.time_complexity, space_complexity: p.space_complexity,
      });
    }).catch(e => setErr(e.message)).finally(() => setLoadingExisting(false));
  }, [api, id]);

  const save = async () => {
    setBusy(true); setErr('');
    try {
      const body = { ...f, hints: f.hints.split('\n').filter(Boolean), company_tags: f.company_tags.split(',').filter(s => s.trim()) };
      await api(id === null ? '/admin/problems' : `/admin/problems/${id}`, { method: id === null ? 'POST' : 'PUT', body: JSON.stringify(body) });
      onSaved();
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };

  const setParam = (i: number, j: number, v: string) => set('params', f.params.map((p, k) => (k === i ? (j === 0 ? [v, p[1]] : [p[0], v]) : p)));
  const setTest = (i: number, k: keyof TestRow, v: any) => set('tests', f.tests.map((t, n) => (n === i ? { ...t, [k]: v } : t)));

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={onClose}>
      <div className="w-full max-w-3xl h-full overflow-y-auto bg-zinc-950 border-l border-zinc-800" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 bg-zinc-950/95 backdrop-blur border-b border-zinc-800">
          <h2 className="text-lg font-bold">{id === null ? 'Add a coding problem' : 'Edit problem'}</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-zinc-800"><X className="w-5 h-5" /></button>
        </div>
        {loadingExisting ? <Status loading error="" /> : (
          <div className="p-6 space-y-6 text-sm">
            <section className="space-y-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-rose-300">1 · The problem</div>
              <div className="grid grid-cols-[1fr_140px] gap-3">
                <div><label className={lbl}>Title</label><input className={field} value={f.title} onChange={e => set('title', e.target.value)} placeholder="e.g. Sum of Squares" /></div>
                <div><label className={lbl}>Difficulty</label><select className={field} value={f.difficulty} onChange={e => set('difficulty', e.target.value)}>{['Easy', 'Medium', 'Hard'].map(d => <option key={d}>{d}</option>)}</select></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className={lbl}>Category</label><input className={field} value={f.category} onChange={e => set('category', e.target.value)} placeholder="Arrays, Strings, DP…" /></div>
                <div><label className={lbl}>Company tags (comma separated)</label><input className={field} value={f.company_tags} onChange={e => set('company_tags', e.target.value)} placeholder="Amazon, TCS" /></div>
              </div>
              <div><label className={lbl}>Problem statement (Markdown allowed: `code`, **bold**)</label><textarea rows={5} className={field} value={f.statement} onChange={e => set('statement', e.target.value)} placeholder="Given an integer array `nums`, return…" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className={lbl}>Constraints (one per line)</label><textarea rows={3} className={field} value={f.constraints} onChange={e => set('constraints', e.target.value)} placeholder={'1 <= nums.length <= 10^5'} /></div>
                <div><label className={lbl}>Example explanation</label><textarea rows={3} className={field} value={f.explanation} onChange={e => set('explanation', e.target.value)} placeholder="1² + 2² + 3² = 14" /></div>
              </div>
            </section>

            <section className="space-y-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-rose-300">2 · The function students write</div>
              <div className="grid grid-cols-[1fr_160px] gap-3">
                <div><label className={lbl}>Function name</label><input className={`${field} font-mono`} value={f.fn} onChange={e => set('fn', e.target.value.replace(/[^A-Za-z0-9_]/g, ''))} placeholder="sumSquares" /></div>
                <div><label className={lbl}>Returns</label><select className={`${field} font-mono`} value={f.returns} onChange={e => set('returns', e.target.value)}>{TYPES.map(t => <option key={t}>{t}</option>)}</select></div>
              </div>
              <div>
                <label className={lbl}>Parameters (in order)</label>
                <div className="space-y-2">
                  {f.params.map((p, i) => (
                    <div key={i} className="flex gap-2">
                      <input className={`${field} font-mono`} value={p[0]} onChange={e => setParam(i, 0, e.target.value.replace(/[^A-Za-z0-9_]/g, ''))} placeholder="name" />
                      <select className={`${field} font-mono w-40`} value={p[1]} onChange={e => setParam(i, 1, e.target.value)}>{TYPES.map(t => <option key={t}>{t}</option>)}</select>
                      <button onClick={() => set('params', f.params.filter((_, k) => k !== i))} className="px-2 text-zinc-500 hover:text-rose-400"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  ))}
                  <button onClick={() => set('params', [...f.params, ['', 'int']])} className="text-xs text-rose-300 hover:underline">+ Add parameter</button>
                </div>
              </div>
              <p className="text-xs text-zinc-500">Starter code for Python, JavaScript, Java, C++ and C is generated from this automatically.</p>
            </section>

            <section className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-rose-300">3 · Test cases</div>
              <p className="text-xs text-zinc-500">Input: one line per parameter, e.g. <code className="text-zinc-300">[1,2,3]</code> then <code className="text-zinc-300">5</code>. Strings are written as plain text. Hidden tests are only used when a student submits.</p>
              {f.tests.map((t, i) => (
                <div key={i} className="grid grid-cols-[1fr_1fr_auto] gap-2 items-start p-3 rounded-lg border border-zinc-800 bg-zinc-900/40">
                  <div><label className={lbl}>Test {i + 1} input</label><textarea rows={Math.max(2, f.params.length)} className={`${field} font-mono`} value={t.input} onChange={e => setTest(i, 'input', e.target.value)} placeholder={f.params.map(p => p[1] === 'int[]' ? '[1,2,3]' : p[1] === 'string' ? 'hello' : p[1] === 'int' ? '5' : p[1]).join('\n')} /></div>
                  <div><label className={lbl}>Expected output</label><input className={`${field} font-mono`} value={t.output} onChange={e => setTest(i, 'output', e.target.value)} placeholder={f.reference_solution ? 'leave empty to compute' : 'e.g. 14 or 1,2'} /></div>
                  <div className="flex flex-col items-end gap-2 pt-5">
                    <label className="flex items-center gap-1.5 text-xs text-zinc-400"><input type="checkbox" className="accent-rose-500" checked={t.is_hidden} onChange={e => setTest(i, 'is_hidden', e.target.checked)} /> Hidden</label>
                    <button onClick={() => set('tests', f.tests.filter((_, k) => k !== i))} className="text-zinc-500 hover:text-rose-400"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
              ))}
              <div className="flex items-center gap-4">
                <button onClick={() => set('tests', [...f.tests, { input: '', output: '', is_hidden: true }])} className="text-xs text-rose-300 hover:underline">+ Add test case</button>
                <label className="flex items-center gap-1.5 text-xs text-zinc-400"><input type="checkbox" className="accent-rose-500" checked={f.unordered} onChange={e => set('unordered', e.target.checked)} /> Answer order doesn&apos;t matter</label>
              </div>
            </section>

            <section className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-rose-300">4 · Reference solution (recommended)</div>
              <p className="text-xs text-zinc-500">A correct Python solution. It&apos;s run against every test before saving: it fills empty expected outputs and catches wrong ones. It&apos;s also shown as the editorial.</p>
              <textarea rows={7} spellCheck={false} className={`${field} font-mono text-xs`} value={f.reference_solution} onChange={e => set('reference_solution', e.target.value)}
                placeholder={`class Solution:\n    def ${f.fn || 'sumSquares'}(self, ${f.params.map(p => p[0]).join(', ') || 'nums'}):\n        return ...`} />
            </section>

            <section className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-rose-300">5 · Hints & complexity</div>
              <div><label className={lbl}>Hints (one per line, revealed one at a time)</label><textarea rows={3} className={field} value={f.hints} onChange={e => set('hints', e.target.value)} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className={lbl}>Expected time</label><input className={`${field} font-mono`} value={f.time_complexity} onChange={e => set('time_complexity', e.target.value)} /></div>
                <div><label className={lbl}>Expected space</label><input className={`${field} font-mono`} value={f.space_complexity} onChange={e => set('space_complexity', e.target.value)} /></div>
              </div>
            </section>

            {err && <div className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-4 py-3">{err}</div>}
            <div className="flex justify-end gap-2 pb-6">
              <button onClick={onClose} className="px-4 py-2 rounded-lg border border-zinc-800 hover:bg-zinc-800">Cancel</button>
              <button disabled={busy} onClick={save} className="flex items-center gap-2 px-5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-60 text-white font-semibold">
                {busy && <Loader2 className="w-4 h-4 animate-spin" />} {busy ? 'Checking tests…' : id === null ? 'Check & publish' : 'Check & save'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ───────────────────────── interview questions ─────────────────────────
function InterviewQuestions({ api }: { api: Api }) {
  const { data, error, loading, reload } = useLoad<any>(() => api('/admin/interview-questions'), [api]);
  const blank = { track: 'frontend', topic: '', level: 'Medium', question: '', key_points: '', ideal_answer: '', hint: '' };
  const [f, setF] = useState(blank);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const set = (k: string, v: string) => setF(prev => ({ ...prev, [k]: v }));
  const words = f.question.trim() ? f.question.trim().split(/\s+/).length : 0;

  const save = async () => {
    setBusy(true); setErr('');
    try {
      await api('/admin/interview-questions', { method: 'POST', body: JSON.stringify({ ...f, key_points: f.key_points.split('\n').filter(s => s.trim()) }) });
      setF({ ...blank, track: f.track }); setOpen(false); reload();
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  const remove = async (q: any) => {
    if (!window.confirm('Delete this question? It will stop appearing in interviews.')) return;
    try { await api(`/admin/interview-questions/${q.id}`, { method: 'DELETE' }); reload(); } catch (e: any) { alert(e.message); }
  };
  const label = (id: string) => data?.tracks.find((t: any) => t.id === id)?.label || id;

  return (
    <>
      <Header title="Interview questions" sub="Add technical questions for any role. They're asked first in that role's mock interviews and scored on your key points." onRefresh={reload}>
        <button onClick={() => setOpen(o => !o)} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold"><Plus className="w-4 h-4" /> Add question</button>
      </Header>
      <Status loading={loading && !data} error={error} />
      {open && data && (
        <Card className="p-5 mb-6 space-y-4 text-sm">
          <div className="grid grid-cols-3 gap-3">
            <div><label className={lbl}>Role / track</label><select className={field} value={f.track} onChange={e => set('track', e.target.value)}>{data.tracks.map((t: any) => <option key={t.id} value={t.id}>{t.label}</option>)}</select></div>
            <div><label className={lbl}>Topic</label><input className={field} value={f.topic} onChange={e => set('topic', e.target.value)} placeholder="React Hooks" /></div>
            <div><label className={lbl}>Level</label><select className={field} value={f.level} onChange={e => set('level', e.target.value)}>{['Easy', 'Medium', 'Hard'].map(d => <option key={d}>{d}</option>)}</select></div>
          </div>
          <div>
            <label className={lbl}>Question <span className={words > 40 ? 'text-rose-400' : 'text-zinc-500'}>({words}/40 words, keep it to 2 lines)</span></label>
            <textarea rows={2} className={field} value={f.question} onChange={e => set('question', e.target.value)} placeholder="What does the useEffect hook do, and when does it run?" />
          </div>
          <div>
            <label className={lbl}>Key points a good answer mentions (one per line; add synonyms after commas)</label>
            <textarea rows={3} className={`${field} font-mono text-xs`} value={f.key_points} onChange={e => set('key_points', e.target.value)} placeholder={'side effects, side effect\ndependency array, dependencies, deps\ncleanup, clean up'} />
          </div>
          <div><label className={lbl}>Model answer (shown in the feedback report)</label><textarea rows={3} className={field} value={f.ideal_answer} onChange={e => set('ideal_answer', e.target.value)} /></div>
          <div><label className={lbl}>Hint (if the candidate asks for help, optional)</label><input className={field} value={f.hint} onChange={e => set('hint', e.target.value)} /></div>
          {err && <div className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-4 py-3">{err}</div>}
          <div className="flex justify-end gap-2">
            <button onClick={() => setOpen(false)} className="px-4 py-2 rounded-lg border border-zinc-800 hover:bg-zinc-800">Cancel</button>
            <button disabled={busy} onClick={save} className="flex items-center gap-2 px-5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-60 text-white font-semibold">{busy && <Loader2 className="w-4 h-4 animate-spin" />} Save question</button>
          </div>
        </Card>
      )}
      {data && (
        <>
          <div className="flex flex-wrap gap-2 mb-4">
            {data.tracks.map((t: any) => {
              const added = data.questions.filter((q: any) => q.track === t.id).length;
              return <span key={t.id} className="text-xs px-2.5 py-1 rounded-full border border-zinc-800 text-zinc-400">{t.label}: {t.built_in} built-in{added ? <b className="text-rose-300"> + {added} added</b> : ''}</span>;
            })}
          </div>
          <div className="space-y-3">
            {data.questions.map((q: any) => (
              <Card key={q.id} className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-zinc-500 mb-1">{label(q.track)} · {q.topic} · {q.level} · added by {q.created_by} · {fmt(q.created_at)}</div>
                    <div className="font-medium">{q.question}</div>
                    <div className="flex flex-wrap gap-1.5 mt-2">{q.key_points.map((k: string) => <span key={k} className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300">{k.split(',')[0]}</span>)}</div>
                  </div>
                  <button onClick={() => remove(q)} className="p-1.5 rounded hover:bg-zinc-800 text-rose-400" title="Delete"><Trash2 className="w-4 h-4" /></button>
                </div>
              </Card>
            ))}
            {!data.questions.length && <Card className="p-10 text-center text-sm text-zinc-500">No questions added yet. The built-in question bank is used.</Card>}
          </div>
        </>
      )}
    </>
  );
}

// ───────────────────────── system ─────────────────────────
function SystemTab({ api }: { api: Api }) {
  const { data, error, loading, reload } = useLoad<any>(() => api('/admin/system'), [api]);
  const Row = ({ label, ok, note }: { label: string; ok: boolean; note?: string }) => (
    <div className="flex items-center gap-3 px-4 py-3">
      {ok ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-zinc-600" />}
      <span className="flex-1">{label}</span>
      <span className={`text-xs ${ok ? 'text-emerald-400' : 'text-zinc-500'}`}>{note || (ok ? 'Ready' : 'Not configured')}</span>
    </div>
  );
  return (
    <>
      <Header title="System" sub="Which services are switched on right now" onRefresh={reload} />
      <Status loading={loading && !data} error={error} />
      {data && (
        <div className="grid lg:grid-cols-2 gap-4">
          <Card className="divide-y divide-zinc-800">
            <div className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">Services</div>
            <Row label="AI provider" ok={data.ai_provider !== 'offline'} note={`${data.ai_provider}${data.ai_model ? ` · ${data.ai_model}` : ''}`} />
            <Row label="Natural voice (Gemini TTS)" ok={data.natural_voice && !data.voice_quota_used_up} note={data.voice_quota_used_up ? 'Daily quota used up' : data.natural_voice ? 'Ready' : 'Off'} />
            <Row label="Verification e-mails (SMTP)" ok={data.email_sending} note={data.email_sending ? 'Ready' : 'Codes printed in backend console'} />
            <Row label="Google sign-in" ok={data.google_sign_in} />
            <Row label="Environment" ok note={data.environment} />
          </Card>
          <Card className="divide-y divide-zinc-800">
            <div className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">Code runners</div>
            <Row label="Python" ok={data.code_runners.python} />
            <Row label="JavaScript (Node)" ok={data.code_runners.javascript} />
            <Row label="Java" ok={data.code_runners.java} />
            <Row label="C++ (g++)" ok={data.code_runners.cpp} note={data.code_runners.cpp ? 'Ready' : 'Install GCC'} />
            <Row label="C (gcc)" ok={data.code_runners.c} note={data.code_runners.c ? 'Ready' : 'Install GCC'} />
            <Row label="Judge0 sandbox" ok={data.code_runners.judge0_sandbox} note={data.code_runners.judge0_sandbox ? 'Ready' : 'Local runner in use'} />
          </Card>
        </div>
      )}
    </>
  );
}
