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
      const row = el('div', { cls: 'sb-step st-' + (s.status || 'pending'), attrs: { 'data-step': s.id }, }, [
        el('span', { text: MARK[s.status] || '•', attrs: { 'aria-hidden': 'true' } }),
        el('strong', { text: ' ' + s.title }),
        el('span', { text: s.duration_s ? '  (' + s.duration_s + ' sn)' : '' }),
        s.message ? el('div', { text: s.message }) : null,
        s.fix ? el('pre', { text: 'Nasıl düzeltilir:\n' + s.fix, cls: 'pre' }) : null
      ]);
      row.lastChild && row.querySelectorAll('div,pre').forEach((n) => { n.style.color = 'inherit'; });
      kids.push(row);
    });
    const foot = st.running ? 'Çalışıyor…' : st.done ? (st.ok ? 'Bitti.' : 'Bitti; sorunlar var.') : 'Henüz çalıştırılmadı.';
    kids.push(el('p', { text: foot }));
    box.replaceChildren(...kids);
    if (st.done && !st.running) paintApps();
  }

  /* Uygulamalar kartı: ClipBoardLine / Nashi durumu, Aç, Şimdi senkronla */
  let appsBox = null;
  async function paintApps() {
    if (!appsBox || !appsBox.isConnected) return;
    const r = await SB.api('/api/v2/apps/status');
    if (!r || r.error) { appsBox.replaceChildren(el('p', { text: 'Uygulama durumu okunamadı.' })); return; }
    appsBox.replaceChildren(el('h3', { text: 'Uygulamalar' }), ...(r.apps || []).map((a) => {
      const state = !a.supported ? 'bu sistemde desteklenmiyor' : !a.installed ? 'kurulu değil (kurmak için: sb apps install ' + a.id + ')'
        : (a.running ? 'çalışıyor' : 'kapalı') + (a.version ? ' · sürüm ' + a.version : '');
      const sync = a.last_sync ? 'Son senkron: ' + a.last_sync.replace('T', ' ') + ' · ' + (a.records || 0) + ' kayıt'
        + (a.skipped_secret ? ' · ' + a.skipped_secret + ' kayıt sır içerdiği için atlandı' : '') : 'Henüz senkron yok';
      const open = el('button', { cls: 'btn sm', type: 'button', text: 'Aç', disabled: !a.installed || a.running, on: { click: async () => {
        const x = await SB.api('/api/v2/apps/start', { id: a.id }); SB.toast(x && x.message || (x && x.error) || 'Tamam'); setTimeout(paintApps, 1500); } } });
      const syn = el('button', { cls: 'btn sm', type: 'button', text: 'Şimdi senkronla', disabled: !a.supported, on: { click: async () => {
        const x = await SB.api('/api/v2/apps/sync', { id: a.id }); SB.toast(x && x.text || (x && x.error) || 'Tamam'); paintApps(); } } });
      const pin = a.pinned_version ? 'Bilinen iyi (sabit) sürüm: ' + a.pinned_version + (a.pinned_by_user ? ' (senin onayınla)' : '') + ' · SHA-256 ' + String(a.pinned_sha256 || '').slice(0, 12) + '…' : '';
      const note = el('div', { cls: 'stack', attrs: { 'aria-live': 'polite' } });
      const chk = el('button', { cls: 'btn sm', type: 'button', text: 'Yeni sürüm var mı?', disabled: !a.supported, on: { click: async () => {
        const x = await SB.api('/api/v2/apps/update', { id: a.id }); const u = x && x.update;
        if (!u) { note.replaceChildren(el('div', { text: (x && x.error) || 'Denetlenemedi' })); return; }
        if (!u.available) { note.replaceChildren(el('div', { text: 'Güncel' + (u.error ? ' (denetim hatası: ' + u.error + ')' : '') })); return; }
        const ok = el('button', { cls: 'btn sm', type: 'button', text: 'Bu sürümü kabul et', disabled: !u.digest, on: { click: async () => {
          const y = await SB.api('/api/v2/apps/accept', { id: a.id, version: u.latest }); SB.toast(y && y.message || (y && y.error) || 'Tamam'); paintApps(); } } });
        const no = el('button', { cls: 'btn sm', type: 'button', text: 'Vazgeç', on: { click: () => note.replaceChildren() } });
        const link = el('a', { text: 'Değişiklik notları', attrs: { href: u.notes_url, target: '_blank', rel: 'noopener noreferrer' } });
        note.replaceChildren(el('div', { cls: 'card' }, [
          el('strong', { text: 'Yeni sürüm: ' + u.latest + ' (kendiliğinden kurulmaz)' }), el('div', {}, [link]),
          el('div', { text: 'Dosya: ' + (u.asset || '?') }), el('div', { text: 'SHA-256 (yayıncı): ' + (u.digest || 'okunamadı') }),
          el('div', { text: 'Kabul edersen bu sürüm ve özet senin adına sabitlenir; kurmak için: sb apps install ' + a.id + ' --force' }),
          el('div', { cls: 'row' }, [ok, no])]));
      } } });
      return el('div', { cls: 'card', attrs: { 'data-app': a.id } }, [
        el('strong', { text: a.title || a.name }), el('div', { text: state }), el('div', { text: sync }), pin ? el('div', { text: pin }) : null,
        el('div', { cls: 'row' }, [open, syn, chk]), note]);
    }));
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
      appsBox = el('div', { cls: 'stack', attrs: { 'aria-label': 'Uygulamalar' } });
      root.append(el('div', { cls: 'sbv stack' }, [el('p', { text: 'Güncelleme, sağlık, günlük işler, uygulamalar (ClipBoardLine, Nashi) ve model ısıtma sırayla çalışır.' }), go, box, appsBox]));
      poll();
      paintApps();
      return () => { box = null; appsBox = null; if (timer) { clearTimeout(timer); timer = null; } };
    }
  });
  SB.registerView('app-settings', {
    title: 'Uygulama ayarları', icon: 'settings',
    render(root) {
      root.append(el('div', { cls: 'sbv stack' }, [
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
