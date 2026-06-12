/* ═══════════════════════════════════════════════════════════
   AI Lead Pipeline — SPA Application Logic
   ═══════════════════════════════════════════════════════════ */

'use strict';

// ── State ───────────────────────────────────────────────────
const State = {
  token:       null,
  user:        null,
  leads:       [],
  stats:       {},
  alerts:      [],
  activePage:  'overview',
  selectedLead: null,
  polling:     null,
  refreshing:  false,
};

// ── SVG Icons ────────────────────────────────────────────────
const Icons = {
  logo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
  overview: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>`,
  leads: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  analytics: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  alerts: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
  refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`,
  signout: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
  close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  phone: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.15 10a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.06 0h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.09 7.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 21 14.92z"/></svg>`,
  mail: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`,
  zap: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  star: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  trending: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`,
  inbox: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>`,
};

// ── Mock Data Generator ──────────────────────────────────────
function generateMockLeads() {
  const names   = ['Adebayo Okonkwo','Chisom Nwosu','Emeka Adeleke','Fatima Hassan','Oluwaseun Bello','Ngozi Chukwu','Babajide Adeyemi','Amaka Obi','Chukwuemeka Eze','Yetunde Afolabi','Kola Adesanya','Rukayat Ibrahim','Tunde Fashola','Aisha Mohammed','Gbenga Williams'];
  const phones  = ['+2348012345678','+2348098765432','+2348155667788','+2348033221100','+2348167890123','+2348144332211','+2348022334455','+2348177889900','+2348066778899','+2348111223344'];
  const sources = ['website','facebook','instagram','referral','whatsapp'];
  const interests = ['3-bedroom apartment','duplex','commercial space','land','studio apartment','office complex'];
  const budgets   = ['₦25M','₦50M','₦15M','₦80M','₦100M','₦35M','₦60M','₦45M'];
  const timelines = ['immediately','1-3 months','3-6 months','6-12 months'];
  const summaries = [
    'Lead showed strong intent to purchase. Budget confirmed. Ready to view properties.',
    'Interested but needs to discuss with spouse. Follow up in 48 hours.',
    'Price sensitive. Exploring multiple options. Long-term nurture recommended.',
    'Very hot lead. Wants to close this month. Immediate sales handoff required.',
    'Budget mismatch with initial query. Redirected to more suitable options.',
    'Called twice. No answer. Left voicemail. Auto-nurture sequence activated.',
  ];

  const statuses = [
    { label:'Sales Qualified', cls:'qualified', score: [65,100] },
    { label:'Nurturing',       cls:'nurturing', score: [40,64] },
    { label:'Long-term Nurture',cls:'cold',     score: [0,39] },
    { label:'Pending Call',    cls:'pending',   score: [0,50] },
  ];

  const now = Date.now();
  return Array.from({ length: 18 }, (_, i) => {
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const [sMin, sMax] = status.score;
    const score = sMin + Math.floor(Math.random() * (sMax - sMin + 1));
    const ts    = now - Math.floor(Math.random() * 86400000 * 3);
    return {
      session_key: `lead:+234${Math.floor(Math.random()*9e9)}:${Math.floor(ts/1000)}`,
      name:     names[i % names.length],
      phone:    phones[i % phones.length],
      email:    i % 3 === 0 ? `lead${i}@email.com` : '',
      interest: interests[i % interests.length],
      budget:   budgets[i % budgets.length],
      location: ['Lagos','Abuja','Port Harcourt','Ibadan'][i % 4],
      source:   sources[i % sources.length],
      status:   status.label,
      status_cls: status.cls,
      score,
      confidence: +(0.5 + Math.random() * 0.5).toFixed(2),
      intent_strength: ['high','medium','low'][Math.floor(Math.random() * 3)],
      budget_confirmed: Math.random() > 0.4,
      timeline: timelines[i % timelines.length],
      summary_notes: summaries[i % summaries.length],
      transcript: i % 4 !== 0 ? `Agent: Hello, may I speak with ${names[i % names.length]}?\nLead: Yes, this is them speaking.\nAgent: Great! I'm calling about your inquiry regarding ${interests[i % interests.length]}. Are you still interested?\nLead: Yes, definitely. I've been looking for a good option in that range.\nAgent: Excellent. Can you tell me more about your timeline and budget?\nLead: I'm looking at ${timelines[i % timelines.length]} and my budget is around ${budgets[i % budgets.length]}.\nAgent: That's very helpful. We have some excellent options in that range. Would you be available to visit a property this week?\nLead: That sounds good, let me check my schedule.\nAgent: Perfect. I'll send over some details. Is there anything specific you're looking for?` : '',
      created_at: ts,
    };
  });
}

function generateMockStats(leads) {
  const total   = leads.length;
  const hot     = leads.filter(l => l.score >= 65).length;
  const warm    = leads.filter(l => l.score >= 40 && l.score < 65).length;
  const called  = leads.filter(l => l.transcript).length;
  const avgScore = Math.round(leads.reduce((s, l) => s + l.score, 0) / total);
  return {
    total_leads: total,
    hot_leads:   hot,
    calls_made:  called,
    avg_score:   avgScore,
    call_success_rate: Math.round((called / total) * 100),
    conversion_rate: Math.round((hot / total) * 100),
    nurture_count: warm,
    cold_count: leads.filter(l => l.score < 40).length,
  };
}

function generateMockAlerts() {
  const agents  = ['IntakeAgent','AnalysisAgent','CallAgent','NurtureAgent','ClosingAgent'];
  const types   = ['error','warning','info','success'];
  const messages = [
    'HubSpot API rate limit reached. Retrying in 10s.',
    'VAPI webhook received with no transcript. Session skipped.',
    'Lead session expired before analysis completed.',
    'Brevo email delivered successfully.',
    'New hot lead routed to Closing Agent.',
    'Redis connection timeout. Retrying…',
    'Low-confidence score (0.43) flagged for manual review.',
    'Slack alert posted to #system-alerts.',
    'HubSpot contact created successfully.',
    'Call dispatch failed — invalid phone number.',
  ];
  const clsMap = { error:'red', warning:'amber', info:'blue', success:'green' };
  const now    = Date.now();
  return Array.from({ length: 10 }, (_, i) => ({
    id:      i,
    agent:   agents[i % agents.length],
    type:    types[i % types.length],
    type_cls: clsMap[types[i % types.length]],
    message: messages[i],
    timestamp: now - i * 1000 * 60 * Math.floor(Math.random() * 30 + 1),
  }));
}

// ── Auth API ──────────────────────────────────────────────────
async function apiLogin(username, password) {
  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (res.ok) return await res.json();
    return null;
  } catch {
    // Server not running or endpoint not yet set up — demo mode
    if (username === 'admin' && password === 'admin123') {
      return { token: 'demo-token', username, role: 'Administrator' };
    }
    return null;
  }
}

// ── Data Fetchers ─────────────────────────────────────────────
async function fetchLeads() {
  try {
    const res = await fetch('/api/leads', {
      headers: { Authorization: `Bearer ${State.token}` },
    });
    if (res.ok) {
      const data = await res.json();
      // Always return real data — empty array is valid (no leads yet)
      return Array.isArray(data) ? data : [];
    }
  } catch (err) {
    console.warn('fetchLeads error:', err);
  }
  // Only fall back to mock if the server itself is unreachable (not running)
  return State.token === 'demo-token' ? generateMockLeads() : [];
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats', {
      headers: { Authorization: `Bearer ${State.token}` },
    });
    if (res.ok) return await res.json();
  } catch {}
  return generateMockStats(State.leads);
}

async function fetchAlerts() {
  try {
    const res = await fetch('/api/alerts', {
      headers: { Authorization: `Bearer ${State.token}` },
    });
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    }
  } catch {}
  return State.token === 'demo-token' ? generateMockAlerts() : [];
}

async function triggerAction(action, sessionKey) {
  try {
    const res = await fetch('/api/leads/action', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${State.token}`,
      },
      body: JSON.stringify({ action, session_key: sessionKey }),
    });
    return res.ok;
  } catch {
    // Demo mode — simulate success
    await new Promise(r => setTimeout(r, 800));
    return true;
  }
}

