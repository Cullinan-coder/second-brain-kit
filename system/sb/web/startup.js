/* Paket 4: "Çalışmaya başla" düğmesi + ilerleme paneli (görünüm "startup") + "Uygulama ayarları" girişi. Ham HTML yok. */
(function () {
  'use strict';
  const SB = window.SB;
  if (!SB) return;
  const el = (tag, props, kids) => {
    const n = document.createElement(tag);
    if (props) for (const k in props) {
      if (k === 'cls') n.className = props[k];
      else if (k === 'text') n.textContent = props[k];
      else if (k === 'on') for (const e in props[k]) n.addEventListener(e, props[k][e]);
      else if (k === 'attrs') for (const a in props[k]) n.setAttribute(a, props[k][a]);
      else n[k] = props[k];
    }
    for (const c of [].concat(kids || [])) if (c != null && c !== false) n.append(c);
    return n;
  };
  const MARK = { pending: '○', running: '…', ok: '✓', warn: '!', error: '✗', skipped: '–' };
  const COLOR = { ok: '#16a34a', warn: '#d97706', error: '#dc2626', running: '#2563eb', pending: '#9ca3af', skipped: '#9ca3af' };
  let timer = null, last = null, box = null, btn = null;

  function paint(st) {
    last = st;
    if (btn) { btn.disabled = !!st.running; btn.title = st.running ? 'Çalışıyor…' : 'Çalışmaya başla'; }
    if (!box || !box.isConnected) return;
    const kids = [];
    if (st.update && st.update.available) {
      kids.push(el('div', { cls: 'card', text: 'Güncelleme var: ' + (st.update.current || '?') + ' → ' + (st.update.new || '?') }));
    }
    (st.steps || []).forEach((s) => {
      const row = el('div', { cls: 'sb-step', attrs: { 'data-step': s.id }, }, [
        el('span', { text: MARK[s.status] || '•', attrs: { 'aria-hidden': 'true' } }),
        el('strong', { text: ' ' + s.title }),
        el('span', { text: s.duration_s ? '  (' + s.duration_s + ' sn)' : '' }),
        s.message ? el('div', { text: s.message }) : null,
        s.fix ? el('pre', { text: 'Nasıl düzeltilir:\n' + s.fix, style: 'white-space:pre-wrap;font:inherit;opacity:.85;margin:.25em 0 0' }) : null
      ]);
      row.style.cssText = 'padding:8px 0;border-bottom:1px solid rgba(128,128,128,.25);color:' + (COLOR[s.status] || 'inherit');
      row.lastChild && row.querySelectorAll('div,pre').forEach((n) => { n.style.color = 'inherit'; });
      kids.push(row);
    });
    const foot = st.running ? 'Çalışıyor…' : st.done ? (st.ok ? 'Bitti.' : 'Bitti; sorunlar var.') : 'Henüz çalıştırılmadı.';
    kids.push(el('p', { text: foot }));
    box.replaceChildren(...kids);
  }

  async function poll() {
    const st = await SB.api('/api/v2/startup/status');
    if (st && !st.error) paint(st);
    if (st && st.running) timer = setTimeout(poll, 1000); else timer = null;
    return st;
  }
  function watch() { if (!timer) poll(); }

  async function run() {
    const r = await SB.api('/api/v2/startup/run', {});
    if (!r || r.error) { SB.toast('Başlatılamadı: ' + (r && r.error), 'error'); return; }
    if (!r.started) SB.toast('Zaten çalışıyor');
    if (r.status) paint(r.status);
    SB.openView('startup');
    watch();
  }

  async function openSettings() {
    const r = await SB.api('/api/v2/startup/settings-url');
    if (!r || r.error || !r.url) { SB.toast('Ayarlar açılamadı: ' + (r && r.error), 'error'); return; }
    if (!window.open(r.url, '_blank', 'noopener')) window.location.href = r.url;
  }

  SB.registerView('startup', {
    title: 'Çalışmaya başla', icon: 'spark',
    render(root) {
      box = el('div', { attrs: { role: 'status', 'aria-live': 'polite' } });
      const go = el('button', { cls: 'btn', type: 'button', text: 'Çalışmaya başla', on: { click: run } });
      root.append(el('div', { style: 'padding:16px;max-width:720px' }, [el('p', { text: 'Güncelleme, sağlık, günlük işler ve model ısıtma sırayla çalışır.' }), go, box]));
      poll();
      return () => { box = null; if (timer) { clearTimeout(timer); timer = null; } };
    }
  });
  SB.registerView('app-settings', {
    title: 'Uygulama ayarları', icon: 'settings',
    render(root) {
      root.append(el('div', { style: 'padding:16px' }, [
        el('p', { text: 'Özellikler, hesaplar, API anahtarları, MCP, veri yükleme, başlangıç, güncelleme ve sağlık ayarları ayrı bir pencerede açılır.' }),
        el('button', { cls: 'btn', type: 'button', text: 'Ayarları aç', on: { click: openSettings } })]));
    }
  });

  function mount() {
    const bar = document.querySelector('.top-actions');
    if (!bar || document.getElementById('btn-startup')) return;
    btn = el('button', { cls: 'btn sm', id: 'btn-startup', type: 'button', text: 'Çalışmaya başla', title: 'Çalışmaya başla', on: { click: run } });
    bar.prepend(btn);
    poll().then((st) => { if (st && st.running) watch(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
  if (SB.bus && SB.bus.on) SB.bus.on('ready', () => { mount(); });
})();
