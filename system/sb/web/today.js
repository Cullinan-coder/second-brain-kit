/* "Bugün" (varsayılan ilk ekran) ve "Kaynaklar" görünümleri + üst çubuktaki bayat kaynak rozeti.
   Uçlar: GET /api/v2/today, GET /api/v2/freshness (salt okunur; telefonda mail/onay ayrıntısı kırpılmış gelir).
   Ham HTML ataması yok (yalnız textContent / createElement). Görünüm açıkken 60 sn'de bir yenilenir. */
(function () {
  'use strict';
  const REFRESH_MS = 60000;
  const INBOX_REL = '00-Inbox/İçe aktar/';
  const MODE = { auto: 'otomatik', export: 'dışa aktarma', manual: 'elle' };
  const STATE = { taze: 'ok', eskiyor: 'warn', bayat: 'danger', 'hiç': '' };

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
  async function call(path) {
    try { const r = await window.SB.api(path); return r == null ? { error: 'boş yanıt' } : r; }
    catch (e) { return { error: String(e && e.message || e) }; }
  }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  const tr = function (o) { return o && typeof o === 'object' ? (o.tr || o.en || '') : (o || ''); };
  const when = function (iso) { return iso ? String(iso).replace('T', ' ').slice(0, 16) : '—'; };
  const ageText = function (d) { return d == null ? 'hiç alınmadı' : d < 1 ? 'bugün' : (Math.round(d * 10) / 10) + ' gün önce'; };

  function stateBadge(state) { return h('span', { class: 'badge ' + (STATE[state] || ''), text: state }); }

  function copyText(text) {
    function fallback() {
      const ta = h('textarea', { 'aria-hidden': 'true', style: 'position:fixed;opacity:0;left:-9999px' });
      ta.value = text; document.body.append(ta); ta.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      ta.remove(); return ok;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return fallback(); });
    }
    return Promise.resolve(fallback());
  }

  // ---------------------------------------------------------------- Bugün
  function skeleton() {
    const blocks = [];
    for (let i = 0; i < 4; i++) {
      blocks.push(h('div', { class: 'card today-card', 'aria-hidden': 'true' },
        h('div', { class: 'today-skel today-skel-t' }), h('div', { class: 'today-skel' }), h('div', { class: 'today-skel today-skel-s' })));
    }
    return h('div', { class: 'today-grid', role: 'status', 'aria-label': 'Yükleniyor' }, blocks);
  }
  function section(title, count, kids, extra) {
    return h('section', { class: 'card today-card', 'aria-label': title },
      h('div', { class: 'today-h' }, h('h3', { text: title }), count != null ? h('span', { class: 'badge ' + (count ? 'accent' : ''), text: String(count) }) : null),
      kids, extra || null);
  }
  function dueClass(n) { return n <= 0 ? 'today-d-now' : n === 1 ? 'today-d-soon' : 'today-d-week'; }
  function dueLabel(n) { return n <= 0 ? 'Bugün' : n === 1 ? 'Yarın' : n + ' gün'; }

  function deadlinesCard(t) {
    const week = (t.deadlines && t.deadlines.week) || [];
    const todayN = ((t.deadlines && t.deadlines.today) || []).length;
    const body = week.length
      ? h('ul', { class: 'today-list' }, week.map(function (r) {
        return h('li', { class: 'today-item' },
          h('span', { class: 'today-due ' + dueClass(r.days_left), text: dueLabel(r.days_left) }),
          h('span', { class: 'today-main' },
            h('span', { class: 'today-title', text: r.title || '' }),
            h('span', { class: 'muted today-sub', text: [String(r.date || '').slice(5), r.time, r.type].filter(Boolean).join(' · ') })));
      }))
      : h('p', { class: 'empty', text: 'Önümüzdeki 7 günde teslim, sınav ya da etkinlik yok.' });
    return section('Bugün ve 7 gün', week.length, body, week.length ? h('p', { class: 'muted today-foot', text: 'Bugün ' + todayN + ' · 7 günde ' + week.length }) : null);
  }

  function approvalsCard(t) {
    const a = t.approvals || { count: 0, oldest: [] };
    const body = a.count
      ? h('ul', { class: 'today-list' }, (a.oldest || []).map(function (r) {
        return h('li', { class: 'today-item' },
          h('span', { class: 'badge', text: r.kind || 'onay' }),
          h('span', { class: 'today-main' }, h('span', { class: 'today-title', text: r.title || '' }),
            h('span', { class: 'muted today-sub', text: when(r.created) })));
      }))
      : h('p', { class: 'empty', text: 'Bekleyen onay yok.' });
    const go = a.count ? h('div', { class: 'sbv-actions' }, h('button', { type: 'button', class: 'btn sm', text: 'Onaylar\'a git', onclick: function () { window.SB.openView('approvals'); } })) : null;
    const more = a.count > (a.oldest || []).length ? h('p', { class: 'muted today-foot', text: 'En eski ' + a.oldest.length + ' gösteriliyor.' }) : null;
    return section('Bekleyen onaylar', a.count, body, [more, go]);
  }

  function mailCard(t) {
    const m = t.mail || { count: 0, items: [] };
    let body;
    if (!m.count) body = h('p', { class: 'empty', text: 'Önemli okunmamış mail yok.' });
    else if (!(m.items || []).length) {
      const cats = Object.keys(m.by_category || {}).map(function (k) { return k + ' ' + m.by_category[k]; }).join(' · ');
      body = h('p', { class: 'muted', text: 'Başlıklar telefonda gizli.' + (cats ? ' (' + cats + ')' : '') });
    } else {
      body = h('ul', { class: 'today-list' }, m.items.map(function (r) {
        return h('li', { class: 'today-item' },
          h('span', { class: 'badge', text: r.category || 'mail' }),
          h('span', { class: 'today-main' }, h('span', { class: 'today-title today-clip', title: r.subject || '', text: r.subject || '' }),
            h('span', { class: 'muted today-sub today-clip', text: (r.from || '') + (r.date ? ' · ' + r.date : '') })));
      }));
    }
    return section('Önemli okunmamış mailler', m.count, body, m.count > (m.items || []).length && (m.items || []).length ? h('p', { class: 'muted today-foot', text: 'Son 7 gün; ilk ' + m.items.length + ' başlık.' }) : null);
  }

  function staleCard(t) {
    const s = t.stale_sources || { total: 0, items: [] };
    const body = s.total
      ? h('ul', { class: 'today-list' }, s.items.map(function (r) {
        return h('li', { class: 'today-item today-stale' },
          stateBadge(r.state),
          h('span', { class: 'today-main' },
            h('span', { class: 'today-title', text: tr(r.name) }),
            h('span', { class: 'muted today-sub', text: ageText(r.age_days) + ' · eşik ' + r.threshold_days + ' gün · ' + (MODE[r.mode] || r.mode) }),
            h('span', { class: 'today-hint', text: tr(r.hint) })));
      }))
      : h('p', { class: 'empty', text: 'Eskiyen kaynak yok.' });
    const acts = [h('button', { type: 'button', class: 'btn sm', text: 'Kaynaklar', onclick: function () { window.SB.openView('sources'); } })];
    if (!t.remote) {
      acts.push(h('button', { type: 'button', class: 'btn sm', text: 'İçe aktar klasör yolunu kopyala', title: 'Kasa içinde: ' + INBOX_REL, onclick: function () {
        copyText(INBOX_REL).then(function (ok) { toast(ok ? 'Kopyalandı: ' + INBOX_REL + ' (kasa içinde)' : 'Kopyalanamadı. Yol: ' + INBOX_REL, ok ? undefined : 'error'); });
      } }));
    }
    const more = s.total > s.items.length ? h('p', { class: 'muted today-foot', text: 'İlk ' + s.items.length + ' gösteriliyor; tümü Kaynaklar\'da.' }) : null;
    return section('Eskiyen kaynaklar', s.total, body, [more,
      s.total && !t.remote ? h('p', { class: 'muted today-foot', text: 'Yeni dışa aktarmayı kasadaki ' + INBOX_REL + ' klasörüne bırak.' }) : null,
      h('div', { class: 'sbv-actions' }, acts)]);
  }

  function failedCard(t) {
    const f = t.last_failed_step;
    if (!f) return null;
    return h('section', { class: 'card today-card today-fail', 'aria-label': 'Son başarısız günlük adım' },
      h('div', { class: 'today-h' }, h('h3', { text: 'Son başarısız günlük adım' }), h('span', { class: 'badge danger', text: 'kod ' + f.rc })),
      h('p', { class: 'today-title', text: f.name + ' · ' + when(f.ts) }),
      f.tail ? h('pre', { class: 'pre today-tail', text: f.tail }) : null);
  }

  function todayView(el) {
    const wrap = h('div', { class: 'sbv stack today' });
    el.replaceChildren(wrap);
    let alive = true, loaded = false, busy = false, timer = null;

    function head(t, err) {
      const d = t && t.date ? t.date : '';
      return h('div', { class: 'sbv-head today-head' },
        h('div', null, h('h2', { text: 'Bugün' }), h('div', { class: 'muted', text: d + (t && t.generated ? ' · güncellendi ' + String(t.generated).slice(11, 16) : '') })),
        h('div', { class: 'row' },
          h('button', { type: 'button', class: 'btn sm', text: 'Yenile', onclick: function () { load(true); } }),
          h('button', { type: 'button', class: 'btn primary sm', text: 'Sohbete geç', onclick: function () { window.SB.closeView(); } })),
        err ? h('p', { role: 'alert', class: 'today-err', text: err }) : null);
    }
    async function load(manual) {
      if (busy) return;
      busy = true;
      if (!loaded) wrap.replaceChildren(head(null), skeleton());
      const t = await call('/api/v2/today');
      busy = false;
      if (!alive) return;
      if (t.error) {
        if (loaded && !manual) { const old = wrap.querySelector('.today-err'); if (!old) wrap.prepend(h('p', { role: 'alert', class: 'today-err', text: 'Yenilenemedi: ' + t.error })); return; }
        wrap.replaceChildren(head(null), h('div', { class: 'card today-card', role: 'alert' }, h('h3', { text: 'Bugün yüklenemedi' }), h('p', { text: t.error }),
          h('button', { type: 'button', class: 'btn sm', text: 'Yeniden dene', onclick: function () { loaded = false; load(true); } })));
        return;
      }
      loaded = true;
      wrap.replaceChildren(head(t), h('div', { class: 'today-grid' }, [deadlinesCard(t), approvalsCard(t), mailCard(t), staleCard(t), failedCard(t)]));
    }
    load();
    timer = setInterval(function () { if (!document.hidden && alive) load(); }, REFRESH_MS);
    return function () { alive = false; if (timer) clearInterval(timer); };
  }

  // ---------------------------------------------------------------- Kaynaklar
  function sourcesView(el) {
    const wrap = h('div', { class: 'sbv stack today' });
    el.replaceChildren(wrap);
    let alive = true, data = null, onlyBad = false, timer = null, busy = false;
    const body = h('div', { class: 'stack' });
    const chk = h('input', { type: 'checkbox', id: 'src-only', onchange: function () { onlyBad = chk.checked; paint(); } });
    const bar = h('div', { class: 'sbv-toolbar' },
      h('label', { class: 'row', for: 'src-only' }, chk, h('span', { text: 'Yalnız sorunlu (eskiyor, bayat, hiç)' })),
      h('button', { type: 'button', class: 'btn sm', text: 'Yenile', onclick: function () { load(); } }));
    wrap.append(h('div', { class: 'sbv-head' }, h('h2', { text: 'Kaynaklar' }),
      h('span', { class: 'muted', text: 'Her kaynağın son başarılı güncellemesi ve ne zaman eskidiği.' })), bar, body);

    function paint() {
      if (!data) return;
      const all = data.sources || [];
      const rows = onlyBad ? all.filter(function (s) { return s.state !== 'taze'; }) : all;
      const c = data.counts || {};
      const sum = h('p', { class: 'muted', role: 'status', text: 'Taze ' + (c.taze || 0) + ' · eskiyor ' + (c.eskiyor || 0) + ' · bayat ' + (c.bayat || 0) + ' · hiç ' + (c['hiç'] || 0) });
      if (!all.length) { body.replaceChildren(h('p', { class: 'empty', text: 'Etkin kaynak yok (henüz bir şey içe aktarılmadı).' })); return; }
      if (!rows.length) { body.replaceChildren(sum, h('p', { class: 'empty', text: 'Sorunlu kaynak yok.' })); return; }
      const th = ['Kaynak', 'Mod', 'Son güncelleme', 'Eşik', 'Durum', 'İpucu'];
      const tbl = h('table', { class: 'table today-table' },
        h('thead', null, h('tr', null, th.map(function (x) { return h('th', { scope: 'col', text: x }); }))),
        h('tbody', null, rows.map(function (s) {
          return h('tr', { class: 'st-' + s.state },
            h('td', { 'data-label': th[0] }, h('strong', { text: tr(s.name) })),
            h('td', { 'data-label': th[1], text: MODE[s.mode] || s.mode }),
            h('td', { 'data-label': th[2], text: s.last ? when(s.last) + ' (' + ageText(s.age_days) + ')' : 'hiç alınmadı' }),
            h('td', { 'data-label': th[3], text: s.threshold_days + ' gün' }),
            h('td', { 'data-label': th[4] }, stateBadge(s.state)),
            h('td', { 'data-label': th[5], text: tr(s.hint) }));
        })));
      body.replaceChildren(sum, h('div', { class: 'today-tablewrap' }, tbl));
    }
    async function load() {
      if (busy) return; busy = true;
      if (!data) body.replaceChildren(skeleton());
      const r = await call('/api/v2/freshness');
      busy = false;
      if (!alive) return;
      if (r.error) {
        if (data) return;
        body.replaceChildren(h('div', { class: 'card today-card', role: 'alert' }, h('h3', { text: 'Kaynaklar yüklenemedi' }), h('p', { text: r.error }),
          h('button', { type: 'button', class: 'btn sm', text: 'Yeniden dene', onclick: function () { load(); } })));
        return;
      }
      data = r; badge(r); paint();
    }
    load();
    timer = setInterval(function () { if (!document.hidden && alive) load(); }, REFRESH_MS);
    return function () { alive = false; if (timer) clearInterval(timer); };
  }

  // ---------------------------------------------------------------- üst çubuk rozeti
  function badge(r) {
    const b = document.getElementById('src-badge'), btn = document.getElementById('btn-sources');
    if (!b || !btn) return;
    const n = (r && r.counts && r.counts.bayat) || 0;
    btn.hidden = !n; b.hidden = !n; b.textContent = n > 9 ? '9+' : String(n || '');
    btn.setAttribute('aria-label', 'Kaynaklar' + (n ? ' (' + n + ' bayat)' : ''));
    btn.title = n ? n + ' bayat kaynak' : 'Kaynaklar';
  }
  async function refreshBadge() {
    if (!window.SB || !window.SB.has || !window.SB.has('/api/v2/freshness')) return;
    const r = await call('/api/v2/freshness');
    if (!r.error) badge(r);
  }

  function homeIsToday() {
    try { return !(window.SB.settings && window.SB.settings.get('home', 'today') === 'chat'); } catch (e) { return true; }
  }
  function viewOpen() { const v = document.getElementById('view'); return !!(v && !v.hidden); }

  function register() {
    const SB = window.SB;
    SB.registerView('today', { title: 'Bugün', icon: 'calendar', render: todayView });
    SB.registerView('sources', { title: 'Kaynaklar', icon: 'refresh', render: sourcesView });
    const btn = document.getElementById('btn-sources');
    if (btn) btn.addEventListener('click', function () { SB.openView('sources'); });
    if (SB.bus) {
      SB.bus.on('ready', function () {
        refreshBadge();
        // varsayılan ilk ekran: Bugün (başka bir görünüm zaten açıldıysa ona dokunma)
        if (SB.has('/api/v2/today') && homeIsToday() && !viewOpen() && !/[?&](shared|queued)=/.test(location.search)) SB.openView('today');
      });
      SB.bus.on('approval', refreshBadge);
    }
    setInterval(function () { if (!document.hidden) refreshBadge(); }, REFRESH_MS);
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