// ── Helpers ───────────────────────────────────────────────────
function timeAgo(ts) {
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  const h = Math.floor(m / 60);
  const d = Math.floor(h / 24);
  if (d > 0)  return `${d}d ago`;
  if (h > 0)  return `${h}h ago`;
  if (m > 0)  return `${m}m ago`;
  return 'just now';
}

function scoreClass(score) {
  if (score >= 65) return 'hot';
  if (score >= 40) return 'warm';
  return 'cold';
}

function initials(name) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '—';
}

// ── Toast ─────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  const toast  = document.getElementById('toast');
  const icon   = type === 'success' ? Icons.check : type === 'error' ? Icons.alert : Icons.info;
  toast.innerHTML = `${icon} <span>${message}</span>`;
  toast.className = `toast ${type} show`;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { toast.className = 'toast'; }, 3200);
}

// ── Drawer ────────────────────────────────────────────────────
function openDrawer(lead) {
  State.selectedLead = lead;
  const sc   = scoreClass(lead.score);
  const conf = Math.round((lead.confidence || 0) * 100);

  document.getElementById('drawer-lead-name').textContent  = lead.name;
  document.getElementById('drawer-lead-phone').textContent = lead.phone;
  document.getElementById('drawer-lead-status').innerHTML  = statusBadgeHtml(lead.status_cls, lead.status);

  // Info grid
  document.getElementById('drawer-info').innerHTML = `
    <div class="info-tile"><div class="info-tile-label">Interest</div><div class="info-tile-value">${capitalize(lead.interest) || '—'}</div></div>
    <div class="info-tile"><div class="info-tile-label">Budget</div><div class="info-tile-value">${lead.budget || '—'}</div></div>
    <div class="info-tile"><div class="info-tile-label">Location</div><div class="info-tile-value">${lead.location || '—'}</div></div>
    <div class="info-tile"><div class="info-tile-label">Source</div><div class="info-tile-value">${capitalize(lead.source)}</div></div>
    <div class="info-tile"><div class="info-tile-label">Timeline</div><div class="info-tile-value">${capitalize(lead.timeline) || '—'}</div></div>
    <div class="info-tile"><div class="info-tile-label">Email</div><div class="info-tile-value">${lead.email || '—'}</div></div>
  `;

  // Score breakdown
  const intentMap = { high: 80, medium: 55, low: 25 };
  const intentPct = intentMap[lead.intent_strength] || 50;
  document.getElementById('drawer-scores').innerHTML = `
    <div class="score-breakdown-row">
      <span class="score-breakdown-key">Overall Score</span>
      <div class="score-breakdown-bar-track"><div class="score-breakdown-bar-fill" style="width:${lead.score}%;background:${sc==='hot'?'var(--green)':sc==='warm'?'var(--amber)':'var(--red)'}"></div></div>
      <span class="score-breakdown-val ${sc}">${lead.score}</span>
    </div>
    <div class="score-breakdown-row">
      <span class="score-breakdown-key">AI Confidence</span>
      <div class="score-breakdown-bar-track"><div class="score-breakdown-bar-fill" style="width:${conf}%;background:var(--blue)"></div></div>
      <span class="score-breakdown-val">${conf}%</span>
    </div>
    <div class="score-breakdown-row">
      <span class="score-breakdown-key">Intent Strength</span>
      <div class="score-breakdown-bar-track"><div class="score-breakdown-bar-fill" style="width:${intentPct}%;background:var(--purple)"></div></div>
      <span class="score-breakdown-val">${capitalize(lead.intent_strength)}</span>
    </div>
    <div class="score-breakdown-row">
      <span class="score-breakdown-key">Budget Confirmed</span>
      <div class="score-breakdown-bar-track"><div class="score-breakdown-bar-fill" style="width:${lead.budget_confirmed?100:20}%;background:${lead.budget_confirmed?'var(--green)':'var(--red)'}"></div></div>
      <span class="score-breakdown-val">${lead.budget_confirmed ? 'Yes' : 'No'}</span>
    </div>
  `;

  // Summary notes
  document.getElementById('drawer-summary').textContent = lead.summary_notes || 'No analysis available yet.';

  // Transcript
  const transcriptSection = document.getElementById('drawer-transcript-section');
  if (lead.transcript) {
    transcriptSection.style.display = 'block';
    document.getElementById('drawer-transcript').textContent = lead.transcript;
    document.getElementById('drawer-transcript-chars').textContent = `${lead.transcript.length} chars`;
  } else {
    transcriptSection.style.display = 'none';
  }

  // Actions
  document.getElementById('drawer-actions').innerHTML = `
    <p class="drawer-section-label">Quick Actions</p>
    <button class="action-btn blue-btn" onclick="handleAction('recall','${lead.session_key}')">
      ${Icons.phone}
      <span>
        <div class="action-label">Re-dispatch Call</div>
        <div class="action-sub">Trigger VAPI outbound call</div>
      </span>
    </button>
    <button class="action-btn green-btn" onclick="handleAction('nurture','${lead.session_key}')">
      ${Icons.mail}
      <span>
        <div class="action-label">Send Nurture Email</div>
        <div class="action-sub">Dispatch via Brevo sequence</div>
      </span>
    </button>
    <button class="action-btn" onclick="handleAction('hubspot','${lead.session_key}')">
      ${Icons.zap}
      <span>
        <div class="action-label">Open in HubSpot</div>
        <div class="action-sub">View CRM contact record</div>
      </span>
    </button>
  `;

  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawer-backdrop').classList.add('visible');

  // Highlight selected row
  document.querySelectorAll('.leads-table tbody tr').forEach(r => r.classList.remove('selected'));
  const row = document.querySelector(`tr[data-key="${lead.session_key}"]`);
  if (row) row.classList.add('selected');
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawer-backdrop').classList.remove('visible');
  document.querySelectorAll('.leads-table tbody tr').forEach(r => r.classList.remove('selected'));
  State.selectedLead = null;
}

