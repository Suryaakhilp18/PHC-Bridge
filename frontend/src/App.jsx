import React, { useEffect, useMemo, useState } from 'react';
import { QRCodeCanvas } from 'qrcode.react';
import {
  Activity, ArrowDownLeft, ArrowUpRight, Bell, Building2, CalendarDays, Check,
  CheckCircle2, ChevronDown, CircleHelp, ClipboardList, Clock3, CloudOff, FilePlus2,
  HeartPulse, LayoutDashboard, LogOut, Menu, MoreHorizontal, Plus, RefreshCw,
  Search, ShieldCheck, Users, Wifi, X, QrCode, Stethoscope, AlertCircle
} from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const roles = [
  {id:'phc', label:'PHC Doctor', desc:'Create and send referrals', icon:Stethoscope},
  {id:'hospital', label:'Hospital Doctor', desc:'Receive referrals and record outcomes', icon:Building2},
  {id:'cho', label:'Community Health Officer', desc:'Coordinate patient follow-ups', icon:Users},
  {id:'admin', label:'Administrator', desc:'Monitor the referral network', icon:ShieldCheck},
];
const emptyForm = {patient_name:'',age:'',sex:'Female',patient_code:'',phone:'',source_phc:'Lakshmi Nagar PHC',destination:'District General Hospital',reason:'',priority:'Routine'};
const localKey = 'phc-bridge-offline-queue';

