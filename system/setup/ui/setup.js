'use strict';
/* Kurulum paneli. Ham HTML dizgesi yok (yalnız textContent / DOM düğümleri), dış kaynak yok.
   Şifre alanlarının değeri yalnız DOM'da durur, sunucuya bir kez gider, sonra silinir. */
const TOKEN = new URLSearchParams(location.search).get('t') || '';
const CATS = {
  mail: ['gmail', 'imap', 'calendar', 'dates', 'derived', 'digest'],
  google: ['contacts', 'drive', 'github'],
  data: ['sms', 'local_files', 'projects', 'courses', 'sessions', 'linkedin', 'browser', 'inbox', 'cards'],
  ai: ['brain', 'vision', 'voice', 'image_gen', 'screen_watch', 'flush', 'memory_ui'],
  assist: ['assistant', 'phone', 'computer', 'media', 'whatsapp', 'capture', 'claude_hooks', 'night', 'automation', 'telegram', 'wake_word'],
};
const WIZ = { google: 7, spotify: 4, telegram: 4, tailscale: 4 };
const TOUR_STEPS = 5;
const S = {
  tr: {}, en: {}, lang: 'tr', cats: null, presets: [], modules: [], preset: '', picked: {}, fields: [],
  wiz: '', wizStep: 1, applying: false, poll: null, tour: 0,
};

const $ = (id) => document.getElementById(id);
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (k === 'text') el.textContent = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) if (kid != null) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return el;
}
function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }
function t(key, vars) {
  let s = (S[S.lang] && S[S.lang][key]) || (S.tr && S.tr[key]) || key;
  for (const [k, v] of Object.entries(vars || {})) s = s.split('{' + k + '}').join(String(v));
  return s;
}
function guard(fn) { try { return fn(); } catch (e) { return null; } }

/* ---- API: hiçbir zaman fırlatmaz; 404/ağ hatası => {ok:false,status,data:null} ---- */
async function api(path, body, method) {
  const opts = { method: method || (body === undefined ? 'GET' : 'POST'), headers: { 'X-Setup-Token': TOKEN } };
  if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  try {
    const r = await fetch(path, opts);
    let data = null;
    try { data = await r.json(); } catch (e) { data = null; }
    return { ok: r.ok, status: r.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: null };
  }
}

/* ---- dil / tema ---- */
function applyI18n() {
  document.documentElement.lang = S.lang;
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-title]').forEach((el) => { el.title = t(el.dataset.i18nTitle); });
  document.title = t('app.title');
}
async function loadI18n() {
  for (const url of ['i18n.json', '/i18n.json']) {
    try {
      const r = await fetch(url, { headers: { 'X-Setup-Token': TOKEN } });
      if (r.ok) { const d = await r.json(); S.tr = d.tr || {}; S.en = d.en || {}; return; }
    } catch (e) { /* sıradaki adresi dene */ }
  }
}
function initLang() {
  const saved = guard(() => localStorage.getItem('sb-setup-lang'));
  S.lang = saved || ((navigator.language || 'tr').toLowerCase().startsWith('tr') ? 'tr' : 'en');
}
function setLang(l) {
  S.lang = l;
  guard(() => localStorage.setItem('sb-setup-lang', l));
  renderAll();
}
function setTheme(th) {
  document.documentElement.dataset.theme = th;
  guard(() => localStorage.setItem('sb-setup-theme', th));
}
function showBanner(text, kind, action) {
  const b = $('banner');
  clear(b);
  if (!text) { b.hidden = true; return; }
  b.append(h('span', { class: kind || '', text }), ' ');
  if (action) b.append(h('button', { type: 'button', class: 'primary', text: action.label, onclick: action.fn }));
  b.hidden = false;
}

/* ---- sekmeler ---- */
function showTab(name) {
  document.querySelectorAll('#tabs [role=tab]').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === name)));
  document.querySelectorAll('main .panel').forEach((p) => { p.hidden = p.id !== 'p-' + name; });
  if (name === 'model') loadHardware();
  if (name === 'guncelle') loadUpdate();
  if (name === 'hesaplar') loadFields();
}