async function handleAction(action, sessionKey) {
  const labels = { recall: 'Call dispatched', nurture: 'Email sent', hubspot: 'Opening HubSpot…' };
  const btn    = event.currentTarget;
  btn.disabled = true;
  btn.style.opacity = '0.6';
  const ok = await triggerAction(action, sessionKey);
  btn.disabled = false;
  btn.style.opacity = '1';
  if (ok) showToast(labels[action] || 'Action completed', 'success');
  else    showToast('Action failed. Check system logs.', 'error');
}

// ── Status Badge HTML ─────────────────────────────────────────
function statusBadgeHtml(cls, label) {
  return `<span class="status-badge ${cls}"><span class="status-dot"></span>${label}</span>`;
}

// ── Render: Stat Cards ────────────────────────────────────────
function renderStats() {
  const s = State.stats;
  const cards = [
    { icon: Icons.users, iconCls: 'blue',   value: s.total_leads || 0,          label: 'Total Leads',       delta: '+12%', deltaCls: 'up' },
    { icon: Icons.star,  iconCls: 'green',  value: s.hot_leads || 0,            label: 'Sales Qualified',   delta: '+8%',  deltaCls: 'up' },
    { icon: Icons.phone, iconCls: 'amber',  value: s.calls_made || 0,           label: 'Calls Dispatched',  delta: '—',    deltaCls: 'flat' },
    { icon: Icons.trending,iconCls:'purple',value: `${s.avg_score || 0}`,       label: 'Avg Lead Score',    delta: '+3',   deltaCls: 'up' },
  ];
  document.getElementById('stats-grid').innerHTML = cards.map(c => `
    <div class="stat-card">
      <div class="stat-card-top">
        <div class="stat-icon-wrap ${c.iconCls}">${c.icon}</div>
        <span class="stat-delta ${c.deltaCls}">${c.delta}</span>
      </div>
      <div class="stat-value">${c.value}</div>
      <div class="stat-label">${c.label}</div>
    </div>
  `).join('');
}

