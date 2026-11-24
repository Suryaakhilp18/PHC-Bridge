import React, { useEffect, useMemo, useState } from 'react';
import { QRCodeCanvas } from 'qrcode.react';
import {
  Activity, ArrowDownLeft, ArrowUpRight, Bell, Building2, CalendarDays, Check,
  CheckCircle2, ChevronDown, CircleHelp, ClipboardList, Clock3, CloudOff, FilePlus2,
  HeartPulse, LayoutDashboard, LogOut, Menu, MoreHorizontal, Plus, RefreshCw,
  Search, ShieldCheck, Users, Wifi, X, QrCode, Stethoscope, AlertCircle, Bot,
  Sparkles, Printer, UserPlus, Download, Languages, CheckCheck, Eye, Network,
  AlertTriangle, MapPin
} from 'lucide-react';

import QRScannerModal from './components/QRScannerModal';
import AIOperationsModal from './components/AIOperationsModal';
import AIQualityBadge from './components/AIQualityBadge';
import PatientRegistry from './components/PatientRegistry';
import NotificationCenter from './components/NotificationCenter';
import PrintSlipModal from './components/PrintSlipModal';
import JourneySummaryModal from './components/JourneySummaryModal';
import FHIRModal from './components/FHIRModal';
import FacilityDirectoryView from './components/FacilityDirectoryView';
import {
  queueOfflineReferral, getOfflineQueue, clearOfflineQueue,
  cacheReferrals, getCachedReferrals
} from './utils/indexedDB';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ROLES = [
  { id: 'state_admin', label: 'State Mission Director', desc: 'Statewide governance & institutional monitoring', icon: ShieldCheck },
  { id: 'district_admin', label: 'District Health Officer (DHO)', desc: 'District network & SLA bottleneck oversight', icon: Activity },
  { id: 'phc', label: 'PHC Medical Officer', desc: 'Primary triage, AI referral drafting & QR slips', icon: Stethoscope },
  { id: 'hospital', label: 'Hospital Specialist', desc: 'Triage QR optical scanning & back-referrals', icon: Building2 },
  { id: 'cho', label: 'Community Health Officer (CHO)', desc: 'Home visits & patient follow-up completion', icon: Users },
];

const emptyForm = {
  patient_name: '',
  age: '',
  sex: 'Female',
  patient_code: '',
  phone: '',
  source_phc: 'Patamata Primary Health Centre',
  destination: 'Vijayawada Government General Hospital',
  reason: '',
  priority: 'Routine'
};