/* ---- Kur: hazır seçimler + özellikler ---- */
const NSTATUS = { pending: 'bekliyor', running: 'calisiyor', done: 'tamam', skipped: 'tamam', error: 'hata' };
const nstat = (s) => NSTATUS[s] || s;
function normPresets(d) {
  let list = Array.isArray(d) ? d : (d && (d.presets || d.items)) || [];
  if (!Array.isArray(list)) list = Object.entries(list).map(([id, p]) => ({ ...p, id }));   // sunucu: {ad: {label,desc,modules}}
  return list.map((p) => (typeof p === 'string' ? { id: p, title: p } : {
    id: p.id || p.key || p.name, title: p.label || p.title || p.name || p.id, desc: p.desc || p.description || '', modules: p.modules || null,
  }));
}
function normModules(list, cats) {
  if (list && !Array.isArray(list)) {                                  // sunucu: {anahtar: {name,desc,requires,default,category}}
    const where = {};
    Object.entries(cats || {}).forEach(([c, keys]) => keys.forEach((k) => { where[k] = c; }));
    list = Object.entries(list).map(([id, m]) => ({ ...m, id, category: m.category || where[id] }));
  }
  return (list || []).map((m) => (Array.isArray(m)
    ? { id: m[0], name: m[1], desc: m[2], requires: m[3], on: m[4] }
    : { id: m.id || m.key, name: m.name || m.title || m.id, desc: m.desc || m.description || '', requires: m.requires || m.req || '', on: m.on !== undefined ? m.on : m.default, category: m.category }));
}
function catOf(m) {
  if (m.category) return m.category;
  for (const [c, keys] of Object.entries(CATS)) if (keys.includes(m.id)) return c;
  return 'other';
}
async function loadPresets() {
  const r = await api('/api/presets');
  if (!r.ok || !r.data) { $('presets').append(h('p', { class: 'muted', text: t('err.unavailable') })); return; }
  S.presets = normPresets(r.data);
  const mods = Array.isArray(r.data) ? [] : (r.data.modules || r.data.features || []);
  S.cats = (!Array.isArray(r.data) && r.data.categories) || null;
  if (Array.isArray(mods) ? mods.length : Object.keys(mods).length) S.modules = normModules(mods, S.cats);
  S.modules.forEach((m) => { if (!(m.id in S.picked)) S.picked[m.id] = m.on !== false; });
  renderPresets();
  renderModules();
  if (S.presets.length && !S.preset) selectPreset(S.presets[0].id);
}
function selectPreset(id) {
  S.preset = id;
  const p = S.presets.find((x) => x.id === id);
  if (p && p.modules) {
    const on = Array.isArray(p.modules) ? p.modules : null;
    S.modules.forEach((m) => { S.picked[m.id] = on ? on.includes(m.id) : !!p.modules[m.id]; });
  }
  renderPresets();
  renderModules();
  loadFields();
}
function renderPresets() {
  const box = $('presets');
  clear(box);
  S.presets.forEach((p) => box.append(h('button', {
    type: 'button', class: 'card', 'aria-pressed': String(p.id === S.preset), onclick: () => selectPreset(p.id),
  }, h('b', { text: p.title }), h('small', { text: p.desc }))));
}
function renderModules() {
  const box = $('modules');
  clear(box);
  const groups = {};
  S.modules.forEach((m) => { (groups[catOf(m)] = groups[catOf(m)] || []).push(m); });
  const order = [...new Set([...Object.keys(S.cats || {}), ...Object.keys(CATS), 'other'])];
  for (const c of order) {
    if (!groups[c]) continue;
    const grid = h('div', { class: 'mods' });
    groups[c].forEach((m) => {
      const cb = h('input', { type: 'checkbox', id: 'mod-' + m.id, onchange: (e) => { S.picked[m.id] = e.target.checked; } });
      cb.checked = !!S.picked[m.id];
      grid.append(h('label', { class: 'check' }, cb, h('span', {}, m.name,
        h('small', { text: m.desc + (m.requires && m.requires !== '—' ? ' · ' + t('kur.requires') + ': ' + m.requires : '') }))));
    });
    box.append(h('fieldset', {}, h('legend', { text: (S.tr['cat.' + c] || S.en['cat.' + c]) ? t('cat.' + c) : c }), grid));
  }
}
function setAllModules(v) {
  S.modules.forEach((m) => { S.picked[m.id] = v; });
  renderModules();
}
function collectFields() {
  const out = {};
  document.querySelectorAll('#fields input[data-field]').forEach((i) => { if (i.value) out[i.dataset.field] = i.value; });
  return out;
}
function wipeSecrets() { document.querySelectorAll('#fields input[type=password]').forEach((i) => { i.value = ''; }); }
async function apply(resume) {
  const btn = $('apply');
  btn.disabled = true;
  const r = await api('/api/apply', { preset: S.preset, modules: { ...S.picked }, fields: collectFields(), resume: resume === true });
  wipeSecrets();
  btn.disabled = false;
  if (r.status === 409) { $('apply-msg').textContent = t('kur.busy'); S.applying = true; startPolling(); return; }
  if (!r.ok) { $('apply-msg').textContent = t('err.unavailable'); return; }
  $('apply-msg').textContent = t('kur.applying');
  S.applying = true;
  showTab('gunluk');
  startPolling();
}

