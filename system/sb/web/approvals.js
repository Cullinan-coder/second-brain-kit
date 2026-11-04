/* Tek "Onaylar" görünümü ve sayacı (D-30): sohbet kartları, otomasyon ve tarih adayları aynı depodan (GET /api/v2/approvals).
   Mevcut bileşen sınıfları: .prop/.prop-h/.prop-k/.prop-btns (sohbet onay kartı), .bell-wrap/.bell-badge (sayaç), .sbv/.stack/.muted.
   Ham HTML ataması yok. Telefonda yalnız kendi kartların görünür; komut/WhatsApp/gece/silme kartları yalnız bilgisayardan onaylanır. */
(function () {
  'use strict';
  const KIND = { takvim: 'Takvim', 'takvim-sil': 'Takvim silme', komut: 'Komut', whatsapp: 'WhatsApp (onaylanınca gönderilir)', gece: 'Gece koşusu',
    eylem: 'Eylem', kasa: 'Kasa', unut: 'Unutma', tarih: 'Tarih adayı' };
  const ORIGIN = { sohbet: 'sohbet', otomasyon: 'otomasyon', tarih: 'mail/SMS tarihi' };

  function h(tag, attrs) {
    const e = document.createElement(tag);
    for (const k in (attrs || {})) {
      const v = attrs[k];
      if (k === 'text') e.textContent = v;
      else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), v);
      else if (v != null && v !== false) e.setAttribute(k, v === true ? '' : v);
    }
    for (let i = 2; i < arguments.length; i++) {
      const c = arguments[i];
      if (c == null || c === false) continue;
      (Array.isArray(c) ? c : [c]).forEach(function (x) { if (x != null) e.append(x.nodeType ? x : document.createTextNode(String(x))); });
    }
    return e;
  }
  async function call(path, body) {
    try { const r = await window.SB.api(path, body); return r == null ? { error: 'boş yanıt' } : r; }
    catch (e) { return { error: String(e && e.message || e) }; }
  }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }

  // sayaç: başlıktaki düğme + rozet (bildirim zilinin sınıfları)
  function badge(n) {
    const b = document.getElementById('appr-badge'), btn = document.getElementById('btn-approvals');
    if (!b || !btn) return;
    btn.hidden = false;
    b.hidden = !n; b.textContent = n > 9 ? '9+' : String(n || '');
    btn.setAttribute('aria-label', 'Onaylar' + (n ? ' (' + n + ' bekliyor)' : ''));
  }
  async function refreshCount() {
    if (!window.SB || !window.SB.has || !window.SB.has('/api/v2/approvals')) return;
    const r = await call('/api/v2/approvals');
    if (!r.error) badge(r.count != null ? r.count : (r.approvals || []).length);
  }

  function card(a, reload) {
    const kind = KIND[a.kind] || a.kind || 'Onay';
    const meta = (ORIGIN[a.origin] || a.origin || '') + (a.source === 'telefon' ? ' · telefondan' : '') + (a.created ? ' · ' + String(a.created).replace('T', ' ').slice(0, 16) : '');
    const res = h('div', { class: 'prop-res', role: 'status' });
    const yes = h('button', { type: 'button', class: 'btn primary', text: 'Onayla', disabled: !a.can_decide || !a.runnable });
    const no = h('button', { type: 'button', class: 'btn', text: 'İptal' });
    async function act(ok) {
      yes.disabled = no.disabled = true;
      const r = await call('/api/v2/approvals/decide', { id: a.id, ok: ok });
      if (r.error) { toast('İşlem yapılamadı: ' + r.error, 'error'); res.textContent = r.error; no.disabled = false; return; }
      toast(r.message || (ok ? 'Onaylandı' : 'İptal edildi'));
      if (window.SB && window.SB.bus) window.SB.bus.emit('approval', { id: a.id, ok: ok, message: r.message });
      reload();
    }
    yes.addEventListener('click', function () { act(true); });
    no.addEventListener('click', function () { act(false); });
    const why = !a.runnable ? 'Sunucu yeniden başladı: bu kart artık yürütülemez, isteği yeniden yap.'
      : !a.can_decide ? 'Bu kart yalnız bilgisayardaki asistandan onaylanır.' : '';
    return h('section', { class: 'prop', 'aria-label': 'Onay gerekli: ' + (a.title || '') },
      h('div', { class: 'prop-h' }, h('div', null, h('div', { class: 'prop-k', text: kind + ' · ' + meta }), h('div', { text: a.title || '' }))),
      a.detail ? h('details', { open: String(a.detail).length < 160 }, h('summary', { text: 'Ayrıntı' }), h('pre', { text: a.detail })) : null,
      why ? h('p', { class: 'muted', text: why }) : null,
      h('div', { class: 'prop-btns' }, yes, no), res);
  }

  function view(el) {
    const wrap = h('div', { class: 'sbv stack' });
    el.replaceChildren(wrap);
    async function load() {
      wrap.replaceChildren(h('p', { class: 'muted', role: 'status', text: 'Yükleniyor…' }));
      const r = await call('/api/v2/approvals');
      if (r.error) { wrap.replaceChildren(h('p', { role: 'alert', text: r.error })); return; }
      const list = r.approvals || [];
      badge(r.count != null ? r.count : list.length);
      const items = list.length ? list.map(function (a) { return card(a, load); }) : [h('p', { class: 'empty', text: 'Bekleyen onay yok.' })];
      wrap.replaceChildren.apply(wrap, [h('h2', { text: 'Onaylar (' + list.length + ')' }),
        h('p', { class: 'muted', text: 'Onay bekleyen her şey burada: sohbet kartları (komut, takvim, WhatsApp…), otomasyonlar ve mailden çıkarılan tarih adayları. '
          + 'Tarih adayları Obsidian\'da 00-Inbox/onay-bekleyenler.md içinde de görünür; orada [x] yapmak da onaydır.' })].concat(items));
    }
    load();
  }

  function register() {
    window.SB.registerView('approvals', { title: 'Onaylar', icon: 'check', render: view });
    const btn = document.getElementById('btn-approvals');
    if (btn) btn.addEventListener('click', function () { window.SB.openView('approvals'); });
    if (window.SB.bus) {
      window.SB.bus.on('ready', refreshCount);
      window.SB.bus.on('approval', refreshCount);
      window.SB.bus.on('message', function (m) { if (m && m.role === 'assistant') refreshCount(); });
    }
    setInterval(function () { if (!document.hidden) refreshCount(); }, 30000);
    refreshCount();
  }
  if (window.SB && window.SB.registerView) register();
  else {
    let done = false;
    const go = function () { if (!done && window.SB && window.SB.registerView) { done = true; register(); } };
    document.addEventListener('DOMContentLoaded', go);
    window.addEventListener('load', go);
    const t = setInterval(function () { go(); if (done) clearInterval(t); }, 200);
    setTimeout(function () { clearInterval(t); }, 15000);
  }
})();