function App(){
  const [user,setUser] = useState(()=>JSON.parse(localStorage.getItem('phc-user')||'null'));
  const [token,setToken] = useState(()=>localStorage.getItem('phc-token')||'');
  const [referrals,setReferrals] = useState([]);
  const [metrics,setMetrics] = useState({total:0,pending:0,acknowledged:0,completed:0,followups_due:0,back_referrals:0});
  const [page,setPage] = useState('Overview');
  const [query,setQuery] = useState('');
  const [filter,setFilter] = useState('All');
  const [selected,setSelected] = useState(null);
  const [showCreate,setShowCreate] = useState(false);
  const [showOutcome,setShowOutcome] = useState(null);
  const [form,setForm] = useState(emptyForm);
  const [outcome,setOutcome] = useState({outcome:'Consultation completed. Follow-up at PHC advised.',back_referral:true,follow_up_date:new Date(Date.now()+7*86400000).toISOString().slice(0,10),follow_up_note:'Review at PHC as advised by the hospital team.'});
  const [online,setOnline] = useState(navigator.onLine);
  const [queue,setQueue] = useState(()=>JSON.parse(localStorage.getItem(localKey)||'[]'));
  const [notice,setNotice] = useState('');
  const [mobileOpen,setMobileOpen] = useState(false);
  const [timeline,setTimeline] = useState([]);

  useEffect(()=>{const on=()=>setOnline(navigator.onLine);window.addEventListener('online',on);window.addEventListener('offline',on);return()=>{window.removeEventListener('online',on);window.removeEventListener('offline',on)}},[]);
  useEffect(()=>{localStorage.setItem(localKey,JSON.stringify(queue))},[queue]);
  useEffect(()=>{if(token) refresh()},[token]);
  useEffect(()=>{if(notice){const t=setTimeout(()=>setNotice(''),3500);return()=>clearTimeout(t)}},[notice]);

  async function api(path, options={}){
    const res=await fetch(API+path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`,...options.headers}});
    if(!res.ok){const d=await res.json().catch(()=>({}));throw new Error(d.detail||'Request failed')}
    return res.json();
  }
  async function login(role){
    try{
      const res=await fetch(API+'/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role})});
      if(!res.ok) throw new Error('Backend unavailable');
      const data=await res.json();setToken(data.token);setUser(data.user);localStorage.setItem('phc-token',data.token);localStorage.setItem('phc-user',JSON.stringify(data.user));
    }catch(e){setNotice('Start the backend first, then sign in.');}
  }
  function logout(){setUser(null);setToken('');localStorage.removeItem('phc-token');localStorage.removeItem('phc-user');}
  async function refresh(){
    try{const [r,m]=await Promise.all([api('/api/referrals'),api('/api/metrics')]);setReferrals(r);setMetrics(m)}
    catch(e){if(navigator.onLine)setNotice(e.message)}
  }
  async function createReferral(e){
    e.preventDefault();
    const payload={...form,age:String(form.age)};
    try{const r=await api('/api/referrals',{method:'POST',body:JSON.stringify(payload)});setReferrals(v=>[r,...v]);setShowCreate(false);setForm(emptyForm);setNotice('Referral created successfully.');refresh()}
    catch(err){
      if(!navigator.onLine || err.message==='Failed to fetch'){setQueue(v=>[...v,payload]);setShowCreate(false);setForm(emptyForm);setNotice('Saved on this device. Sync when online.')}
      else setNotice(err.message);
    }
  }
  async function syncQueue(){
    if(!queue.length){setNotice('Your offline queue is empty.');return}
    try{const res=await api('/api/sync',{method:'POST',body:JSON.stringify(queue)});setQueue([]);setNotice(`${res.synced} offline referral(s) synced.`);refresh()}
    catch(e){setNotice('Sync failed. Check your connection and sign-in role.')}
  }
  async function action(path,body=null){
    try{await api(path,{method:'POST',body:body?JSON.stringify(body):undefined});setNotice('Record updated.');await refresh();if(selected){const r=await api(`/api/referrals/${selected.id}/timeline`);setTimeline(r);}}
    catch(e){setNotice(e.message)}
  }
  async function openDetails(r){
    setSelected(r);
    try{setTimeline(await api(`/api/referrals/${r.id}/timeline`))}catch{setTimeline([])}
  }
  const filtered=useMemo(()=>referrals.filter(r=>{
    const matches=[r.patient_name,r.id,r.patient_code,r.destination].join(' ').toLowerCase().includes(query.toLowerCase());
    return matches&&(filter==='All'||r.status===filter);
  }),[referrals,query,filter]);
  const nav=[['Overview',LayoutDashboard],['Referrals',ClipboardList],['Follow-ups',CalendarDays],['Patients',Users]];
  if(!user) return <Login onLogin={login} notice={notice}/>;
  const roleName=roles.find(r=>r.id===user.role)?.label||user.role;
  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen?'open':''}`}>
      <div className="brand"><div className="brand-mark"><HeartPulse size={22}/></div><div><b>PHC Bridge</b><small>CARE COORDINATION</small></div><button className="icon-btn mobile-close" onClick={()=>setMobileOpen(false)}><X/></button></div>
      <div className="facility"><span className="facility-dot"/><div><b>{user.facility}</b><small>Healthcare network</small></div><ChevronDown size={15}/></div>
      <div className="nav-label">WORKSPACE</div>
      {nav.map(([n,I])=><button key={n} className={`nav-item ${page===n?'active':''}`} onClick={()=>{setPage(n);setMobileOpen(false)}}><I size={18}/>{n}{n==='Referrals'&&<span className="nav-count">{referrals.length}</span>}</button>)}
      <div className="nav-label section-gap">MANAGEMENT</div>
      <button className={`nav-item ${page==='Analytics'?'active':''}`} onClick={()=>setPage('Analytics')}><Activity size={18}/>Analytics</button>
      <button className={`nav-item ${page==='Audit log'?'active':''}`} onClick={()=>setPage('Audit log')}><ShieldCheck size={18}/>Audit timeline</button>
      <div className="sidebar-bottom">
        <div className={`connection ${online?'online':'offline'}`}><span/>{online?<><Wifi size={15}/> Online</>:<><CloudOff size={15}/> Offline mode</>}<small>{queue.length} queued</small></div>
        <button className="sync-button" onClick={syncQueue}><RefreshCw size={15}/> Sync offline queue {queue.length>0&&<b>{queue.length}</b>}</button>
        <div className="profile"><div className="avatar">{user.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</div><div className="profile-text"><b>{user.name}</b><small>{roleName}</small></div><button className="icon-btn" onClick={logout} title="Sign out"><LogOut size={17}/></button></div>
      </div>
    </aside>
    <main className="main">
      <header className="topbar"><button className="icon-btn menu-toggle" onClick={()=>setMobileOpen(true)}><Menu/></button><div className="crumb">Workspace <span>/</span> <b>{page}</b></div><div className="top-actions"><div className={`top-status ${online?'':'is-offline'}`}><i/>{online?'System operational':'Offline mode'}</div><button className="icon-btn notification" onClick={()=>setNotice(`${metrics.followups_due} follow-up(s) due today.`)}><Bell size={19}/>{metrics.followups_due>0&&<i/>}</button><div className="top-avatar">{user.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</div></div></header>
      <div className="content">
        <div className="welcome-row"><div><div className="eyebrow">TUESDAY, NOVEMBER 24, 2026</div><h1>{page==='Overview'?'Good morning':page}</h1><p>{page==='Overview'?'Here is what is happening across your referral network today.':page==='Follow-ups'?'Track assigned patient follow-ups and close the loop.':`Manage ${page.toLowerCase()} across your healthcare network.`}</p></div>{(user.role==='phc'||user.role==='admin')&&<button className="primary-btn" onClick={()=>setShowCreate(true)}><Plus size={17}/> New referral</button>}</div>
        {page==='Overview'&&<Overview metrics={metrics} referrals={referrals} onOpen={openDetails} onCreate={()=>setShowCreate(true)} role={user.role}/>}
        {(page==='Referrals'||page==='Patients'||page==='Follow-ups'||page==='Audit log')&&<ReferralTable rows={page==='Follow-ups'?referrals.filter(r=>r.follow_up_date):page==='Audit log'?referrals:filtered} query={query} setQuery={setQuery} filter={filter} setFilter={setFilter} onOpen={openDetails} page={page} role={user.role} onAcknowledge={id=>action(`/api/referrals/${id}/acknowledge`)} onOutcome={setShowOutcome}/>}
        {page==='Analytics'&&<Analytics metrics={metrics} referrals={referrals}/>}
        <footer className="footer"><span>PHC Bridge <b>•</b> Referral coordination platform</span><span><ShieldCheck size={13}/> Synthetic demo data · Not for clinical use</span></footer>
      </div>
    </main>
    {showCreate&&<Modal title="Create patient referral" subtitle="Enter synthetic patient and referral details." onClose={()=>setShowCreate(false)}><form className="form-grid" onSubmit={createReferral}>
      <label className="full">Patient full name<input required minLength="2" value={form.patient_name} onChange={e=>setForm({...form,patient_name:e.target.value})} placeholder="e.g. Ananya Devi"/></label>
      <label>Age<input required type="number" min="0" max="120" value={form.age} onChange={e=>setForm({...form,age:e.target.value})} placeholder="Age"/></label>
      <label>Sex<select value={form.sex} onChange={e=>setForm({...form,sex:e.target.value})}><option>Female</option><option>Male</option><option>Other</option><option>Prefer not to say</option></select></label>
      <label>Patient code<input required value={form.patient_code} onChange={e=>setForm({...form,patient_code:e.target.value})} placeholder="SYN-1004"/></label>
      <label>Contact (optional)<input value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} placeholder="Demo contact only"/></label>
      <label>Referring PHC<input required value={form.source_phc} onChange={e=>setForm({...form,source_phc:e.target.value})}/></label>
      <label>Receiving facility<input required value={form.destination} onChange={e=>setForm({...form,destination:e.target.value})}/></label>
      <label className="full">Referral reason<textarea required minLength="3" rows="3" value={form.reason} onChange={e=>setForm({...form,reason:e.target.value})} placeholder="Enter referral reason (no diagnosis required)"/></label>
      <label>Priority<select value={form.priority} onChange={e=>setForm({...form,priority:e.target.value})}><option>Routine</option><option>Urgent</option><option>Emergency</option></select></label>
      <div className="full form-note"><ShieldCheck size={15}/> Use synthetic information only. Clinical decisions remain with qualified healthcare professionals.</div>
      <div className="full modal-actions"><button type="button" className="secondary-btn" onClick={()=>setShowCreate(false)}>Cancel</button><button className="primary-btn"><FilePlus2 size={16}/> Create referral</button></div>
    </form></Modal>}
    {showOutcome&&<Modal title="Record consultation outcome" subtitle={`Referral ${showOutcome.id} · ${showOutcome.patient_name}`} onClose={()=>setShowOutcome(null)}><form className="form-grid" onSubmit={async e=>{e.preventDefault();await action(`/api/referrals/${showOutcome.id}/outcome`,{...outcome,follow_up_date:outcome.follow_up_date||null});setShowOutcome(null)}}><label className="full">Consultation outcome<textarea rows="4" required value={outcome.outcome} onChange={e=>setOutcome({...outcome,outcome:e.target.value})}/></label><label className="full check-label"><input type="checkbox" checked={outcome.back_referral} onChange={e=>setOutcome({...outcome,back_referral:e.target.checked})}/> Create back-referral to PHC</label><label>Follow-up date<input type="date" value={outcome.follow_up_date} onChange={e=>setOutcome({...outcome,follow_up_date:e.target.value})}/></label><label className="full">Follow-up instruction<textarea rows="2" value={outcome.follow_up_note} onChange={e=>setOutcome({...outcome,follow_up_note:e.target.value})}/></label><div className="full modal-actions"><button type="button" className="secondary-btn" onClick={()=>setShowOutcome(null)}>Cancel</button><button className="primary-btn">Save outcome</button></div></form></Modal>}
    {selected&&<Modal title="Referral details" subtitle={`${selected.id} · Created ${new Date(selected.created_at).toLocaleString()}`} onClose={()=>setSelected(null)} wide><div className="detail-layout"><div><div className="patient-card"><div className="patient-avatar">{selected.patient_name.split(' ').map(x=>x[0]).slice(0,2).join('')}</div><div><h3>{selected.patient_name}</h3><p>{selected.age} years · {selected.sex} · {selected.patient_code}</p></div><Status status={selected.status}/></div><div className="detail-grid"><Info label="Referring facility" value={selected.source_phc}/><Info label="Receiving facility" value={selected.destination}/><Info label="Priority" value={selected.priority}/><Info label="Referral status" value={selected.status}/><Info label="Referral reason" value={selected.reason} full/><Info label="Consultation outcome" value={selected.outcome||'Awaiting hospital update'} full/><Info label="Follow-up" value={selected.follow_up_date?`${selected.follow_up_date} · ${selected.follow_up_status}`:'Not scheduled'} full/></div><div className="detail-actions">
      {user.role==='hospital'&&selected.status==='Referred'&&<button className="primary-btn" onClick={()=>action(`/api/referrals/${selected.id}/acknowledge`)}> <Check size={16}/> Acknowledge receipt</button>}
      {user.role==='hospital'&&selected.status!=='Completed'&&<button className="primary-btn" onClick={()=>{setShowOutcome(selected);setSelected(null)}}>Record outcome</button>}
      {(user.role==='cho'||user.role==='phc'||user.role==='admin')&&selected.follow_up_status!=='Completed'&&selected.follow_up_date&&<button className="primary-btn" onClick={()=>action(`/api/referrals/${selected.id}/follow-up/complete`)}> <CheckCircle2 size={16}/> Complete follow-up</button>}
      <button className="secondary-btn" onClick={()=>window.print()}>Print summary</button>
      </div></div><div className="qr-panel"><div className="qr-heading"><QrCode size={18}/><b>Referral QR</b></div><div className="qr-box"><QRCodeCanvas value={JSON.stringify({type:'PHC_BRIDGE_REFERRAL',referralId:selected.id})} size={164} level="M"/></div><b className="qr-id">{selected.id}</b><small>Scan to identify this referral</small><div className="timeline"><b>Activity timeline</b>{timeline.length?timeline.map((t,i)=><div className="timeline-item" key={i}><i/><div><b>{t.action}</b><small>{t.actor} · {new Date(t.created_at).toLocaleString()}</small>{t.details&&<p>{t.details}</p>}</div></div>):<p className="muted">No events loaded.</p>}</div></div></div></Modal>}
    {notice&&<div className="toast"><CheckCircle2 size={17}/>{notice}<button onClick={()=>setNotice('')}><X size={15}/></button></div>}
  </div>
}

function Login({onLogin,notice}){
  return <div className="login-page"><div className="login-left"><div className="login-brand"><div className="brand-mark"><HeartPulse size={23}/></div><b>PHC Bridge</b></div><div className="login-message"><span className="eyebrow light">CONTINUITY OF CARE, CONNECTED</span><h1>Every referral.<br/><em>One connected journey.</em></h1><p>A smarter coordination layer connecting primary healthcare centres and district hospitals — from referral to follow-up.</p><div className="login-points"><span><CheckCircle2/> Accountable handoffs</span><span><CheckCircle2/> Visible referral progress</span><span><CheckCircle2/> Follow-up coordination</span></div></div><div className="login-foot">PHC Bridge · HealthTech prototype</div></div><div className="login-right"><div className="login-card"><div className="eyebrow">WELCOME TO PHC BRIDGE</div><h2>Sign in to your workspace</h2><p>Select a demo role to explore the platform. No password required.</p><div className="role-list">{roles.map(r=><button key={r.id} className="role-option" onClick={()=>onLogin(r.id)}><div className="role-icon"><r.icon size={20}/></div><div><b>{r.label}</b><small>{r.desc}</small></div><ArrowUpRight size={17}/></button>)}</div>{notice&&<div className="login-error"><AlertCircle size={16}/>{notice}</div>}<div className="demo-warning"><ShieldCheck size={16}/><span>Demo environment only. Use synthetic patient data. No real clinical information.</span></div></div><div className="login-copyright">© 2026 PHC Bridge · Prototype</div></div></div>
}
function Overview({metrics,referrals,onOpen,onCreate,role}){
  const cards=[['Total referrals',metrics.total,'All recorded referrals',ClipboardList],['Awaiting acknowledgement',metrics.pending,'Sent to receiving facility',Clock3],['Acknowledged',metrics.acknowledged,'Received by hospital',CheckCircle2],['Follow-ups due',metrics.followups_due,'Require attention',CalendarDays]];
  return <><div className="metric-grid">{cards.map(([label,value,sub,I],i)=><div className="metric-card" key={label}><div className="metric-top"><span>{label}</span><div className={`metric-icon tone-${i}`}><I size={18}/></div></div><strong>{value}</strong><small>{sub}</small></div>)}</div><div className="overview-grid"><section className="panel referrals-panel"><div className="panel-head"><div><h3>Recent referrals</h3><p>Latest patient handoffs across the network</p></div><button className="text-button" onClick={()=>document.querySelector('.nav-item:nth-child(2)')?.click()}>View all <ArrowUpRight size={14}/></button></div><ReferralTable rows={referrals.slice(0,5)} compact onOpen={onOpen} role={role}/></section><section className="panel attention-panel"><div className="panel-head"><div><h3>Continuity snapshot</h3><p>Referral lifecycle overview</p></div><Activity size={18} className="muted"/></div><div className="snapshot-row"><div className="snapshot-icon blue"><ArrowUpRight/></div><div><b>{metrics.back_referrals} back-referrals</b><small>Returned to PHC for continued care</small></div></div><div className="snapshot-row"><div className="snapshot-icon green"><CheckCircle2/></div><div><b>{metrics.completed} completed referrals</b><small>Consultation outcome recorded</small></div></div><div className="snapshot-row"><div className="snapshot-icon amber"><Clock3/></div><div><b>{metrics.pending} pending handoffs</b><small>Awaiting receiving-facility acknowledgement</small></div></div><div className="help-card"><div className="help-icon"><CircleHelp/></div><b>Keep the care journey connected</b><p>Close every referral loop by recording hospital outcomes and assigning follow-up tasks.</p><button onClick={onCreate}>Create a referral <ArrowUpRight size={14}/></button></div></section></div><div className="bottom-note"><ShieldCheck size={16}/><span><b>Designed for accountable coordination.</b> PHC Bridge supports referral visibility and follow-up tracking. Clinical decisions remain with qualified healthcare professionals.</span></div></>
}
function ReferralTable({rows,query,setQuery,filter,setFilter,onOpen,compact=false,page,role,onAcknowledge,onOutcome}){
  const showFilters=!compact;
  return <section className={`panel table-panel ${compact?'compact-table':''}`}><div className="table-toolbar">{showFilters&&<><div className="search-box"><Search size={16}/><input placeholder="Search patient, referral ID..." value={query||''} onChange={e=>setQuery?.(e.target.value)}/></div><select className="filter-select" value={filter||'All'} onChange={e=>setFilter?.(e.target.value)}><option>All</option><option>Referred</option><option>Acknowledged</option><option>Completed</option></select></>}</div><div className="table-wrap"><table><thead><tr><th>Patient / Referral ID</th><th>Facility</th><th>Priority</th><th>Status</th><th>Created</th><th></th></tr></thead><tbody>{rows.map(r=><tr key={r.id}><td><button className="patient-link" onClick={()=>onOpen(r)}><b>{r.patient_name}</b><small>{r.id}</small></button></td><td><span className="facility-cell">{r.destination}</span></td><td><Priority value={r.priority}/></td><td><Status status={r.status}/></td><td className="date-cell">{r.created_at?new Date(r.created_at).toLocaleDateString():'—'}</td><td><button className="row-more" onClick={()=>onOpen(r)}><MoreHorizontal size={18}/></button></td></tr>)}</tbody></table>{rows.length===0&&<div className="empty-state"><ClipboardList size={25}/><b>No referrals found</b><span>Try changing your search or filter.</span></div>}</div></section>
}
function Analytics({metrics,referrals}){
  const total=Math.max(metrics.total,1), pct=n=>Math.round(n/total*100);
  return <><div className="metric-grid">{[['Total referrals',metrics.total],['Back-referrals',metrics.back_referrals],['Completed',metrics.completed],['Follow-ups due',metrics.followups_due]].map(([a,b],i)=><div className="metric-card" key={a}><div className="metric-top"><span>{a}</span></div><strong>{b}</strong><small>Network performance</small></div>)}</div><div className="panel analytics-panel"><div className="panel-head"><div><h3>Referral status distribution</h3><p>Current status of all recorded referrals</p></div></div>{[['Referred',metrics.pending,'blue'],['Acknowledged',metrics.acknowledged,'amber'],['Completed',metrics.completed,'green']].map(([n,v,c])=><div className="bar-row" key={n}><div><b>{n}</b><span>{v} · {pct(v)}%</span></div><div className="bar-track"><i className={c} style={{width:`${pct(v)}%`}}/></div></div>)}</div><div className="bottom-note"><ShieldCheck size={16}/><span>Analytics are based on synthetic prototype records and should not be used for operational or clinical reporting.</span></div></>
}
function Status({status}){const c=status==='Completed'?'green':status==='Acknowledged'?'blue':'amber';return <span className={`status ${c}`}><i/>{status}</span>}
function Priority({value}){return <span className={`priority ${value.toLowerCase()}`}>{value}</span>}
function Info({label,value,full}){return <div className={`info ${full?'full':''}`}><small>{label}</small><b>{value||'—'}</b></div>}
function Modal({title,subtitle,onClose,children,wide}){return <div className="modal-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><div className={`modal ${wide?'wide':''}`}><div className="modal-head"><div><h2>{title}</h2><p>{subtitle}</p></div><button className="icon-btn" onClick={onClose}><X/></button></div>{children}</div></div>}
export default App;