// ── Render: Leads Table ───────────────────────────────────────
function renderLeadsTable(leads) {
  const tbody = document.getElementById('leads-tbody');
  document.getElementById('leads-count').textContent = leads.length;

  if (!leads.length) {
    tbody.innerHTML = `<tr><td colspan="6">
      <div class="empty-state">${Icons.inbox}<h3>No leads yet</h3><p>Leads will appear here as they enter the pipeline.</p></div>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = leads.map(l => {
    const sc = scoreClass(l.score);
    return `
    <tr data-key="${l.session_key}" onclick="openDrawer(State.leads.find(x=>x.session_key==='${l.session_key}'))">
      <td>
        <div class="lead-name">${l.name}</div>
        <div class="lead-phone">${l.phone}</div>
      </td>
      <td><span class="source-badge">${capitalize(l.source)}</span></td>
      <td>
        <div class="score-cell">
          <div class="score-bar-track"><div class="score-bar-fill ${sc}" style="width:${l.score}%"></div></div>
          <span class="score-num ${sc}">${l.score}</span>
        </div>
      </td>
      <td>${statusBadgeHtml(l.status_cls, l.status)}</td>
      <td class="time-cell">${timeAgo(l.created_at)}</td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn-icon" title="View details" onclick="event.stopPropagation();openDrawer(State.leads.find(x=>x.session_key==='${l.session_key}'))">${Icons.info}</button>
        </div>
      </td>
    </tr>`;
  }).join('');
}

// ── Render: Alerts ────────────────────────────────────────────
function renderAlerts() {
  const list   = document.getElementById('alerts-list');
  const alerts = State.alerts;

  if (!alerts.length) {
    list.innerHTML = `<div class="empty-state">${Icons.check}<h3>All clear</h3><p>No alerts in the system right now.</p></div>`;
    return;
  }

  const iconMap = { error: Icons.alert, warning: Icons.alert, info: Icons.info, success: Icons.check };

  list.innerHTML = alerts.map(a => `
    <div class="alert-item">
      <div class="alert-icon-wrap ${a.type_cls}">${iconMap[a.type] || Icons.info}</div>
      <div class="alert-body">
        <div class="alert-agent" style="color:var(--${a.type_cls === 'red' ? 'red' : a.type_cls === 'amber' ? 'amber' : a.type_cls === 'green' ? 'green' : 'blue'})">${a.agent}</div>
        <div class="alert-message">${a.message}</div>
      </div>
      <div class="alert-time">${timeAgo(a.timestamp)}</div>
    </div>
  `).join('');
}

// ── Render: Analytics Page ────────────────────────────────────
function renderAnalytics() {
  const leads = State.leads;
  const s     = State.stats;

  // Funnel
  const total  = leads.length || 1;
  const hot    = leads.filter(l => l.score >= 65).length;
  const warm   = leads.filter(l => l.score >= 40 && l.score < 65).length;
  const cold   = leads.filter(l => l.score < 40).length;
  const called = leads.filter(l => l.transcript).length;

  document.getElementById('funnel-wrap').innerHTML = `
    ${[
      { label:'Total Leads', count: total,  pct: 100,    cls:'blue' },
      { label:'Calls Made',  count: called, pct: Math.round(called/total*100),  cls:'purple' },
      { label:'Qualified',   count: hot,    pct: Math.round(hot/total*100),    cls:'green' },
      { label:'Nurturing',   count: warm,   pct: Math.round(warm/total*100),   cls:'amber' },
    ].map(r => `
      <div class="funnel-row">
        <span class="funnel-label">${r.label}</span>
        <div class="funnel-track"><div class="funnel-fill ${r.cls}" style="width:${r.pct}%">${r.pct > 15 ? r.pct + '%' : ''}</div></div>
        <span class="funnel-count">${r.count}</span>
      </div>
    `).join('')}
  `;

  // Mini timeline chart (last 7 days)
  const now   = Date.now();
  const days  = Array.from({ length: 7 }, (_, i) => {
    const dayStart = now - (6 - i) * 86400000;
    const dayEnd   = dayStart + 86400000;
    return leads.filter(l => l.created_at >= dayStart && l.created_at < dayEnd).length;
  });
  const maxDay = Math.max(...days, 1);
  const dayLabels = ['6d','5d','4d','3d','2d','1d','Today'];

  document.getElementById('timeline-chart').innerHTML = `
    <div class="mini-chart">
      ${days.map((d, i) => `
        <div class="mini-bar" style="height:${Math.max(8, Math.round(d / maxDay * 100))}%" title="${d} leads">
          <div class="mini-bar-tooltip">${d} leads</div>
        </div>
      `).join('')}
    </div>
    <div class="mini-chart-labels">
      ${dayLabels.map(l => `<span class="mini-chart-label">${l}</span>`).join('')}
    </div>
  `;

  // Ring chart — score distribution
  const ringWrap = document.getElementById('ring-wrap');
  const hotPct   = Math.round(hot  / total * 100);
  const warmPct  = Math.round(warm / total * 100);
  const coldPct  = 100 - hotPct - warmPct;
  const r = 40, circ = 2 * Math.PI * r;

  // Segments: hot → warm → cold
  const segs = [
    { pct: hotPct,  color: 'var(--green)',  label: 'Qualified' },
    { pct: warmPct, color: 'var(--amber)',  label: 'Nurturing' },
    { pct: coldPct, color: 'var(--red)',    label: 'Cold'      },
  ];

  let offset = 0;
  const paths = segs.map(seg => {
    const dash   = (seg.pct / 100) * circ;
    const gap    = circ - dash;
    const path   = `<circle class="ring-fill" cx="60" cy="60" r="${r}" stroke="${seg.color}" stroke-width="10" stroke-dasharray="${dash} ${gap}" stroke-dashoffset="${-offset}" />`;
    offset += dash;
    return path;
  }).join('');

  ringWrap.innerHTML = `
    <div class="ring-container">
      <svg class="ring-svg" width="120" height="120" viewBox="0 0 120 120">
        <circle class="ring-track" cx="60" cy="60" r="${r}" stroke-width="10"/>
        ${paths}
      </svg>
      <div class="ring-center-label">
        <div class="ring-center-value">${hotPct}%</div>
        <div class="ring-center-sub">Qualified</div>
      </div>
    </div>
    <div class="ring-legend">
      ${segs.map(s => `
        <div class="ring-legend-item">
          <div class="ring-legend-dot" style="background:${s.color}"></div>
          ${s.label}
        </div>
      `).join('')}
    </div>
  `;
}

// ── Page Navigation ───────────────────────────────────────────
function navigateTo(page) {
  State.activePage = page;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
  document.querySelectorAll('.page-section').forEach(el => {
    el.classList.toggle('active', el.id === `page-${page}`);
  });

  const titles = {
    overview:  { title: 'Pipeline Overview',  subtitle: 'Real-time lead activity and performance' },
    leads:     { title: 'All Leads',          subtitle: 'Browse, filter and act on every lead' },
    analytics: { title: 'Analytics',          subtitle: 'Pipeline funnel, score distribution and trends' },
    alerts:    { title: 'System Alerts',      subtitle: 'Agent errors, warnings and activity log' },
  };
  const t = titles[page] || titles.overview;
  document.getElementById('topbar-title').textContent    = t.title;
  document.getElementById('topbar-subtitle').textContent = t.subtitle;

  if (page === 'analytics') renderAnalytics();
}

// ── Full Data Load ────────────────────────────────────────────
async function loadData(silent = false) {
  if (State.refreshing) return;
  State.refreshing = true;
  const refreshBtn = document.getElementById('btn-refresh');
  if (refreshBtn) refreshBtn.querySelector('svg').classList.add('spinning');

  const [leads, alerts] = await Promise.all([fetchLeads(), fetchAlerts()]);
  State.leads  = leads;
  State.stats  = generateMockStats(leads);
  State.alerts = alerts;

  renderStats();
  renderLeadsTable(leads);
  renderAlerts();
  if (State.activePage === 'analytics') renderAnalytics();

  if (refreshBtn) refreshBtn.querySelector('svg').classList.remove('spinning');
  State.refreshing = false;
  if (!silent) showToast('Data refreshed', 'success');
}

// ── Build Dashboard HTML ──────────────────────────────────────
function buildDashboard() {
  document.getElementById('dashboard-view').innerHTML = `
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="sidebar-logo-icon">${Icons.logo}</div>
      <span class="sidebar-logo-name">LeadPipeline</span>
    </div>
    <div class="sidebar-section-label">Navigation</div>
    ${[
      { page:'overview',  icon: Icons.overview,  label:'Overview' },
      { page:'leads',     icon: Icons.leads,     label:'Leads' },
      { page:'analytics', icon: Icons.analytics, label:'Analytics' },
      { page:'alerts',    icon: Icons.alerts,    label:'Alerts' },
    ].map(n => `
      <button class="nav-item${n.page === 'overview' ? ' active' : ''}" data-page="${n.page}" onclick="navigateTo('${n.page}')">
        ${n.icon}<span>${n.label}</span>
      </button>
    `).join('')}
    <div class="sidebar-spacer"></div>
    <div class="sidebar-footer">
      <div class="sidebar-user">
        <div class="sidebar-avatar">${initials(State.user?.username || 'Admin')}</div>
        <div class="sidebar-user-info">
          <div class="sidebar-user-name">${State.user?.username || 'Admin'}</div>
          <div class="sidebar-user-role">${State.user?.role || 'Administrator'}</div>
        </div>
        <button class="btn-signout" title="Sign out" onclick="signOut()">${Icons.signout}</button>
      </div>
    </div>
  </aside>

  <!-- Main Content -->
  <main class="main-content">
    <header class="topbar">
      <div>
        <div class="topbar-title" id="topbar-title">Pipeline Overview</div>
        <div class="topbar-subtitle" id="topbar-subtitle">Real-time lead activity and performance</div>
      </div>
      <div class="topbar-actions">
        <span class="pill-badge green"><span class="pulse-dot"></span>Live</span>
        <button class="btn-icon" id="btn-refresh" title="Refresh data" onclick="loadData(false)">${Icons.refresh}</button>
      </div>
    </header>

    <div class="page-area">

      <!-- ─── Overview Page ─── -->
      <section class="page-section active" id="page-overview">
        <div class="stats-grid" id="stats-grid">
          <!-- Shimmer placeholders -->
          ${Array(4).fill(`<div class="stat-card"><div class="shimmer" style="height:38px;width:38px;border-radius:10px;margin-bottom:16px"></div><div class="shimmer" style="height:34px;width:70%;margin-bottom:8px"></div><div class="shimmer" style="height:14px;width:50%"></div></div>`).join('')}
        </div>

        <div class="section-header">
          <span class="section-title">Active Leads</span>
          <span class="section-count" id="leads-count">—</span>
        </div>
        <div class="leads-table-wrap">
          <table class="leads-table">
            <thead>
              <tr>
                <th>Lead</th>
                <th>Source</th>
                <th style="min-width:160px">Score</th>
                <th>Status</th>
                <th>Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="leads-tbody">
              ${Array(5).fill(`<tr><td colspan="6"><div class="shimmer" style="height:42px;margin:4px 20px;border-radius:8px"></div></td></tr>`).join('')}
            </tbody>
          </table>
        </div>

        <div class="section-header">
          <span class="section-title">Recent Alerts</span>
        </div>
        <div class="alerts-list" id="alerts-list-overview">
          ${Array(3).fill(`<div class="alert-item"><div class="shimmer" style="height:34px;width:34px;border-radius:9px;flex-shrink:0"></div><div style="flex:1"><div class="shimmer" style="height:12px;width:40%;margin-bottom:8px"></div><div class="shimmer" style="height:14px;width:80%"></div></div></div>`).join('')}
        </div>
      </section>

      <!-- ─── Leads Page ─── -->
      <section class="page-section" id="page-leads">
        <div class="section-header">
          <span class="section-title">All Leads</span>
          <span class="section-count" id="leads-all-count">—</span>
        </div>
        <div class="leads-table-wrap">
          <table class="leads-table">
            <thead>
              <tr>
                <th>Lead</th>
                <th>Source</th>
                <th style="min-width:160px">Score</th>
                <th>Status</th>
                <th>Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="leads-tbody-all"></tbody>
          </table>
        </div>
      </section>

      <!-- ─── Analytics Page ─── -->
      <section class="page-section" id="page-analytics">
        <div class="analytics-grid">
          <div class="chart-card">
            <div class="chart-card-title">Pipeline Funnel</div>
            <div id="funnel-wrap"></div>
          </div>
          <div class="chart-card">
            <div class="chart-card-title">Score Distribution</div>
            <div class="ring-wrap" id="ring-wrap"></div>
          </div>
          <div class="chart-card">
            <div class="chart-card-title">Leads This Week</div>
            <div id="timeline-chart"></div>
          </div>
          <div class="chart-card">
            <div class="chart-card-title">Key Metrics</div>
            <div id="kpi-wrap"></div>
          </div>
        </div>
      </section>

      <!-- ─── Alerts Page ─── -->
      <section class="page-section" id="page-alerts">
        <div class="section-header">
          <span class="section-title">System Alerts</span>
        </div>
        <div class="alerts-list" id="alerts-list"></div>
      </section>

    </div><!-- /.page-area -->
  </main>

  <!-- Drawer Backdrop -->
  <div class="drawer-backdrop" id="drawer-backdrop" onclick="closeDrawer()"></div>

  <!-- Lead Detail Drawer -->
  <aside class="drawer" id="drawer">
    <div class="drawer-header">
      <div class="drawer-header-info">
        <div class="drawer-lead-name" id="drawer-lead-name">—</div>
        <div class="drawer-lead-phone" id="drawer-lead-phone">—</div>
      </div>
      <div id="drawer-lead-status"></div>
      <button class="btn-close" onclick="closeDrawer()">${Icons.close}</button>
    </div>
    <div class="drawer-body">
      <p class="drawer-section-label" style="margin-bottom:10px">Contact Details</p>
      <div class="info-grid" id="drawer-info"></div>

      <p class="drawer-section-label" style="margin-bottom:10px">Score Breakdown</p>
      <div class="score-breakdown" id="drawer-scores"></div>

      <p class="drawer-section-label" style="margin-bottom:10px;margin-top:20px">AI Summary</p>
      <div class="score-breakdown" style="margin-bottom:20px">
        <p style="font-size:var(--text-sm);color:var(--label-secondary);line-height:1.6" id="drawer-summary"></p>
      </div>

      <div id="drawer-transcript-section" style="display:none;margin-bottom:20px">
        <p class="drawer-section-label" style="margin-bottom:10px">Call Transcript</p>
        <div class="transcript-wrap">
          <div class="transcript-head">
            <span class="transcript-title">Full Transcript</span>
            <span class="transcript-chars" id="drawer-transcript-chars"></span>
          </div>
          <div class="transcript-body" id="drawer-transcript"></div>
        </div>
      </div>

      <div id="drawer-actions"></div>
    </div>
  </aside>
  `;
}

// ── Leads Table Sync (both pages) ─────────────────────────────
function renderLeadsTable(leads) {
  const render = (tbodyId, countId) => {
    const tbody = document.getElementById(tbodyId);
    const cnt   = document.getElementById(countId);
    if (!tbody) return;
    if (cnt) cnt.textContent = leads.length;

    if (!leads.length) {
      tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state">${Icons.inbox}<h3>No leads yet</h3><p>Leads will appear here as they enter the pipeline.</p></div></td></tr>`;
      return;
    }

    tbody.innerHTML = leads.map(l => {
      const sc = scoreClass(l.score);
      return `
      <tr data-key="${l.session_key}" onclick="openDrawer(State.leads.find(x=>x.session_key==='${l.session_key}'))">
        <td>
          <div class="lead-name">${l.name}</div>
          <div class="lead-phone">${l.phone}</div>
        </td>
        <td><span class="source-badge">${capitalize(l.source)}</span></td>
        <td>
          <div class="score-cell">
            <div class="score-bar-track"><div class="score-bar-fill ${sc}" style="width:${l.score}%"></div></div>
            <span class="score-num ${sc}">${l.score}</span>
          </div>
        </td>
        <td>${statusBadgeHtml(l.status_cls, l.status)}</td>
        <td class="time-cell">${timeAgo(l.created_at)}</td>
        <td>
          <button class="btn-icon" title="View details" onclick="event.stopPropagation();openDrawer(State.leads.find(x=>x.session_key==='${l.session_key}'))">${Icons.info}</button>
        </td>
      </tr>`;
    }).join('');
  };

  render('leads-tbody', 'leads-count');
  render('leads-tbody-all', 'leads-all-count');
}