export default function App() {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('phc-user') || 'null'));
  const [token, setToken] = useState(() => localStorage.getItem('phc-token') || '');
  const [referrals, setReferrals] = useState([]);
  const [followups, setFollowups] = useState([]);
  const [metrics, setMetrics] = useState({
    total: 0, pending: 0, acknowledged: 0, completed: 0,
    back_referrals: 0, followups_due: 0, overdue_followups: 0,
    avg_ack_hours: 2.4, completion_rate_pct: 0,
    facility_workloads: [], monthly_trends: []
  });
  const [notifications, setNotifications] = useState([]);
  const [page, setPage] = useState('Overview');
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');

  // Modals & Drawers
  const [selected, setSelected] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showOutcome, setShowOutcome] = useState(null);
  const [showScanner, setShowScanner] = useState(false);
  const [showAIOps, setShowAIOps] = useState(false);
  const [showPrintSlip, setShowPrintSlip] = useState(null);
  const [showJourneySummary, setShowJourneySummary] = useState(null);
  const [showFHIR, setShowFHIR] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);

  // Forms & State
  const [form, setForm] = useState(emptyForm);
  const [outcome, setOutcome] = useState({
    outcome_notes: 'Specialist consultation and evaluation completed at GGH. Returning patient to PHC for scheduled continuity review.',
    diagnosis_category: 'General Medicine',
    back_referral: true,
    follow_up_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10),
    follow_up_instructions: 'Review vitals, medication tolerance, and recovery progress at primary health centre.'
  });

  const [online, setOnline] = useState(navigator.onLine);
  const [queue, setQueue] = useState([]);
  const [notice, setNotice] = useState('');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [timeline, setTimeline] = useState([]);

  useEffect(() => {
    loadOfflineQueue();
    const handleOnline = () => {
      setOnline(true);
      setNotice('Network connection restored. Syncing offline records to state registry...');
      syncQueue();
    };
    const handleOffline = () => {
      setOnline(false);
      setNotice('Working in offline mode. Changes are secured locally in IndexedDB.');
    };
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (token) {
      refreshData();
    }
  }, [token]);

  useEffect(() => {
    if (notice) {
      const t = setTimeout(() => setNotice(''), 4000);
      return () => clearTimeout(t);
    }
  }, [notice]);

  async function loadOfflineQueue() {
    try {
      const q = await getOfflineQueue();
      setQueue(q);
    } catch (e) {
      console.warn('IndexedDB load error', e);
    }
  }

  async function api(path, options = {}) {
    const res = await fetch(API + path, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...options.headers
      }
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error(d.detail || 'Request failed');
    }
    return res.json();
  }

  async function login(roleId) {
    try {
      const res = await fetch(API + '/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: roleId })
      });
      if (!res.ok) throw new Error('Backend unavailable');
      const data = await res.json();
      setToken(data.token);
      setUser(data.user);
      localStorage.setItem('phc-token', data.token);
      localStorage.setItem('phc-user', JSON.stringify(data.user));
      setNotice(`Signed in as ${data.user.name} (${data.user.role.toUpperCase()})`);
    } catch (e) {
      setNotice('Unable to connect to backend API server. Ensure it is running.');
    }
  }

  function logout() {
    if (token) {
      api('/api/auth/logout', { method: 'POST' }).catch(() => {});
    }
    setUser(null);
    setToken('');
    localStorage.removeItem('phc-token');
    localStorage.removeItem('phc-user');
  }

  async function refreshData() {
    try {
      const [refs, mets, notifs, fus] = await Promise.all([
        api('/api/referrals'),
        api('/api/metrics'),
        api('/api/notifications').catch(() => []),
        api('/api/followups').catch(() => [])
      ]);
      setReferrals(refs);
      setMetrics(mets);
      setNotifications(notifs);
      setFollowups(fus);
      cacheReferrals(refs);
    } catch (e) {
      if (!navigator.onLine) {
        const cached = await getCachedReferrals();
        if (cached && cached.length) setReferrals(cached);
      }
    }
  }

  async function createReferral(e) {
    e.preventDefault();
    const payload = { ...form, age: parseInt(form.age || 30) };
    try {
      const r = await api('/api/referrals', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      setReferrals(v => [r, ...v]);
      setShowCreate(false);
      setForm(emptyForm);
      setNotice(`Referral ${r.id} successfully dispatched to destination facility.`);
      refreshData();
    } catch (err) {
      if (!navigator.onLine || err.message === 'Failed to fetch') {
        const queuedItem = await queueOfflineReferral(payload);
        setQueue(v => [...v, queuedItem]);
        setShowCreate(false);
        setForm(emptyForm);
        setNotice('Saved locally in IndexedDB. Will sync automatically when network returns.');
      } else {
        setNotice(err.message);
      }
    }
  }

  async function syncQueue() {
    const currentQueue = await getOfflineQueue();
    if (!currentQueue.length) {
      setNotice('Offline queue is empty.');
      return;
    }
    try {
      const res = await api('/api/sync', {
        method: 'POST',
        body: JSON.stringify(currentQueue)
      });
      await clearOfflineQueue();
      setQueue([]);
      setNotice(`${res.synced} offline referral(s) synchronized to central registry.`);
      refreshData();
    } catch (e) {
      setNotice('Offline synchronization failed. Check your network or credentials.');
    }
  }

  async function handleAction(path, body = null) {
    try {
      const res = await api(path, {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined
      });
      setNotice('Record updated successfully.');
      await refreshData();
      if (selected) {
        const r = await api(`/api/referrals/${selected.id}`);
        setSelected(r);
        setTimeline(r.events || []);
      }
      return res;
    } catch (e) {
      setNotice(e.message);
      throw e;
    }
  }

  async function openDetails(r) {
    setSelected(r);
    try {
      const detail = await api(`/api/referrals/${r.id}`);
      setSelected(detail);
      setTimeline(detail.events || []);
    } catch {
      setTimeline(r.events || []);
    }
  }

  async function handleScanSuccess(scannedCode) {
    try {
      const result = await api('/api/referrals/scan-qr', {
        method: 'POST',
        body: JSON.stringify({ ref: scannedCode, id: scannedCode })
      });
      setShowScanner(false);
      openDetails(result);
      setNotice(`Verified referral ${result.id} via optical scan.`);
    } catch (err) {
      throw new Error(err.message || 'Scanned QR code could not be verified.');
    }
  }

  // Filtered referrals
  const filtered = useMemo(() => referrals.filter(r => {
    const matches = [r.patient_name, r.id, r.patient_code, r.destination, r.source_phc].join(' ').toLowerCase().includes(query.toLowerCase());
    const matchesStatus = statusFilter === 'All' || r.status === statusFilter;
    const matchesPriority = priorityFilter === 'All' || r.priority === priorityFilter;
    return matches && matchesStatus && matchesPriority;
  }), [referrals, query, statusFilter, priorityFilter]);

  if (!user) return <Login onLogin={login} notice={notice} />;

  const roleName = ROLES.find(r => r.id === user.role)?.label || user.role;
  const unreadNotifs = notifications.filter(n => !n.is_read).length;

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><HeartPulse size={22} /></div>
          <div><b>PHC Bridge</b><small>AP DIGITAL HEALTHCARE</small></div>
          <button className="icon-btn mobile-close" onClick={() => setMobileOpen(false)}><X /></button>
        </div>

        <div className="facility">
          <span className="facility-dot" />
          <div>
            <b>{user.facility}</b>
            <small>Andhra Pradesh Health Network</small>
          </div>
        </div>

        <div className="nav-label">COMMAND CENTRE</div>
        <button className={`nav-item ${page === 'Overview' ? 'active' : ''}`} onClick={() => { setPage('Overview'); setMobileOpen(false); }}>
          <LayoutDashboard size={18} /> Overview
        </button>
        <button className={`nav-item ${page === 'Referrals' ? 'active' : ''}`} onClick={() => { setPage('Referrals'); setMobileOpen(false); }}>
          <ClipboardList size={18} /> Referral Registry <span className="nav-count">{referrals.length}</span>
        </button>
        <button className={`nav-item ${page === 'Follow-ups' ? 'active' : ''}`} onClick={() => { setPage('Follow-ups'); setMobileOpen(false); }}>
          <CalendarDays size={18} /> Follow-up Worklist {metrics.overdue_followups > 0 && <span className="nav-count alert">{metrics.overdue_followups}</span>}
        </button>
        <button className={`nav-item ${page === 'Patients' ? 'active' : ''}`} onClick={() => { setPage('Patients'); setMobileOpen(false); }}>
          <Users size={18} /> Patient Directory
        </button>
        <button className={`nav-item ${page === 'Facilities' ? 'active' : ''}`} onClick={() => { setPage('Facilities'); setMobileOpen(false); }}>
          <Building2 size={18} /> Facility Network
        </button>

        <div className="nav-label section-gap">INTELLIGENCE & OVERSIGHT</div>
        <button className={`nav-item ${page === 'Analytics' ? 'active' : ''}`} onClick={() => { setPage('Analytics'); setMobileOpen(false); }}>
          <Activity size={18} /> Operational Analytics
        </button>
        <button className={`nav-item ${page === 'Audit' ? 'active' : ''}`} onClick={() => { setPage('Audit'); setMobileOpen(false); }}>
          <ShieldCheck size={18} /> Audit & Provenance
        </button>

        {(user.role === 'admin' || user.role === 'state_admin' || user.role === 'district_admin') && (
          <button className="nav-item ai-nav-pill" onClick={() => setShowAIOps(true)}>
            <Bot size={18} /> AI Operations Copilot
          </button>
        )}

        <div className="sidebar-bottom">
          <div className={`connection ${online ? 'online' : 'offline'}`}>
            <span />
            {online ? <><Wifi size={15} /> State Grid (Online)</> : <><CloudOff size={15} /> Offline Resilience</>}
            <small>{queue.length} in queue</small>
          </div>
          <button className="sync-button" onClick={syncQueue}>
            <RefreshCw size={15} /> Sync Offline Queue {queue.length > 0 && <b>({queue.length})</b>}
          </button>
          <div className="profile">
            <div className="avatar">{user.name.split(' ').map(x => x[0]).slice(0, 2).join('')}</div>
            <div className="profile-text">
              <b>{user.name}</b>
              <small>{roleName}</small>
            </div>
            <button className="icon-btn" onClick={logout} title="Sign out"><LogOut size={17} /></button>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu-toggle" onClick={() => setMobileOpen(true)}><Menu /></button>
          <div className="crumb">Andhra Pradesh Health Mesh <span>/</span> <b>{page}</b></div>
          <div className="top-actions">
            {(user.role === 'hospital' || user.role === 'admin' || user.role === 'district_admin') && (
              <button className="secondary-btn small-btn" onClick={() => setShowScanner(true)}>
                <QrCode size={15} /> Triage QR Scanner
              </button>
            )}
            <div className={`top-status ${online ? '' : 'is-offline'}`}>
              <i />{online ? 'Active Bridge' : 'Offline Mode'}
            </div>
            <button className="icon-btn notification" onClick={() => setShowNotifications(!showNotifications)}>
              <Bell size={19} />
              {unreadNotifs > 0 && <span className="bell-badge">{unreadNotifs}</span>}
            </button>
            <div className="top-avatar">{user.name.split(' ').map(x => x[0]).slice(0, 2).join('')}</div>
          </div>

          {showNotifications && (
            <NotificationCenter
              notifications={notifications}
              onMarkRead={id => api(`/api/notifications/${id}/read`, { method: 'POST' }).then(refreshData)}
              onMarkAllRead={() => api('/api/notifications/read-all', { method: 'POST' }).then(refreshData)}
              onClose={() => setShowNotifications(false)}
              onNavigate={url => { setShowNotifications(false); setPage('Referrals'); }}
            />
          )}
        </header>

        <div className="content">
          <div className="welcome-row">
            <div>
              <div className="eyebrow">DIGITAL HEALTHCARE REFERRAL INTELLIGENCE</div>
              <h1>{page === 'Overview' ? `Welcome, ${user.name}` : page}</h1>
              <p>
                {page === 'Overview' ? `Continuity-of-care coordination for ${user.facility}.`
                  : page === 'Follow-ups' ? 'Frontline health worker visit schedules, medication compliance, and task completion.'
                  : page === 'Facilities' ? 'Authoritative Health Facility Registry (HFR) across Andhra Pradesh districts.'
                  : `Real-time management for ${page.toLowerCase()} across public health institutions.`}
              </p>
            </div>
            <div className="welcome-actions">
              {(user.role === 'hospital' || user.role === 'district_admin') && (
                <button className="secondary-btn" onClick={() => setShowScanner(true)}>
                  <QrCode size={16} /> Scan QR
                </button>
              )}
              {(user.role === 'phc' || user.role === 'admin' || user.role === 'state_admin') && (
                <button className="primary-btn" onClick={() => setShowCreate(true)}>
                  <Plus size={16} /> Create Referral
                </button>
              )}
              {(user.role === 'admin' || user.role === 'state_admin' || user.role === 'district_admin') && (
                <button className="secondary-btn" onClick={() => setShowAIOps(true)}>
                  <Bot size={16} /> AI Operations
                </button>
              )}
            </div>
          </div>

          {page === 'Overview' && (
            <Overview
              metrics={metrics}
              referrals={referrals}
              onOpen={openDetails}
              onCreate={() => setShowCreate(true)}
              onScan={() => setShowScanner(true)}
              role={user.role}
            />
          )}

          {page === 'Referrals' && (
            <ReferralTable
              rows={filtered}
              query={query} setQuery={setQuery}
              statusFilter={statusFilter} setStatusFilter={setStatusFilter}
              priorityFilter={priorityFilter} setPriorityFilter={setPriorityFilter}
              onOpen={openDetails}
              role={user.role}
              onAcknowledge={id => handleAction(`/api/referrals/${id}/acknowledge`)}
              onOutcome={r => setShowOutcome(r)}
              onPrintSlip={r => setShowPrintSlip(r)}
              onViewFHIR={r => setShowFHIR(r)}
            />
          )}

          {page === 'Follow-ups' && (
            <FollowUpsTable
              tasks={followups}
              onRefresh={refreshData}
              api={api}
              setNotice={setNotice}
            />
          )}

          {page === 'Patients' && (
            <PatientRegistry
              api={api}
              onOpenReferral={openDetails}
              onCreateReferralForPatient={p => {
                setForm({
                  ...emptyForm,
                  patient_name: p.full_name,
                  age: p.age,
                  sex: p.sex,
                  patient_code: p.patient_code,
                  phone: p.phone || ''
                });
                setShowCreate(true);
              }}
            />
          )}

          {page === 'Facilities' && (
            <FacilityDirectoryView api={api} />
          )}

          {page === 'Analytics' && (
            <AnalyticsView metrics={metrics} api={api} />
          )}

          {page === 'Audit' && (
            <AuditTimelineView referrals={referrals} onOpen={openDetails} />
          )}

          <footer className="footer">
            <span>PHC Bridge <b>•</b> Andhra Pradesh Healthcare Coordination Platform</span>
            <span><ShieldCheck size={14} /> HL7 FHIR R4 & ABDM Compatible · Synthetic Patient Evaluation Mode</span>
          </footer>
        </div>
      </main>

      {/* MODAL 1: Create Referral with AI Quality Assistant */}
      {showCreate && (
        <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && setShowCreate(false)}>
          <div className="modal wide">
            <div className="modal-head">
              <h2>New Patient Referral Initiation</h2>
              <p>Register electronic referral record with real-time AI quality assistance.</p>
            </div>
            <form onSubmit={createReferral} className="form-grid">
              <label className="full">
                Patient Full Name
                <input
                  required
                  minLength={2}
                  value={form.patient_name}
                  onChange={e => setForm({ ...form, patient_name: e.target.value })}
                  placeholder="e.g. Ananya Devi"
                />
              </label>
              <label>
                Age
                <input
                  required
                  type="number"
                  min="0"
                  max="120"
                  value={form.age}
                  onChange={e => setForm({ ...form, age: e.target.value })}
                  placeholder="34"
                />
              </label>
              <label>
                Sex
                <select value={form.sex} onChange={e => setForm({ ...form, sex: e.target.value })}>
                  <option>Female</option>
                  <option>Male</option>
                  <option>Other</option>
                </select>
              </label>
              <label>
                Patient Reference Code
                <input
                  value={form.patient_code}
                  onChange={e => setForm({ ...form, patient_code: e.target.value })}
                  placeholder="AP-SYN-1004 (Auto if empty)"
                />
              </label>
              <label>
                Contact Number
                <input
                  value={form.phone}
                  onChange={e => setForm({ ...form, phone: e.target.value })}
                  placeholder="Primary contact"
                />
              </label>
              <label>
                Referring Facility (Origin)
                <input
                  required
                  value={form.source_phc}
                  onChange={e => setForm({ ...form, source_phc: e.target.value })}
                />
              </label>
              <label>
                Receiving Institution (Destination)
                <input
                  required
                  value={form.destination}
                  onChange={e => setForm({ ...form, destination: e.target.value })}
                />
              </label>
              <label className="full">
                Referral Rationale & Clinical Presentation
                <textarea
                  required
                  minLength={3}
                  rows={3}
                  value={form.reason}
                  onChange={e => setForm({ ...form, reason: e.target.value })}
                  placeholder="Enter presenting symptoms, provisional assessment, and rationale for specialist handoff..."
                />
              </label>
              <label>
                Priority & Response SLA
                <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}>
                  <option value="Routine">Routine (24h SLA)</option>
                  <option value="Urgent">Urgent (4h SLA)</option>
                  <option value="Emergency">Emergency (1h Fast-Track)</option>
                </select>
              </label>

              {/* Integrated AI Referral Quality Assistant */}
              <div className="full">
                <AIQualityBadge
                  form={form}
                  api={api}
                  onApplySuggestion={wording => setForm({ ...form, reason: wording })}
                />
              </div>

              <div className="full modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-btn">
                  <FilePlus2 size={16} /> Transmit Referral
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Record Consultation Outcome & Back-Referral */}
      {showOutcome && (
        <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && setShowOutcome(null)}>
          <div className="modal">
            <div className="modal-head">
              <h2>Record Specialist Consultation Outcome</h2>
              <p>Referral: {showOutcome.id} · Patient: {showOutcome.patient_name}</p>
            </div>
            <form onSubmit={async e => {
              e.preventDefault();
              await handleAction(`/api/referrals/${showOutcome.id}/outcome`, outcome);
              setShowOutcome(null);
            }} className="form-grid">
              <label className="full">
                Specialist Findings & Consultation Notes
                <textarea
                  required
                  rows={4}
                  value={outcome.outcome_notes}
                  onChange={e => setOutcome({ ...outcome, outcome_notes: e.target.value })}
                  placeholder="Document investigations, specialist evaluation, discharge plan..."
                />
              </label>
              <label className="full check-label">
                <input
                  type="checkbox"
                  checked={outcome.back_referral}
                  onChange={e => setOutcome({ ...outcome, back_referral: e.target.checked })}
                />
                <b>Establish Closed-Loop Back-Referral to Primary Health Centre (PHC)</b>
              </label>
              {outcome.back_referral && (
                <>
                  <label>
                    Follow-up Date
                    <input
                      type="date"
                      value={outcome.follow_up_date}
                      onChange={e => setOutcome({ ...outcome, follow_up_date: e.target.value })}
                    />
                  </label>
                  <label className="full">
                    Instructions for PHC Medical Officer & Frontline Health Workers
                    <textarea
                      rows={2}
                      value={outcome.follow_up_instructions}
                      onChange={e => setOutcome({ ...outcome, follow_up_instructions: e.target.value })}
                      placeholder="e.g. Weekly blood pressure tracking, ensure medication adherence..."
                    />
                  </label>
                </>
              )}
              <div className="full modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowOutcome(null)}>
                  Cancel
                </button>
                <button type="submit" className="primary-btn">
                  Save Outcome & Close Loop
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Referral Details Drawer with QR & Lifecycle Timeline */}
      {selected && (
        <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && setSelected(null)}>
          <div className="modal wide detail-modal">
            <div className="modal-head">
              <div>
                <h2>{selected.id}</h2>
                <p>Initiated on {new Date(selected.created_at).toLocaleString()}</p>
              </div>
              <div className="flex-row gap-2">
                <button className="secondary-btn small-btn" onClick={() => setShowFHIR(selected)}>
                  <Network size={14} className="text-teal" /> FHIR R4 Bundle
                </button>
                <button className="secondary-btn small-btn" onClick={() => setShowJourneySummary(selected)}>
                  <Sparkles size={14} className="text-teal" /> AI Journey Summary
                </button>
                <button className="secondary-btn small-btn" onClick={() => setShowPrintSlip(selected)}>
                  <Printer size={14} /> Referral Slip
                </button>
                <button className="icon-btn" onClick={() => setSelected(null)}><X size={18} /></button>
              </div>
            </div>

            <div className="detail-layout">
              <div className="detail-main">
                <div className="patient-card">
                  <div className="patient-avatar">
                    {selected.patient_name.split(' ').map(x => x[0]).slice(0, 2).join('')}
                  </div>
                  <div>
                    <h3>{selected.patient_name}</h3>
                    <p>{selected.age} yrs · {selected.sex} · Identifier: {selected.patient_code}</p>
                  </div>
                  <StatusBadge status={selected.status} />
                </div>

                <div className="detail-grid">
                  <InfoItem label="Origin Facility" value={selected.source_phc} />
                  <InfoItem label="Receiving Hospital" value={selected.destination} />
                  <InfoItem label="Clinical Priority" value={selected.priority} />
                  <InfoItem label="Attending Clinician" value={selected.referring_doctor_name || 'Medical Officer'} />
                  <InfoItem label="Referral Rationale" value={selected.reason} full />
                  <InfoItem label="Consultation Findings" value={selected.outcome || 'Pending hospital consultation'} full />
                  {selected.follow_up_date && (
                    <InfoItem label="Scheduled Follow-up" value={`${selected.follow_up_date} (${selected.follow_up_status || 'Assigned'})`} full />
                  )}
                </div>

                <div className="detail-actions">
                  {(user.role === 'hospital' || user.role === 'district_admin') && selected.status === 'Referred' && (
                    <button className="primary-btn" onClick={() => handleAction(`/api/referrals/${selected.id}/acknowledge`)}>
                      <Check size={16} /> Acknowledge Triage Receipt
                    </button>
                  )}
                  {(user.role === 'hospital' || user.role === 'district_admin') && selected.status !== 'Completed' && selected.status !== 'Back-Referred' && (
                    <button className="primary-btn" onClick={() => { setShowOutcome(selected); setSelected(null); }}>
                      Record Consultation Outcome
                    </button>
                  )}
                  {(user.role === 'cho' || user.role === 'phc' || user.role === 'admin') && selected.follow_up_status !== 'Completed' && selected.follow_up_date && (
                    <button className="primary-btn" onClick={() => handleAction(`/api/referrals/${selected.id}/follow-up/complete`)}>
                      <CheckCircle2 size={16} /> Complete Follow-up
                    </button>
                  )}
                </div>
              </div>

              {/* QR Panel & Timeline */}
              <div className="qr-panel">
                <div className="qr-heading">
                  <QrCode size={18} className="text-teal" />
                  <b>Optical Identification QR</b>
                </div>
                <div className="qr-box">
                  <QRCodeCanvas
                    value={selected.qr_token || JSON.stringify({ type: 'PHC_BRIDGE_REFERRAL', referralId: selected.id })}
                    size={160}
                    level="M"
                  />
                </div>
                <b className="qr-id">{selected.id}</b>
                <small className="text-muted">HMAC-signed verification token</small>

                <div className="timeline-container">
                  <b>Care Coordination Audit Events</b>
                  <div className="timeline">
                    {timeline && timeline.length ? (
                      timeline.map((e, idx) => (
                        <div key={idx} className="timeline-item">
                          <span className="timeline-marker" />
                          <div className="timeline-content">
                            <b>{e.action}</b>
                            <small>{e.actor_name} ({e.actor_role}) · {new Date(e.created_at).toLocaleTimeString()}</small>
                            {e.details && <p>{e.details}</p>}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-muted text-xs">No audit events recorded yet.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Extra Interactive Modals */}
      {showScanner && (
        <QRScannerModal
          onClose={() => setShowScanner(false)}
          onScanSuccess={handleScanSuccess}
        />
      )}

      {showAIOps && (
        <AIOperationsModal
          onClose={() => setShowAIOps(false)}
          api={api}
        />
      )}

      {showPrintSlip && (
        <PrintSlipModal
          referral={showPrintSlip}
          onClose={() => setShowPrintSlip(null)}
        />
      )}

      {showJourneySummary && (
        <JourneySummaryModal
          referral={showJourneySummary}
          api={api}
          onClose={() => setShowJourneySummary(null)}
        />
      )}

      {showFHIR && (
        <FHIRModal
          referral={showFHIR}
          api={api}
          onClose={() => setShowFHIR(null)}
        />
      )}

      {/* Toast Notification */}
      {notice && (
        <div className="toast">
          <CheckCircle2 size={16} className="text-teal" />
          <span>{notice}</span>
          <button onClick={() => setNotice('')}><X size={14} /></button>
        </div>
      )}
    </div>
  );
}

// ---------------- SUB-COMPONENTS ----------------

function Login({ onLogin, notice }) {
  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-brand">
          <div className="brand-mark"><HeartPulse size={24} /></div>
          <b>PHC Bridge</b>
        </div>
        <div className="login-message">
          <span className="eyebrow light">ANDHRA PRADESH DIGITAL HEALTHCARE</span>
          <h1>Closed-Loop Referral Intelligence.<br /><em>Zero Lost Patients.</em></h1>
          <p>
            An AI-assisted, offline-resilient healthcare coordination platform connecting Primary Health Centres,
            Community Health Centres, Area Hospitals, and District Hospitals across Andhra Pradesh.
          </p>
          <div className="login-points">
            <span><CheckCircle2 size={16} /> Transparent Facility Handoff Tracking</span>
            <span><CheckCircle2 size={16} /> HL7 FHIR R4 & ABDM Interoperability Ready</span>
            <span><CheckCircle2 size={16} /> Offline-First Progressive Web Architecture</span>
          </div>
        </div>
        <div className="login-foot">Public Healthcare Coordination Platform · Synthetic Data Evaluation</div>
      </div>

      <div className="login-right">
        <div className="login-card">
          <div className="eyebrow">HEALTHCARE WORKSPACE SIGN-IN</div>
          <h2>Select Institutional Role</h2>
          <p>Choose an authorized role to access the care coordination console:</p>

          <div className="role-list">
            {ROLES.map(r => (
              <button key={r.id} className="role-option" onClick={() => onLogin(r.id)}>
                <div className="role-icon"><r.icon size={20} /></div>
                <div><b>{r.label}</b><small>{r.desc}</small></div>
                <ArrowUpRight size={17} />
              </button>
            ))}
          </div>

          {notice && (
            <div className="banner-alert error">
              <AlertCircle size={15} />
              <span>{notice}</span>
            </div>
          )}

          <div className="demo-warning">
            <ShieldCheck size={16} />
            <span>Evaluation environment using synthetic data only. Does not diagnose or prescribe clinical treatment.</span>
          </div>
        </div>
        <div className="login-copyright">© 2026 PHC Bridge Coordination Platform · Andhra Pradesh Context</div>
      </div>
    </div>
  );
}

function Overview({ metrics, referrals, onOpen, onCreate, onScan, role }) {
  const cards = [
    { label: 'Dispatched Referrals', val: metrics.total, sub: 'Care network volume', icon: ClipboardList, tone: 'tone-0' },
    { label: 'Awaiting Triage Ack', val: metrics.pending, sub: 'Active facility handoffs', icon: Clock3, tone: 'tone-1' },
    { label: 'Acknowledged', val: metrics.acknowledged, sub: 'Hospital receipt verified', icon: CheckCircle2, tone: 'tone-2' },
    { label: 'Follow-ups Due', val: metrics.followups_due, sub: `${metrics.overdue_followups} overdue reviews`, icon: CalendarDays, tone: 'tone-3' }
  ];

  return (
    <>
      <div className="metric-grid">
        {cards.map(c => (
          <div className="metric-card" key={c.label}>
            <div className="metric-top">
              <span>{c.label}</span>
              <div className={`metric-icon ${c.tone}`}><c.icon size={18} /></div>
            </div>
            <strong>{c.val}</strong>
            <small>{c.sub}</small>
          </div>
        ))}
      </div>

      <div className="overview-grid">
        <section className="panel referrals-panel">
          <div className="panel-head">
            <div>
              <h3>Active Referral Transmissions</h3>
              <p>Primary-to-secondary and tertiary care handoffs</p>
            </div>
          </div>
          <ReferralTable rows={referrals.slice(0, 5)} compact onOpen={onOpen} role={role} />
        </section>

        <section className="panel attention-panel">
          <div className="panel-head">
            <div>
              <h3>Institutional Performance Snapshot</h3>
              <p>Network continuum-of-care indicators</p>
            </div>
            <Activity size={18} className="text-muted" />
          </div>

          <div className="snapshot-row">
            <div className="snapshot-icon blue"><ArrowUpRight size={18} /></div>
            <div>
              <b>{metrics.back_referrals} Closed-Loop Back-Referrals</b>
              <small>Patients successfully routed back to primary care</small>
            </div>
          </div>

          <div className="snapshot-row">
            <div className="snapshot-icon green"><CheckCircle2 size={18} /></div>
            <div>
              <b>{metrics.completed} Completed Outcomes</b>
              <small>{metrics.completion_rate_pct}% overall completion rate</small>
            </div>
          </div>

          <div className="snapshot-row">
            <div className="snapshot-icon amber"><Clock3 size={18} /></div>
            <div>
              <b>{metrics.avg_ack_hours}h Average Acknowledgment Latency</b>
              <small>From PHC dispatch to hospital optical scan</small>
            </div>
          </div>

          <div className="help-card">
            <div className="help-icon"><CircleHelp size={20} /></div>
            <b>Offline Resilience Across Mandals</b>
            <p>Clinicians in rural Ayushman Arogya Mandirs can generate referrals offline. Data synchronizes automatically via IndexedDB once back on the network.</p>
          </div>
        </section>
      </div>
    </>
  );
}

function ReferralTable({ rows, query, setQuery, statusFilter, setStatusFilter, priorityFilter, setPriorityFilter, onOpen, compact = false, role, onAcknowledge, onOutcome, onPrintSlip, onViewFHIR }) {
  const showControls = !compact;

  // Detailed Section Analytics
  const emergencyCount = rows.filter(r => r.priority === 'Emergency').length;
  const urgentCount = rows.filter(r => r.priority === 'Urgent').length;
  const routineCount = rows.filter(r => r.priority === 'Routine').length;
  const completedCount = rows.filter(r => r.status === 'Completed').length;
  const backReferredCount = rows.filter(r => r.status === 'Back-Referred' || r.back_referral).length;

  return (
    <div className="referral-section-wrapper">
      {showControls && (
        <div className="section-analytics-banner mb-3 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Emergency Triage</div>
            <div className="text-lg font-bold text-rose-600 mt-1">{emergencyCount} <span className="text-xs text-slate-400 font-normal">({rows.length ? Math.round((emergencyCount / rows.length) * 100) : 0}%)</span></div>
            <div className="text-[11px] text-slate-400 mt-0.5">SLA: Immediate (&lt;2h)</div>
          </div>
          <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Urgent Priority</div>
            <div className="text-lg font-bold text-amber-600 mt-1">{urgentCount} <span className="text-xs text-slate-400 font-normal">({rows.length ? Math.round((urgentCount / rows.length) * 100) : 0}%)</span></div>
            <div className="text-[11px] text-slate-400 mt-0.5">SLA: Priority (&lt;24h)</div>
          </div>
          <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Routine Referrals</div>
            <div className="text-lg font-bold text-emerald-600 mt-1">{routineCount} <span className="text-xs text-slate-400 font-normal">({rows.length ? Math.round((routineCount / rows.length) * 100) : 0}%)</span></div>
            <div className="text-[11px] text-slate-400 mt-0.5">SLA: Elective (&lt;72h)</div>
          </div>
          <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Closed-Loop Resolution</div>
            <div className="text-lg font-bold text-blue-600 mt-1">{completedCount + backReferredCount} <span className="text-xs text-slate-400 font-normal">completed</span></div>
            <div className="text-[11px] text-slate-400 mt-0.5">{backReferredCount} routed back to PHC</div>
          </div>
        </div>
      )}

      <section className={`panel table-panel ${compact ? 'compact-table' : ''}`}>
        {showControls && (
          <div className="table-toolbar">
            <div className="search-box">
              <Search size={16} />
              <input
                placeholder="Search by patient name, ID, facility, or mandal..."
                value={query || ''}
                onChange={e => setQuery?.(e.target.value)}
              />
            </div>
            <div className="filter-group">
              <select className="filter-select" value={statusFilter || 'All'} onChange={e => setStatusFilter?.(e.target.value)}>
                <option>All Statuses</option>
                <option>Referred</option>
                <option>Acknowledged</option>
                <option>In Consultation</option>
                <option>Completed</option>
                <option>Back-Referred</option>
              </select>
              <select className="filter-select" value={priorityFilter || 'All'} onChange={e => setPriorityFilter?.(e.target.value)}>
                <option>All Priorities</option>
                <option>Routine</option>
                <option>Urgent</option>
                <option>Emergency</option>
              </select>
            </div>
          </div>
        )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Patient & ID</th>
              <th>Origin Facility</th>
              <th>Destination</th>
              <th>Priority & SLA</th>
              <th>Status</th>
              <th>Dispatched</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id}>
                <td>
                  <button className="patient-link" onClick={() => onOpen(r)}>
                    <b>{r.patient_name}</b>
                    <small>{r.id} · {r.age}y/{r.sex}</small>
                  </button>
                </td>
                <td><span className="facility-cell">{r.source_phc}</span></td>
                <td><span className="facility-cell">{r.destination}</span></td>
                <td><PriorityBadge value={r.priority} /></td>
                <td><StatusBadge status={r.status} /></td>
                <td className="date-cell">{r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</td>
                <td>
                  <div className="table-action-btns">
                    {(role === 'hospital' || role === 'district_admin') && r.status === 'Referred' && onAcknowledge && (
                      <button className="secondary-btn small-btn" onClick={() => onAcknowledge(r.id)} title="Acknowledge Receipt">
                        <Check size={14} /> Ack
                      </button>
                    )}
                    {(role === 'hospital' || role === 'district_admin') && r.status !== 'Completed' && onOutcome && (
                      <button className="primary-btn small-btn" onClick={() => onOutcome(r)} title="Record Outcome">
                        Outcome
                      </button>
                    )}
                    {onViewFHIR && (
                      <button className="icon-btn" onClick={() => onViewFHIR(r)} title="Export FHIR R4 Bundle">
                        <Network size={15} />
                      </button>
                    )}
                    {onPrintSlip && (
                      <button className="icon-btn" onClick={() => onPrintSlip(r)} title="Print Referral Slip">
                        <Printer size={15} />
                      </button>
                    )}
                    <button className="icon-btn" onClick={() => onOpen(r)} title="View Detail">
                      <Eye size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan="7" className="p-8 text-center text-muted">
                  <ClipboardList size={28} className="mb-2 text-muted" />
                  <p>No referrals found matching the filter criteria.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  </div>
  );
}

function FollowUpsTable({ tasks, onRefresh, api, setNotice }) {
  async function completeTask(id) {
    try {
      await api(`/api/followups/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'Completed', completion_notes: 'Home visit completed by CHO. Health vitals and medication adherence confirmed.' })
      });
      setNotice('Follow-up task marked complete.');
      onRefresh();
    } catch (e) {
      setNotice(e.message);
    }
  }

  const completedCount = tasks.filter(t => t.status === 'Completed').length;
  const overdueCount = tasks.filter(t => t.status === 'Overdue').length;
  const pendingCount = tasks.filter(t => t.status === 'Scheduled' || t.status === 'Pending').length;
  const complianceRate = tasks.length ? Math.round((completedCount / tasks.length) * 100) : 100;

  return (
    <div className="followups-section-wrapper">
      <div className="section-analytics-banner mb-3 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">CHO Compliance Rate</div>
          <div className="text-lg font-bold text-emerald-600 mt-1">{complianceRate}%</div>
          <div className="text-[11px] text-slate-400 mt-0.5">{completedCount} of {tasks.length} tasks closed</div>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Pending Home Visits</div>
          <div className="text-lg font-bold text-amber-600 mt-1">{pendingCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Scheduled on-time visits</div>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Overdue Backlog</div>
          <div className="text-lg font-bold text-rose-600 mt-1">{overdueCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Requires supervisor escalation</div>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Frontline Field Coverage</div>
          <div className="text-lg font-bold text-blue-600 mt-1">100%</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Arogya Mandir Sub-Centres</div>
        </div>
      </div>

      <section className="panel table-panel">
        <div className="panel-head">
          <div>
            <h3>Community Health Officer (CHO) Follow-up Operations</h3>
            <p>Frontline patient visit tracking, medication compliance, and post-discharge continuity</p>
          </div>
        </div>
        <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Patient & Code</th>
              <th>Due Date</th>
              <th>Status</th>
              <th>Assigned Facility</th>
              <th>Follow-up Instructions</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(t => (
              <tr key={t.id}>
                <td>
                  <b>{t.patient_name}</b>
                  <small className="d-block text-muted">{t.patient_code}</small>
                </td>
                <td className="date-cell">
                  <b>{t.due_date}</b>
                </td>
                <td>
                  <span className={`status ${t.status === 'Completed' ? 'green' : t.status === 'Overdue' ? 'rose' : 'amber'}`}>
                    <i />{t.status}
                  </span>
                </td>
                <td>{t.facility_name}</td>
                <td><p className="task-notes-text">{t.notes || 'Routine follow-up review'}</p></td>
                <td>
                  {t.status !== 'Completed' ? (
                    <button className="primary-btn small-btn" onClick={() => completeTask(t.id)}>
                      <CheckCircle2 size={14} /> Complete
                    </button>
                  ) : (
                    <span className="text-xs text-green flex-row items-center gap-1">
                      <CheckCheck size={14} /> Completed
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {tasks.length === 0 && (
              <tr>
                <td colSpan="6" className="p-8 text-center text-muted">
                  No scheduled follow-up tasks recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  </div>
  );
}

function AnalyticsView({ metrics, api }) {
  function handleDownloadCSV() {
    window.open(`${API}/api/analytics/export`, '_blank');
  }

  return (
    <div className="analytics-page">
      <div className="flex-between items-center mb-4">
        <div>
          <h3>Care Coordination Operational Analytics</h3>
          <p className="text-muted text-sm">Aggregated from verified institutional records across Andhra Pradesh.</p>
        </div>
        <button className="secondary-btn" onClick={handleDownloadCSV}>
          <Download size={15} /> Export Referrals CSV
        </button>
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-top"><span>Completion Rate</span></div>
          <strong>{metrics.completion_rate_pct}%</strong>
          <small>Closed-loop continuity</small>
        </div>
        <div className="metric-card">
          <div className="metric-top"><span>Average Ack Latency</span></div>
          <strong>{metrics.avg_ack_hours} hrs</strong>
          <small>Dispatch to hospital triage</small>
        </div>
        <div className="metric-card">
          <div className="metric-top"><span>Back-Referrals</span></div>
          <strong>{metrics.back_referrals}</strong>
          <small>Returned to PHC level</small>
        </div>
        <div className="metric-card">
          <div className="metric-top"><span>Active Follow-ups</span></div>
          <strong>{metrics.followups_due}</strong>
          <small>{metrics.overdue_followups} overdue reviews</small>
        </div>
      </div>

      <div className="overview-grid">
        <div className="panel">
          <div className="panel-head">
            <h3>Facility Receiving Workloads</h3>
            <p>Distribution of referrals across receiving hospitals</p>
          </div>
          <div className="workload-list">
            {metrics.facility_workloads.map((w, idx) => (
              <div key={idx} className="workload-item">
                <div className="flex-between">
                  <b>{w.facility}</b>
                  <span>{w.referrals} referrals</span>
                </div>
                <div className="bar-track">
                  <i className="blue" style={{ width: `${Math.min((w.referrals / Math.max(metrics.total, 1)) * 100, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h3>Monthly Referral Volume Trends</h3>
            <p>Dispatched referrals vs completed outcomes</p>
          </div>
          <div className="trend-bars">
            {metrics.monthly_trends.map((m, idx) => (
              <div key={idx} className="trend-col">
                <div className="trend-bar-pair">
                  <div className="trend-bar-total" style={{ height: `${Math.min(m.referrals * 4, 140)}px` }} title={`Total: ${m.referrals}`} />
                  <div className="trend-bar-completed" style={{ height: `${Math.min(m.completed * 4, 140)}px` }} title={`Completed: ${m.completed}`} />
                </div>
                <small>{m.month}</small>
              </div>
            ))}
          </div>
          <div className="trend-legend">
            <span className="legend-item"><i className="bg-blue" /> Dispatched</span>
            <span className="legend-item"><i className="bg-teal" /> Completed</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AuditTimelineView({ referrals, onOpen }) {
  return (
    <section className="panel table-panel">
      <div className="panel-head">
        <div>
          <h3>System Audit Trail & Provenance</h3>
          <p>Immutable event logging across all institutional handoffs</p>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Referral ID</th>
              <th>Patient</th>
              <th>Lifecycle Status</th>
              <th>Dispatched Timestamp</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {referrals.map(r => (
              <tr key={r.id}>
                <td><b>{r.id}</b></td>
                <td>{r.patient_name}</td>
                <td><StatusBadge status={r.status} /></td>
                <td>{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</td>
                <td>
                  <button className="secondary-btn small-btn" onClick={() => onOpen(r)}>
                    View Audit Log
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function StatusBadge({ status }) {
  const c = status === 'Completed' ? 'green'
    : status === 'Back-Referred' ? 'teal'
    : status === 'Acknowledged' ? 'blue'
    : status === 'In Consultation' ? 'purple'
    : status === 'Cancelled' ? 'rose'
    : 'amber';
  return <span className={`status ${c}`}><i />{status}</span>;
}

function PriorityBadge({ value }) {
  return (
    <div className="flex-row items-center gap-1">
      <span className={`priority ${value.toLowerCase()}`}>{value}</span>
      {value === 'Emergency' && <span className="sla-pill emergency">1h SLA</span>}
      {value === 'Urgent' && <span className="sla-pill urgent">4h SLA</span>}
    </div>
  );
}

function InfoItem({ label, value, full }) {
  return (
    <div className={`info ${full ? 'full' : ''}`}>
      <small>{label}</small>
      <b>{value || '—'}</b>
    </div>
  );
}
