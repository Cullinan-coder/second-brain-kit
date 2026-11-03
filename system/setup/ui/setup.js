'use strict';
/* Kurulum sihirbazı / ayarlar — ÇEKİRDEK. Ham HTML dizgesi yok (yalnız textContent / DOM düğümleri), dış kaynak yok.
   Şifre alanlarının değeri yalnız DOM'da durur, sunucuya bir kez gider, sonra silinir (wipeSecrets).
   Dosyalar: setup.js (çekirdek + açılış) · wizard.js (adım bileşenleri + sihirbaz kabuğu) · settings.js (sekmeli ayarlar kipi). */
const QS = new URLSearchParams(location.search);
const TOKEN = QS.get('t') || '';
const MODE = QS.get('mode') === 'settings' ? 'settings' : 'wizard';
const AXES = ['meslek', 'donanim', 'gizlilik', 'yogunluk'];
const TOUR_STEPS = 5;
const S = {
  tr: {}, en: {}, lang: 'tr',
  catalog: null, presets: null, axes: { meslek: '', donanim: '', gizlilik: '', yogunluk: '' }, warnings: [], combineBusy: false,
  sel: { modules: {}, items: {} }, memo: {}, reqs: null, reqsKey: '',
  profile: { name: '', full_name: '', vault: '', timezone: '', org: '', role: '' },
  auto: { on: false, minimized: true },
  step: 0, skipped: {}, visited: {}, tree: null, tab: 'features',
  panels: new Set(), watch: false, idle: 0, poll: null, after: null, tour: 0, saveTimer: null, applied: false,
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
function L(v) {                                   // {tr,en} nesnesi ya da düz metin → görünen metin
  if (v == null) return '';
  if (typeof v === 'object' && !Array.isArray(v)) return String(v[S.lang] || v.tr || v.en || '');
  return String(v);
}
const enc = encodeURIComponent;
function paras(text, cls) {
  return String(text || '').split('\n').filter((x) => x.trim()).map((x) => h('p', { class: cls || '', text: x }));
}
function btn(label, fn, cls, extra) { return h('button', { type: 'button', class: cls || 'ghost', text: label, onclick: fn, ...(extra || {}) }); }
function msg(el, text, kind) { el.className = 'msg ' + (kind || 'muted'); el.textContent = text || ''; }
function unavailable(r) {
  if (r && r.status === 404) return t('err.unavailable');
  const d = r && r.data;
  return (d && (d.error || d.message)) || t('err.generic');
}
function wipeSecrets() { document.querySelectorAll('input[type=password], textarea[data-secret]').forEach((i) => { i.value = ''; }); }
function arr(v) { return Array.isArray(v) ? v : []; }
function idOf(x) { return typeof x === 'object' && x ? String(x.id || x.key || x.name || '') : String(x); }

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
/* ham gövde yükleme (≤ 2 GB, parça parça değil): POST /api/import/upload?source=&name= */
async function uploadRaw(source, file) {
  try {
    const r = await fetch('/api/import/upload?source=' + enc(source) + '&name=' + enc(file.name), {
      method: 'POST', headers: { 'X-Setup-Token': TOKEN, 'Content-Type': 'application/octet-stream' }, body: file,
    });
    let data = null;
    try { data = await r.json(); } catch (e) { data = null; }
    return { ok: r.ok, status: r.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: null };
  }
}

/* ---- dil / tema / afiş ---- */
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
async function setLang(l) {
  S.lang = l;
  guard(() => localStorage.setItem('sb-setup-lang', l));
  applyI18n();
  if (S.catalog) S.catalog = normCatalog(S.catalog.raw);
  renderApp();
  if (await loadCatalog(true)) renderApp();                    // sunucu katalogu ?lang ile yerelleştirir
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

/* ---- katalog / seçim ---- */
function normMcp(m) {
  return {
    id: String(m.id || m.name), name: L(m.name || m.id), desc: L(m.desc), install: m.install || null, docs_url: m.docs_url || '',
    env: arr(m.env).map((e) => (typeof e === 'string' ? { key: e, label: e, secret: /key|token|secret|pass/i.test(e) }
      : { key: e.key || e.name, label: L(e.label || e.key || e.name), secret: e.secret !== undefined ? !!e.secret : /key|token|secret|pass/i.test(e.key || e.name || '') })),
    note: L(m.note),
  };
}
function normCatalog(raw) {
  const d = raw || {};
  let cats = d.categories || [];
  if (cats && !Array.isArray(cats)) cats = Object.entries(cats).map(([id, name]) => ({ id, name }));
  cats = cats.map((c) => (typeof c === 'string' ? { id: c, name: c } : { id: c.id || c.key || c.category, name: L(c.name || c.title || c.id) }));
  const modules = arr(d.modules).map((m) => ({
    id: String(m.id || m.key), name: L(m.name || m.title || m.id), desc: L(m.desc || m.description), category: m.category || '',
    on: m.default_on !== undefined ? !!m.default_on : (m.on !== undefined ? !!m.on : true), requires: m.requires || null,
    items: arr(m.items).map((i) => ({
      id: String(i.id), name: L(i.name || i.ad || i.title || i.id), cat: i.cat || i.faz || '', desc: L(i.desc || i.description), requires: i.requires || null,
    })),
  }));
  return {
    raw: d, categories: cats, modules,
    sources: arr(d.sources).map((s) => ({ id: String(s.id), name: L(s.name), desc: L(s.desc), formats: arr(s.formats), how_to: L(s.how_to), connector: s.connector || '' })),
    mcps: arr(d.mcps).map(normMcp), sectors: arr(d.sectors),
  };
}
async function loadCatalog(force) {
  if (S.catalog && !force) return true;
  const r = await api('/api/catalog?lang=' + S.lang);
  if (!r.ok || !r.data) return false;
  const first = !S.catalog;
  S.catalog = normCatalog(r.data);
  if (first && !Object.keys(S.sel.modules).length) defaultSelection();
  return true;
}
function defaultSelection() {
  S.sel = { modules: {}, items: {} };
  (S.catalog ? S.catalog.modules : []).forEach((m) => {
    S.sel.modules[m.id] = m.on;
    m.items.forEach((i) => { S.sel.items[i.id] = m.on; });
  });
}
async function loadPresets() {
  const r = await api('/api/presets');
  if (!r.ok || !r.data || !r.data.axes) { S.presets = null; return false; }
  const axes = {};
  AXES.forEach((a) => { axes[a] = arr(r.data.axes[a]).map((x) => ({ id: String(x.id), name: L(x.name), desc: L(x.desc) })); });
  S.presets = { axes, recommended: r.data.recommended || {} };
  const pick = (a, pref) => (axes[a].some((x) => x.id === pref) ? pref : '');
  if (!S.axes.donanim) S.axes.donanim = pick('donanim', S.presets.recommended.donanim) || pick('donanim', 'orta');
  if (!S.axes.gizlilik) S.axes.gizlilik = pick('gizlilik', 'karma');
  if (!S.axes.yogunluk) S.axes.yogunluk = pick('yogunluk', 'gunluk');
  return true;
}
async function applyCombine() {
  S.combineBusy = true;
  const r = await api('/api/combine', { ...S.axes });
  S.combineBusy = false;
  if (!r.ok || !r.data) return false;
  const d = r.data;
  S.sel = { modules: {}, items: {} };
  (S.catalog ? S.catalog.modules : []).forEach((m) => {
    const on = !!(d.modules && d.modules[m.id]);
    S.sel.modules[m.id] = on;
    m.items.forEach((i) => { S.sel.items[i.id] = d.items && d.items[i.id] !== undefined ? !!d.items[i.id] : on; });
  });
  S.memo = {};
  S.warnings = arr(d.warnings).map(L);
  S.reqsKey = '';
  return true;
}
function counts() {
  let mods = 0, items = 0, total = 0;
  (S.catalog ? S.catalog.modules : []).forEach((m) => {
    total += m.items.length;
    if (S.sel.modules[m.id]) { mods++; m.items.forEach((i) => { if (S.sel.items[i.id]) items++; }); }
  });
  return { mods, items, total, modTotal: S.catalog ? S.catalog.modules.length : 0 };
}
function selectionPayload() {
  const modules = {}, items = {};
  (S.catalog ? S.catalog.modules : []).forEach((m) => {
    modules[m.id] = !!S.sel.modules[m.id];
    m.items.forEach((i) => { items[i.id] = !!(S.sel.modules[m.id] && S.sel.items[i.id]); });
  });
  return { modules, items };
}
async function loadReqs() {
  const body = selectionPayload();
  const key = JSON.stringify(body);
  if (S.reqs && S.reqsKey === key) return S.reqs;
  const r = await api('/api/requirements', body);
  if (!r.ok || !r.data) { S.reqs = null; return null; }
  const d = r.data;
  S.reqs = {
    accounts: arr(d.accounts).map(idOf), fields: arr(d.fields), secrets: arr(d.secrets).map(idOf), imports: arr(d.imports).map(idOf), mcps: arr(d.mcps).map(idOf),
  };
  S.reqsKey = key;
  return S.reqs;
}
function sourceNeeded(id) { return !S.reqs || !S.reqs.imports.length || S.reqs.imports.includes(id); }

/* ---- canlı iş ilerlemesi (/api/progress) ---- */
const NSTATUS = { pending: 'bekliyor', running: 'calisiyor', done: 'tamam', skipped: 'tamam', error: 'hata' };
const nstat = (s) => NSTATUS[s] || s;
function jobPanel() {
  const fill = h('div', { class: 'fill' });
  const pct = h('span', { text: '0%' });
  const bar = h('div', { class: 'progress sm', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': '0' }, fill, pct);
  const steps = h('ul', { class: 'steps' });
  const log = h('pre', { class: 'log small', 'aria-live': 'polite' });
  const el = h('div', { class: 'job', hidden: !S.watch }, bar, steps, log);
  const p = {
    el,
    update(d) {
      el.hidden = false;
      const v = Math.max(0, Math.min(100, Math.round(d.percent || 0)));
      fill.style.width = v + '%'; pct.textContent = v + '%'; bar.setAttribute('aria-valuenow', String(v));
      clear(steps);
      arr(d.steps).forEach((s) => steps.append(h('li', { 'data-s': nstat(s.status) }, (s.title || s.id) + ' — ' + t('st.' + nstat(s.status)))));
      const stick = log.scrollTop + log.clientHeight >= log.scrollHeight - 20;
      log.textContent = arr(d.log).slice(-60).join('\n') || t('log.empty');
      if (stick) log.scrollTop = log.scrollHeight;
    },
  };
  S.panels.add(p);
  return p;
}
async function pollOnce() {
  const r = await api('/api/progress');
  if (!r.ok || !r.data) return null;
  const d = r.data;
  S.panels.forEach((p) => { if (!p.el.isConnected) S.panels.delete(p); else if (S.watch || d.running) p.update(d); });
  const running = d.running === true || arr(d.steps).some((s) => nstat(s.status) === 'calisiyor');
  S.idle = running ? 0 : S.idle + 1;
  if (S.watch && S.idle >= 2) {
    S.watch = false;
    stopPolling();
    const cb = S.after;
    S.after = null;
    if (cb) cb(d);
  }
  return d;
}
function startWatch(after) {
  S.watch = true; S.idle = 0; S.after = after || null;
  S.panels.forEach((p) => { p.el.hidden = false; });
  stopPolling();
  S.poll = setInterval(pollOnce, 1000);
  pollOnce();
}
function stopPolling() { if (S.poll) { clearInterval(S.poll); S.poll = null; } }

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

/* ---- açılış ---- */
function renderApp() {
  applyI18n();
  if (MODE === 'settings') renderSettings(); else renderWizard();
  renderTour();
}
async function boot() {
  initLang();
  const th = guard(() => localStorage.getItem('sb-setup-theme'));
  if (th) setTheme(th);
  await loadI18n();
  applyI18n();
  if (!TOKEN) showBanner(t('err.token'), 'bad');
  $('btn-lang').addEventListener('click', () => setLang(S.lang === 'tr' ? 'en' : 'tr'));
  $('btn-theme').addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(cur === 'dark' ? 'light' : 'dark');
  });
  $('tour-close').addEventListener('click', endTour);
  $('tour-next').addEventListener('click', () => { if (S.tour >= TOUR_STEPS) endTour(); else { S.tour++; renderTour(); } });
  $('app-wizard').hidden = MODE !== 'wizard';
  $('app-settings').hidden = MODE !== 'settings';
  document.body.dataset.mode = MODE;
  const ok = await loadCatalog();
  await loadPresets();
  if (MODE === 'settings') await startSettings(ok); else await startWizard(ok);
  pollOnce();
}
window.addEventListener('DOMContentLoaded', boot);