/* ---- Hesaplar ---- */
async function loadFields() {
  const box = $('fields');
  const r = await api('/api/fields?preset=' + encodeURIComponent(S.preset || ''));
  clear(box);
  if (!r.ok || !r.data) { box.append(h('p', { class: 'muted', text: t('err.unavailable') })); return; }
  const list = Array.isArray(r.data) ? r.data : (r.data.fields || []);
  if (!S.modules.length && r.data.modules) {
    S.modules = normModules(r.data.modules, r.data.categories);
    S.modules.forEach((m) => { if (!(m.id in S.picked)) S.picked[m.id] = m.on !== false; });
    renderModules();
  }
  if (!list.length) { box.append(h('p', { class: 'muted', text: t('hes.none') })); return; }
  list.forEach((f) => {
    const id = f.key || f.id || f.name;
    const secret = f.secret || f.kind === 'secret' || f.kind === 'password' || f.type === 'password';
    const input = h('input', { type: secret ? 'password' : 'text', id: 'f-' + id, 'data-field': id, autocomplete: 'off', placeholder: f.placeholder || '' });
    if ((f.value || f.default) && !secret) input.value = f.value || f.default;
    const res = h('span', { class: 'muted', 'aria-live': 'polite' });
    const testKind = f.test || f.test_kind;
    const btn = testKind ? h('button', { type: 'button', class: 'ghost', text: t('hes.test'), onclick: async () => {
      res.className = 'muted'; res.textContent = t('hes.testing');
      const tr = await api('/api/test', { kind: testKind, fields: collectFields() });
      if (!tr.ok || !tr.data) { res.className = 'warn'; res.textContent = t('err.unavailable'); return; }
      res.className = tr.data.ok ? 'ok' : 'bad';
      res.textContent = (tr.data.ok ? '✓ ' : '✗ ') + (tr.data.message || '');
    } }) : h('span');
    box.append(h('div', { class: 'field' }, h('label', { for: 'f-' + id, text: f.label || f.title || id }), h('div', {}, input, res), btn));
  });
}
async function exportProfile() {
  const r = await api('/api/profile');
  if (!r.ok || !r.data) { showBanner(t('err.unavailable'), 'warn'); return; }
  const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' });
  const a = h('a', { href: URL.createObjectURL(blob), download: 'second-brain-profil.json' });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
async function importProfile(file) {
  if (!file) return;
  let data;
  try { data = JSON.parse(await file.text()); } catch (e) { showBanner(t('err.generic'), 'bad'); return; }
  const r = await api('/api/profile', data);
  showBanner(r.ok ? t('hes.imported') : t('err.unavailable'), r.ok ? 'ok' : 'warn');
  if (r.ok) { await loadState(); loadFields(); }
}

/* ---- Model / donanım ---- */
async function loadHardware() {
  const box = $('hw');
  clear(box);
  box.append(h('p', { class: 'muted', text: '…' }));                // donanım taraması birkaç saniye sürebilir
  const r = await api('/api/hardware');
  clear(box);
  if (!r.ok || !r.data) { box.append(h('p', { class: 'muted', text: t('model.none') })); return; }
  const d = r.data.hardware || r.data;
  const num = (v, u) => (v == null || v === '' ? '—' : (typeof v === 'number' ? Math.round(v * 10) / 10 + ' ' + u : String(v)));
  const gpu = d.gpu && typeof d.gpu === 'object' ? [d.gpu.name, d.gpu.vram_gb != null ? d.gpu.vram_gb + ' GB' : ''].filter(Boolean).join(' · ') : d.gpu;
  const cells = [
    ['model.ram', num(d.ram_gb != null ? d.ram_gb : d.ram, 'GB')],
    ['model.cpu', d.cpu_name || (d.cpu_cores != null ? d.cpu_cores + ' ' + t('model.cores') : d.cpu || '—')],
    ['model.gpu', gpu || (d.vram_gb != null ? num(d.vram_gb, 'GB') : '—')],
    ['model.disk', num(d.disk_free_gb != null ? d.disk_free_gb : d.disk, 'GB')],
  ];
  const grid = h('div', { class: 'hw' });
  cells.forEach(([k, v]) => grid.append(h('div', {}, h('b', { text: t(k) }), String(v))));
  box.append(grid);
  const rec = r.data.recommend || r.data.recommended || d.recommended;
  if (rec) {
    const name = typeof rec === 'object' ? [rec.profile, rec.model].filter(Boolean).join(' · ') : String(rec);
    box.append(h('p', {}, h('b', { text: t('model.rec') + ': ' }), name));
    if (rec.why) box.append(h('p', { class: 'muted', text: String(rec.why) }));
  }
  if (d.note) box.append(h('p', { class: 'muted', text: String(d.note) }));
}

/* ---- Sihirbazlar ---- */
function renderWizList() {
  const box = $('wiz-list');
  clear(box);
  Object.keys(WIZ).forEach((id) => box.append(h('button', {
    type: 'button', class: 'card', 'aria-pressed': String(S.wiz === id), onclick: () => { S.wiz = id; S.wizStep = 1; renderWizList(); renderWiz(); },
  }, h('b', { text: t('wiz.' + id + '.name') }))));
}
function renderWiz() {
  const box = $('wiz-body');
  clear(box);
  if (!S.wiz) { box.append(h('p', { class: 'muted', text: t('wiz.pick') })); return; }
  const n = S.wizStep, m = WIZ[S.wiz];
  box.append(h('div', { class: 'wiz' },
    h('p', { class: 'muted', text: t('wiz.step', { n, m }) }),
    h('p', { text: t('wiz.' + S.wiz + '.' + n) }),
    h('div', { class: 'row' },
      h('button', { type: 'button', class: 'ghost', text: t('wiz.prev'), disabled: n <= 1, onclick: () => { S.wizStep--; renderWiz(); } }),
      h('button', { type: 'button', class: 'primary', text: n >= m ? t('wiz.done') : t('wiz.next'), onclick: () => { if (n >= m) { S.wiz = ''; renderWizList(); } else S.wizStep++; renderWiz(); } }))));
}

/* ---- Güncelle / Sağlık / Kaldır ---- */
async function loadUpdate() {
  const box = $('upd');
  const r = await api('/api/update');
  clear(box);
  if (!r.ok || !r.data) { box.append(h('p', { class: 'muted', text: t('err.unavailable') })); return; }
  const d = r.data;
  box.append(h('p', {}, t('upd.current') + ': ', h('b', { text: String(d.current || d.version || '—') })),
    h('p', {}, t('upd.latest') + ': ', h('b', { text: String(d.latest || '—') })));
  const avail = d.update_available !== undefined ? d.update_available : (d.available !== undefined ? d.available : (d.latest && d.current && d.latest !== d.current));
  box.append(h('p', { class: avail ? 'warn' : 'ok', text: avail ? t('upd.available') : t('upd.upToDate') }));
}
async function runUpdate() {
  const r = await api('/api/update', {});
  showBanner(r.ok ? t('upd.started') : t('err.unavailable'), r.ok ? 'ok' : 'warn');
  if (r.ok) { S.applying = true; startPolling(); }
}
async function runHealth() {
  const box = $('health');
  clear(box);
  box.append(h('p', { class: 'muted', text: '…' }));                // sağlık kontrolü 10-20 sn sürebilir
  const r = await api('/api/health');
  clear(box);
  if (!r.ok || !r.data) { box.append(h('p', { class: 'muted', text: t('err.unavailable') })); return; }
  const list = Array.isArray(r.data) ? r.data : (r.data.rows || r.data.checks || r.data.items || []);
  if (!list.length) { box.append(h('p', { class: 'muted', text: t('sag.none') })); return; }
  const ul = h('ul', { class: 'steps' });
  list.forEach((c) => {
    const good = c.ok === true || c.status === 'ok' || c.status === 'tamam';
    ul.append(h('li', { 'data-s': good ? 'tamam' : (c.status === 'warn' ? 'calisiyor' : 'hata') }, h('b', { text: String(c.name || c.title || c.id || '') }), ' ' + String(c.hint || c.message || c.detail || '')));
  });
  box.append(ul);
}
async function uninstall(confirm) {
  const out = $('un-out');
  if (confirm && !$('un-confirm').checked) { out.textContent = t('kal.needConfirm'); return; }
  const r = confirm ? await api('/api/uninstall', { confirm: true }) : await api('/api/uninstall');
  if (!r.ok || !r.data) { out.textContent = t('err.unavailable'); return; }
  const d = r.data;
  const lines = d.plan || d.actions || d.log || d.items || [];
  const txt = (a) => (a && typeof a === 'object' ? (a.desc || a.id || JSON.stringify(a)) + (a.auto === false ? ' *' : '') : String(a));
  out.textContent = (Array.isArray(lines) ? lines.map(txt).join('\n') : String(lines)) || d.message || JSON.stringify(d, null, 2);
}

/* ---- Günlük + ilerleme ---- */
function renderProgress(d) {
  const pct = Math.max(0, Math.min(100, Math.round(d.percent || 0)));
  $('fill').style.width = pct + '%';
  $('pct').textContent = pct + '%';
  $('bar').setAttribute('aria-valuenow', String(pct));
  const ul = $('steps');
  clear(ul);
  (d.steps || []).forEach((s) => ul.append(h('li', { 'data-s': nstat(s.status) }, (s.title || s.id) + ' — ' + t('st.' + nstat(s.status)))));
  const log = $('log');
  const stick = log.scrollTop + log.clientHeight >= log.scrollHeight - 20;
  log.textContent = (d.log || []).join('\n') || t('log.empty');
  if (stick) log.scrollTop = log.scrollHeight;
}
async function pollOnce() {
  const r = await api('/api/progress');
  if (!r.ok || !r.data) return null;
  renderProgress(r.data);
  const steps = r.data.steps || [];
  const st = steps.map((s) => nstat(s.status));
  const running = r.data.running === true || st.includes('calisiyor');
  const failed = st.includes('hata') || !!r.data.error;
  const done = st.length > 0 && st.every((x) => x === 'tamam');
  if (S.applying && !running && (done || failed)) {
    S.applying = false;
    stopPolling();
    if (done) startTour();
  }
  return r.data;
}
function startPolling() { stopPolling(); S.poll = setInterval(pollOnce, 1000); pollOnce(); }
function stopPolling() { if (S.poll) { clearInterval(S.poll); S.poll = null; } }
async function loadState() {
  const r = await api('/api/state');
  if (!r.ok || !r.data) return;
  const d = r.data;
  if (d.resumable) showBanner(t('kur.resume'), 'warn', { label: t('kur.resumeBtn'), fn: () => { showBanner(''); apply(true); } });
}

/* ---- İlk 10 dakika turu ---- */
function startTour() {
  if (guard(() => localStorage.getItem('sb-setup-tour') === '1')) return;
  S.tour = 1;
  renderTour();
}
function renderTour() {
  const m = $('tour');
  if (!S.tour) { m.hidden = true; return; }
  m.hidden = false;
  $('tour-title').textContent = t('tour.title') + ' · ' + t('tour.' + S.tour + '.t');
  $('tour-text').textContent = t('tour.' + S.tour + '.x');
  $('tour-n').textContent = S.tour + '/' + TOUR_STEPS;
  $('tour-next').textContent = S.tour >= TOUR_STEPS ? t('tour.done') : t('tour.next');
}
function endTour() {
  S.tour = 0;
  guard(() => localStorage.setItem('sb-setup-tour', '1'));
  renderTour();
}

/* ---- başlangıç ---- */
function renderAll() {
  applyI18n();
  renderPresets();
  renderModules();
  renderWizList();
  renderWiz();
  renderTour();
}
async function init() {
  initLang();
  const th = guard(() => localStorage.getItem('sb-setup-theme'));
  if (th) setTheme(th);
  await loadI18n();
  applyI18n();
  if (!TOKEN) showBanner(t('err.token'), 'bad');
  $('tabs').addEventListener('click', (e) => { const b = e.target.closest('[role=tab]'); if (b) showTab(b.dataset.tab); });
  $('btn-lang').addEventListener('click', () => setLang(S.lang === 'tr' ? 'en' : 'tr'));
  $('btn-theme').addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(cur === 'dark' ? 'light' : 'dark');
  });
  $('mod-all').addEventListener('click', () => setAllModules(true));
  $('mod-none').addEventListener('click', () => setAllModules(false));
  $('apply').addEventListener('click', () => apply(false));
  $('prof-export').addEventListener('click', exportProfile);
  $('prof-file').addEventListener('change', (e) => { importProfile(e.target.files[0]); e.target.value = ''; });
  $('hw-refresh').addEventListener('click', loadHardware);
  $('upd-check').addEventListener('click', loadUpdate);
  $('upd-run').addEventListener('click', runUpdate);
  $('health-run').addEventListener('click', runHealth);
  $('un-plan').addEventListener('click', () => uninstall(false));
  $('un-run').addEventListener('click', () => uninstall(true));
  $('tour-close').addEventListener('click', endTour);
  $('tour-next').addEventListener('click', () => { if (S.tour >= TOUR_STEPS) endTour(); else { S.tour++; renderTour(); } });
  renderWizList();
  renderWiz();
  showTab('kur');
  await loadPresets();
  await loadState();
  pollOnce();
}
init();
