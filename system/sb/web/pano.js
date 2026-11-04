/* Pano görünümü: yerel pano geçmişi (görsel / metin / bağlantı rafları). Ham HTML yok; yalnız DOM düğümleri. */
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
  const SHELVES = [['image', 'Görseller'], ['text', 'Metinler'], ['link', 'Bağlantılar']];
  const failed = (r) => !r || (typeof r === 'object' && !Array.isArray(r) && r.error);
  const q = (o) => Object.keys(o).filter((k) => o[k] !== '' && o[k] != null).map((k) => k + '=' + encodeURIComponent(o[k])).join('&');
  const ago = (t) => {
    const s = Math.max(0, Date.now() / 1000 - t);
    return s < 60 ? 'şimdi' : s < 3600 ? Math.floor(s / 60) + ' dk' : s < 86400 ? Math.floor(s / 3600) + ' sa' : Math.floor(s / 86400) + ' gün';
  };

  let root = null, st = null, state = null, urls = [];

  async function blobUrl(id, thumb) {                           // X-SB başlığı gerektiği için img.src yerine blob
    try {
      const r = await fetch('/api/v2/pano/image?' + q({ id, thumb: thumb ? 1 : '' }), { headers: { 'X-SB': '1' } });
      if (!r.ok) return '';
      const u = URL.createObjectURL(await r.blob()); urls.push(u); return u;
    } catch (e) { return ''; }
  }

  async function load() {
    st = await SB.api('/api/v2/pano/status');
    if (failed(st)) st = null;
    else if (st.enabled) {
      const query = state.q.trim();
      const res = await Promise.all(SHELVES.map(([k]) => query
        ? SB.api('/api/v2/pano/search?' + q({ q: query, kind: k, per: 60 }))
        : SB.api('/api/v2/pano/list?' + q({ kind: k, per: 60 }))));
      state.data = {};
      SHELVES.forEach(([k], i) => { state.data[k] = failed(res[i]) ? [] : res[i].items; });
    }
    if (root) paint();
  }

  const rowsOf = () => SHELVES.map(([k]) => (state.data && state.data[k]) || []);
  const cur = () => (rowsOf()[state.r] || [])[state.c] || null;

  async function act(kind, it) {
    if (!it) return;
    let r;
    if (kind === 'copy') { r = await SB.api('/api/v2/pano/copy', { id: it.id }); if (!failed(r)) SB.toast('Panoya kopyalandı', 'ok'); }
    if (kind === 'pin') r = await SB.api('/api/v2/pano/pin', { id: it.id });
    if (kind === 'remove') {
      r = await SB.api('/api/v2/pano/remove', { id: it.id });
      if (!failed(r)) SB.toast('Kaldırıldı', 'info', { action: { label: 'Geri al', run: async () => { await SB.api('/api/v2/pano/restore', {}); load(); } } });
    }
    if (failed(r)) return SB.toast('Olmadı: ' + (r && r.error), 'error');
    if (kind !== 'copy') load();
  }

  async function preview(it) {
    if (!it) return;
    const full = await SB.api('/api/v2/pano/item?' + q({ id: it.id }));
    if (failed(full)) return SB.toast('Önizlenemedi', 'error');
    const body = it.kind === 'image' ? el('img', { alt: it.name || 'Pano görseli' }) : el('pre', { cls: 'pre', text: full.text });
    if (it.kind === 'image') blobUrl(it.id, false).then((u) => { if (u) body.src = u; });
    const close = () => dlg.remove();
    const dlg = el('div', {
      cls: 'sbv-modal', attrs: { role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Önizleme' },
      on: { click: (e) => { if (e.target === dlg) close(); }, keydown: (e) => { if (e.key === 'Escape') { e.stopPropagation(); close(); } } }
    }, [el('div', { cls: 'sbv-modal-card pano-prev' }, [el('div', { cls: 'sbv-modal-body stack' }, [body, el('div', { cls: 'sbv-actions' }, [
      el('button', { cls: 'btn primary', type: 'button', text: 'Kopyala', on: { click: () => act('copy', it) } }),
      el('button', { cls: 'btn', type: 'button', text: 'Kapat', on: { click: close } })])])])]);
    root.append(dlg);
    dlg.querySelector('button').focus();
  }

  async function setEnabled(on, images) {
    const patch = { enabled: on };
    if (images !== undefined) patch.collect_images = images;
    const r = await SB.api('/api/v2/pano/settings', patch);
    if (failed(r)) return SB.toast('Ayar kaydedilemedi: ' + (r && r.error), 'error');
    load();
  }

  function card(it, r, c) {
    const body = el('div', { cls: 'pano-body' });
    if (it.kind === 'image') {
      const im = el('img', { alt: it.name || 'Pano görseli' }); body.append(im);
      blobUrl(it.id, true).then((u) => { if (u) im.src = u; });
    } else body.textContent = it.name ? it.name + '\n' + it.text : it.text;
    const tags = it.tags.length ? ' · #' + it.tags.join(' #') : '';
    return el('button', {
      cls: 'card pano-card' + (it.pinned ? ' pinned' : '') + (state.r === r && state.c === c ? ' sel' : ''), type: 'button',
      attrs: { 'data-id': it.id, 'aria-label': (it.pinned ? 'Sabit. ' : '') + (it.name || it.text.slice(0, 60) || 'görsel') },
      on: { click: () => { state.r = r; state.c = c; act('copy', it); }, focus: () => { state.r = r; state.c = c; } }
    }, [body, el('div', { cls: 'pano-meta', text: (it.pinned ? 'Sabit · ' : '') + ago(it.updated) + (it.folder ? ' · ' + it.folder : '') + tags })]);
  }

  function paintSel() {
    root.querySelectorAll('.pano-card.sel').forEach((n) => n.classList.remove('sel'));
    const it = cur(); if (!it) return;
    const n = root.querySelector('.pano-row:not(.pano-pins) .pano-card[data-id="' + it.id + '"]') || root.querySelector('.pano-card[data-id="' + it.id + '"]');
    if (n) { n.classList.add('sel'); n.focus(); }
  }

  function paint() {
    urls.forEach((u) => URL.revokeObjectURL(u)); urls = [];
    const kids = [el('div', { cls: 'sbv-head' }, [el('h2', { text: 'Kopya geçmişi' }),
      el('span', { cls: 'sbv-muted', text: st && st.enabled ? 'Yerel kayıt · sır gibi görünen metin saklanmaz' : '' })])];
    const mount = () => root.replaceChildren(el('div', { cls: 'sbv stack' }, kids));
    if (!st) { kids.push(el('div', { cls: 'empty' }, el('p', { text: 'Pano sunucusuna ulaşılamadı.' }))); return mount(); }
    if (st.module === false) {
      kids.push(el('div', { cls: 'card stack' }, [
        el('h3', { text: 'Kopya geçmişi modülü kapalı' }),
        el('p', { text: 'Uygulama ayarları → Özellikler sekmesinden «Kopya geçmişi (Pano)» modülünü aç ya da terminalde: sb features --on pano' })]));
      return mount();
    }
    if (!st.enabled) {
      kids.push(el('div', { cls: 'card stack' }, [
        el('h3', { text: 'Pano geçmişi kapalı' }),
        el('p', { text: 'Açarsan kopyaladığın metin ve bağlantılar yalnız bu bilgisayarda saklanır; parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez. İstediğin zaman kapatabilirsin.' }),
        st.backend_ok ? null : el('p', { cls: 'note-warn', text: st.note || 'Bu sistemde pano izleyici kullanılamıyor.' }),
        el('div', { cls: 'sbv-actions' }, [el('button', { cls: 'btn primary', type: 'button', text: 'Aç', on: { click: () => setEnabled(true) } })])]));
      return mount();
    }
    const search = el('input', {
      type: 'search', value: state.q, placeholder: 'Ara ( / )', attrs: { 'aria-label': 'Panoda ara', id: 'pano-q' },
      on: { keydown: (e) => { e.stopPropagation(); if (e.key === 'Enter') { state.q = e.target.value; state.r = 0; state.c = 0; load(); } if (e.key === 'Escape') e.target.blur(); } }
    });
    kids.push(el('div', { cls: 'sbv-toolbar' }, [search,
      el('label', { cls: 'row' }, [el('input', { type: 'checkbox', checked: !!st.collect_images, on: { change: (e) => setEnabled(true, e.target.checked) } }), el('span', { text: 'Görselleri de topla' })]),
      el('button', { cls: 'btn sm', type: 'button', text: 'Kapat', on: { click: () => setEnabled(false) } })]));
    if (st.error) kids.push(el('p', { cls: 'note-warn', text: 'İzleyici hatası: ' + st.error }));
    if (!st.running) kids.push(el('p', { cls: 'note-warn', text: 'İzleyici çalışmıyor' + (st.note ? ': ' + st.note : '.') + ' Terminalde "sb pano watch" ile başlatabilirsin.' }));
    const rows = rowsOf();
    const pins = [];
    rows.forEach((items, r) => items.forEach((it, c) => { if (it.pinned) pins.push([it, r, c]); }));
    if (pins.length) kids.push(el('div', { cls: 'pano-shelf' }, [el('h3', { text: 'Sabitler' }), el('div', { cls: 'pano-row pano-pins' }, pins.map((p) => card(p[0], p[1], p[2])))]));
    SHELVES.forEach(([k, title], r) => {
      const items = rows[r];
      const msg = state.q ? 'Eşleşme yok.' : (k === 'image' && !st.collect_images) ? 'Görsel toplama kapalı.' : 'Henüz bir şey yok. Bir şey kopyala, burada belirsin.';
      kids.push(el('div', { cls: 'pano-shelf' }, [el('h3', { text: title + ' (' + ((st.counts && st.counts[k]) || 0) + ')' }),
        items.length ? el('div', { cls: 'pano-row', attrs: { role: 'list' } }, items.map((it, c) => card(it, r, c))) : el('div', { cls: 'empty' }, el('p', { text: msg }))]));
    });
    kids.push(el('p', { cls: 'sbv-muted', text: '←/→ gez · ↑/↓ raf · Enter kopyala · P sabitle · S kaldır · Boşluk önizle · / ara' }));
    mount();
    if (state.focus) { state.focus = false; paintSel(); }
  }

  function onKey(e) {
    if (!root || !root.isConnected || e.ctrlKey || e.metaKey || e.altKey) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName || '') || root.querySelector('.sbv-modal')) return;
    const rows = rowsOf(), k = e.key;
    const clamp = () => { state.c = Math.max(0, Math.min(state.c, (rows[state.r] || []).length - 1)); };
    if (k === 'ArrowRight') { state.c++; clamp(); }
    else if (k === 'ArrowLeft') { state.c--; clamp(); }
    else if (k === 'ArrowDown' || k === 'ArrowUp') {
      const d = k === 'ArrowDown' ? 1 : -1; let r = state.r + d;
      while (r >= 0 && r < rows.length && !rows[r].length) r += d;
      if (r >= 0 && r < rows.length) state.r = r;
      clamp();
    }
    else if (k === 'Enter') act('copy', cur());
    else if (k === 'p' || k === 'P') { state.focus = true; act('pin', cur()); }
    else if (k === 's' || k === 'S') { state.focus = true; act('remove', cur()); }
    else if (k === ' ') preview(cur());
    else if (k === '/') { const i = root.querySelector('#pano-q'); if (i) i.focus(); }
    else return;
    e.preventDefault();
    if (k !== 'p' && k !== 'P' && k !== 's' && k !== 'S') paintSel();
  }

  SB.registerView('pano', {
    title: 'Kopya geçmişi', icon: 'copy',
    render(r) {
      root = r; state = { q: '', r: 0, c: 0, data: null, focus: false };
      document.addEventListener('keydown', onKey);
      load();
      return () => { document.removeEventListener('keydown', onKey); urls.forEach((u) => URL.revokeObjectURL(u)); urls = []; root = null; };
    }
  });
})();