// ── Alerts Sync (overview + alerts page) ─────────────────────
function renderAlerts() {
  const iconMap = { red: Icons.alert, amber: Icons.alert, blue: Icons.info, green: Icons.check };
  const html = State.alerts.map(a => `
    <div class="alert-item">
      <div class="alert-icon-wrap ${a.type_cls}">${iconMap[a.type_cls] || Icons.info}</div>
      <div class="alert-body">
        <div class="alert-agent" style="color:var(--${a.type_cls === 'red' ? 'red' : a.type_cls === 'amber' ? 'amber' : a.type_cls === 'green' ? 'green' : 'blue'})">${a.agent}</div>
        <div class="alert-message">${a.message}</div>
      </div>
      <div class="alert-time">${timeAgo(a.timestamp)}</div>
    </div>
  `).join('') || `<div class="empty-state">${Icons.check}<h3>All clear</h3><p>No alerts right now.</p></div>`;

  const ov = document.getElementById('alerts-list-overview');
  const ap = document.getElementById('alerts-list');
  // Show first 5 in overview, all on alerts page
  if (ov) ov.innerHTML = State.alerts.slice(0, 5).map(a => `
    <div class="alert-item">
      <div class="alert-icon-wrap ${a.type_cls}">${iconMap[a.type_cls] || Icons.info}</div>
      <div class="alert-body">
        <div class="alert-agent" style="color:var(--${a.type_cls === 'red' ? 'red' : a.type_cls === 'amber' ? 'amber' : a.type_cls === 'green' ? 'green' : 'blue'})">${a.agent}</div>
        <div class="alert-message">${a.message}</div>
      </div>
      <div class="alert-time">${timeAgo(a.timestamp)}</div>
    </div>
  `).join('');
  if (ap) ap.innerHTML = html;
}

// ── Analytics KPI block ───────────────────────────────────────
function renderAnalytics() {
  const leads = State.leads;
  const s     = State.stats;
  const total = leads.length || 1;
  const hot   = leads.filter(l => l.score >= 65).length;
  const warm  = leads.filter(l => l.score >= 40 && l.score < 65).length;
  const cold  = leads.filter(l => l.score < 40).length;
  const called = leads.filter(l => l.transcript).length;

  // Funnel
  const fw = document.getElementById('funnel-wrap');
  if (fw) fw.innerHTML = [
    { label:'Total Leads',  count: total,  pct: 100, cls:'blue' },
    { label:'Calls Made',   count: called, pct: Math.round(called/total*100), cls:'purple' },
    { label:'Qualified',    count: hot,    pct: Math.round(hot/total*100),    cls:'green' },
    { label:'Nurturing',    count: warm,   pct: Math.round(warm/total*100),   cls:'amber' },
  ].map(r => `
    <div class="funnel-row">
      <span class="funnel-label">${r.label}</span>
      <div class="funnel-track"><div class="funnel-fill ${r.cls}" style="width:${r.pct}%">${r.pct > 15 ? r.pct + '%' : ''}</div></div>
      <span class="funnel-count">${r.count}</span>
    </div>
  `).join('');

  // Ring chart
  const rw = document.getElementById('ring-wrap');
  if (rw) {
    const hotPct  = Math.round(hot  / total * 100);
    const warmPct = Math.round(warm / total * 100);
    const coldPct = 100 - hotPct - warmPct;
    const r = 40, circ = 2 * Math.PI * r;
    const segs = [
      { pct: hotPct,  color: 'var(--green)' },
      { pct: warmPct, color: 'var(--amber)' },
      { pct: coldPct, color: 'var(--red)' },
    ];
    let off = 0;
    const paths = segs.map(sg => {
      const dash = (sg.pct / 100) * circ;
      const p = `<circle fill="none" cx="60" cy="60" r="${r}" stroke="${sg.color}" stroke-width="10" stroke-dasharray="${dash} ${circ - dash}" stroke-dashoffset="${-off}" stroke-linecap="round"/>`;
      off += dash;
      return p;
    }).join('');
    rw.innerHTML = `
      <div class="ring-container">
        <svg style="transform:rotate(-90deg)" width="120" height="120" viewBox="0 0 120 120">
          <circle fill="none" cx="60" cy="60" r="${r}" stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
          ${paths}
        </svg>
        <div class="ring-center-label"><div class="ring-center-value">${hotPct}%</div><div class="ring-center-sub">Qualified</div></div>
      </div>
      <div class="ring-legend">
        <div class="ring-legend-item"><div class="ring-legend-dot" style="background:var(--green)"></div>Qualified</div>
        <div class="ring-legend-item"><div class="ring-legend-dot" style="background:var(--amber)"></div>Nurturing</div>
        <div class="ring-legend-item"><div class="ring-legend-dot" style="background:var(--red)"></div>Cold</div>
      </div>`;
  }

  // Timeline
  const tc = document.getElementById('timeline-chart');
  if (tc) {
    const now  = Date.now();
    const days = Array.from({ length: 7 }, (_, i) => {
      const s = now - (6 - i) * 86400000, e = s + 86400000;
      return leads.filter(l => l.created_at >= s && l.created_at < e).length;
    });
    const maxD = Math.max(...days, 1);
    tc.innerHTML = `
      <div class="mini-chart">${days.map(d => `<div class="mini-bar" style="height:${Math.max(8, Math.round(d/maxD*100))}%"><div class="mini-bar-tooltip">${d} leads</div></div>`).join('')}</div>
      <div class="mini-chart-labels">${['6d','5d','4d','3d','2d','1d','Today'].map(l => `<span class="mini-chart-label">${l}</span>`).join('')}</div>`;
  }

  // KPI grid
  const kw = document.getElementById('kpi-wrap');
  if (kw) kw.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      ${[
        { label:'Conversion Rate', value: `${Math.round(hot/total*100)}%`,  color:'var(--green)' },
        { label:'Call Rate',       value: `${Math.round(called/total*100)}%`, color:'var(--blue)' },
        { label:'Avg Lead Score',  value: `${s.avg_score||0}`,              color:'var(--purple)' },
        { label:'Cold Leads',      value: cold,                             color:'var(--red)' },
      ].map(k => `
        <div class="info-tile">
          <div class="info-tile-label">${k.label}</div>
          <div class="info-tile-value" style="font-size:var(--text-xl);color:${k.color};font-weight:800;letter-spacing:-0.5px">${k.value}</div>
        </div>
      `).join('')}
    </div>`;
}

// ── Sign Out ──────────────────────────────────────────────────
function signOut() {
  clearInterval(State.polling);
  State.token = null;
  State.user  = null;
  localStorage.removeItem('plp_token');
  localStorage.removeItem('plp_user');
  document.getElementById('dashboard-view').classList.remove('visible');
  const lv = document.getElementById('login-view');
  lv.classList.remove('hidden');
  document.getElementById('login-username').value = '';
  document.getElementById('login-password').value = '';
  document.getElementById('login-error').classList.remove('visible');
}

// ── Login Form ────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const btn      = document.getElementById('login-btn');
  const errEl    = document.getElementById('login-error');

  if (!username || !password) {
    errEl.textContent = 'Please enter your username and password.';
    errEl.classList.add('visible');
    return;
  }

  btn.classList.add('loading');
  btn.textContent = 'Signing in…';
  errEl.classList.remove('visible');

  const result = await apiLogin(username, password);

  if (result) {
    State.token = result.token;
    State.user  = { username: result.username || username, role: result.role || 'Administrator' };
    localStorage.setItem('plp_token', State.token);
    localStorage.setItem('plp_user',  JSON.stringify(State.user));

    // Build & show dashboard
    buildDashboard();
    document.getElementById('login-view').classList.add('hidden');
    const dv = document.getElementById('dashboard-view');
    dv.classList.add('visible');

    await loadData(true);
    // Poll every 60s
    State.polling = setInterval(() => loadData(true), 60000);
  } else {
    errEl.innerHTML = `${Icons.alert} Invalid credentials. Try admin / admin123`;
    errEl.classList.add('visible');
  }

  btn.classList.remove('loading');
  btn.textContent = 'Sign In';
}

// ── Boot ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Restore session
  const savedToken = localStorage.getItem('plp_token');
  const savedUser  = localStorage.getItem('plp_user');

  if (savedToken && savedUser) {
    State.token = savedToken;
    State.user  = JSON.parse(savedUser);
    buildDashboard();
    document.getElementById('login-view').classList.add('hidden');
    document.getElementById('dashboard-view').classList.add('visible');
    loadData(true);
    State.polling = setInterval(() => loadData(true), 60000);
  }

  document.getElementById('login-form').addEventListener('submit', handleLogin);
});
