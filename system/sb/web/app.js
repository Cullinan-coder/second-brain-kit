/* Asistan arayüz kabuğu (Faz 2 · Paket D). Tek ad alanı: window.SB. Ham HTML yok: tüm metin DOM düğümleriyle kurulur. */
(function () {
  'use strict';

  /* ---------- yardımcılar ---------- */
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  function el(tag, props, kids) {
    const n = document.createElement(tag);
    if (props) {
      for (const k in props) {
        const v = props[k];
        if (v == null || v === false) continue;
        if (k === 'cls') n.className = v;
        else if (k === 'text') n.textContent = v;
        else if (k === 'dataset') Object.assign(n.dataset, v);
        else if (k === 'on') for (const e in v) n.addEventListener(e, v[e]);
        else if (k === 'attrs') for (const a in v) n.setAttribute(a, v[a]);
        else n[k] = v;
      }
    }
    if (kids) for (const c of [].concat(kids)) if (c != null && c !== false) n.append(c);
    return n;
  }
  const rand = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
  const meta = (n) => { const m = document.querySelector('meta[name="' + n + '"]'); return m ? m.content : ''; };

  /* ---------- ikonlar (satır içi SVG) ---------- */
  const ICONS = {
    menu: 'M4 6h16M4 12h16M4 18h16', plus: 'M12 5v14M5 12h14', search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-4.3-4.3',
    bell: 'M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.9 1.9 0 0 0 3.4 0',
    sun: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
    moon: 'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z', auto: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 3v18',
    command: 'M15 6v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3',
    send: 'M22 2L11 13M22 2l-7 20-4-9-9-4z',
    clip: 'M21 11l-9.2 9.2a5 5 0 0 1-7.1-7.1l9.2-9.2a3.3 3.3 0 0 1 4.7 4.7l-9.2 9.2a1.7 1.7 0 0 1-2.4-2.4l8.5-8.5',
    mic: 'M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3zM19 10v2a7 7 0 0 1-14 0v-2M12 19v3',
    phone: 'M7 2h10a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1zM11 18h2',
    settings: 'M4 6h10M18 6h2M4 12h2M10 12h10M4 18h12M20 18h0M14 4v4M8 10v4M16 16v4',
    back: 'M19 12H5M12 19l-7-7 7-7', x: 'M18 6L6 18M6 6l12 12', pin: 'M12 17v5M9 3h6l-1 7 3 3v2H7v-2l3-3z',
    more: 'M12 5h.01M12 12h.01M12 19h.01', copy: 'M9 9h11v11H9zM5 15H4V4h11v1',
    up: 'M7 10v11H3V10zM7 10l4-8a3 3 0 0 1 3 3v4h6a2 2 0 0 1 2 2l-2 8a2 2 0 0 1-2 2H7',
    down: 'M17 14V3h4v11zM17 14l-4 8a3 3 0 0 1-3-3v-4H4a2 2 0 0 1-2-2l2-8a2 2 0 0 1 2-2h11',
    edit: 'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z', refresh: 'M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5',
    note: 'M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM14 3v6h6M8 13h8M8 17h5', check: 'M5 13l4 4L19 7',
    mail: 'M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zM3 7l9 6 9-6',
    chat: 'M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z', chev: 'M9 6l6 6-6 6',
    calendar: 'M5 4h14a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM4 9h16M8 2v4M16 2v4',
    terminal: 'M4 17l6-6-6-6M12 19h8', archive: 'M3 4h18v4H3zM5 8v12h14V8M10 12h4',
    spark: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z', grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
    stop: 'M6 6h12v12H6z', info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 11v5M12 8h.01'
  };
  function icon(name) {
    const NS = 'http://www.w3.org/2000/svg';
    const s = document.createElementNS(NS, 'svg');
    s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('class', 'ic'); s.setAttribute('aria-hidden', 'true');
    const p = document.createElementNS(NS, 'path'); p.setAttribute('d', ICONS[name] || ICONS.spark);
    s.appendChild(p); return s;
  }
  const setIcon = (node, name) => { node.dataset.icon = name; node.replaceChildren(icon(name)); };

  /* ---------- ayarlar / olay yolu ---------- */
  const mem = {};
  const settings = {
    get(k, d) { try { const v = localStorage.getItem('sb.' + k); if (v != null) return JSON.parse(v); } catch (e) { if (k in mem) return mem[k]; } return k in mem ? mem[k] : d; },
    set(k, v) { mem[k] = v; try { localStorage.setItem('sb.' + k, JSON.stringify(v)); } catch (e) { /* kapalı olabilir */ } applySetting(k); bus.emit('settings', { key: k, value: v }); }
  };
  const handlers = {}; const fired = {};
  const bus = {
    on(evt, fn) { (handlers[evt] = handlers[evt] || []).push(fn); if (evt === 'ready' && fired.ready) setTimeout(() => safe(fn, fired.ready.data), 0); return () => bus.off(evt, fn); },
    off(evt, fn) { handlers[evt] = (handlers[evt] || []).filter((f) => f !== fn); },
    emit(evt, data) { if (evt === 'ready') fired.ready = { data }; (handlers[evt] || []).slice().forEach((f) => safe(f, data)); }
  };
  function safe(fn, a) { try { return fn(a); } catch (e) { console.error(e); } }

  /* ---------- SB çekirdeği ---------- */
  const SB = window.SB = {
    sid: settings.get('sid', '') || rand(),
    local: meta('sb-local') === '1',
    routes: new Set(),
    settings, bus, version: '0.6.0'
  };
  SB.model = meta('sb-model').indexOf('__') === 0 ? '' : meta('sb-model');
  SB.has = (p) => SB.routes.has(p);

  SB.api = async function api(path, body) {
    const post = body !== undefined;
    let url = path; const init = { headers: { 'X-SB': '1' } };
    if (post) {
      init.method = 'POST'; init.headers['Content-Type'] = 'application/json';
      const b = body && typeof body === 'object' && !Array.isArray(body) ? Object.assign({ sid: SB.sid }, body) : body;
      init.body = JSON.stringify(b);
    } else if (!/[?&]sid=/.test(path)) url += (path.indexOf('?') < 0 ? '?' : '&') + 'sid=' + encodeURIComponent(SB.sid);
    try {
      const r = await fetch(url, init);
      const txt = await r.text(); let j;
      try { j = JSON.parse(txt); } catch (e) { return { error: r.status === 401 ? 'Eşlenmemiş cihaz' : 'Geçersiz yanıt (' + r.status + ')', status: r.status }; }
      if (!r.ok && !(j && j.error)) return { error: 'HTTP ' + r.status, status: r.status };
      if (!r.ok && j && typeof j === 'object') j.status = r.status;
      return j;
    } catch (e) { return { error: 'Sunucuya ulaşılamadı: ' + (e && e.message || e) }; }
  };
  const api = SB.api;
  const failed = (r) => !r || (typeof r === 'object' && !Array.isArray(r) && r.error);

  /* ---------- güvenli markdown ---------- */
  const SAFE_URL = /^(https?:\/\/|obsidian:\/\/)/i;
  function linkNode(url, kids) {
    const a = document.createElement('a'); a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer';
    a.append(...kids); return a;
  }
  function inline(text, parent, noLink) {
    const re = /(`+)([\s\S]*?[^`])\1(?!`)|\*\*([^\n]+?)\*\*|(?<![\w*])\*([^\s*][^*\n]*?)\*(?![\w*])|(?<![\w_])_([^\s_][^_\n]*?)_(?![\w_])|\[([^\]\n]+)\]\(([^)\s]+)\)|(https?:\/\/[^\s<>]+)/g;
    let last = 0, m;
    while ((m = re.exec(text))) {
      if (m.index > last) parent.append(text.slice(last, m.index));
      last = re.lastIndex;
      if (m[2] != null) parent.append(el('code', { text: m[2] }));
      else if (m[3] != null) { const s = el('strong'); inline(m[3], s, noLink); parent.append(s); }
      else if (m[4] != null || m[5] != null) { const s = el('em'); inline(m[4] != null ? m[4] : m[5], s, noLink); parent.append(s); }
      else if (m[6] != null) {
        if (!noLink && SAFE_URL.test(m[7])) { const tmp = document.createDocumentFragment(); inline(m[6], tmp, true); parent.append(linkNode(m[7], [tmp])); }
        else parent.append(m[6] + ' (' + m[7] + ')');
      } else if (m[8] != null) {
        let u = m[8]; const tail = (u.match(/[.,;:!?)\]'"]+$/) || [''])[0];
        if (tail) { u = u.slice(0, -tail.length); last -= tail.length; re.lastIndex = last; }
        if (!noLink && SAFE_URL.test(u)) parent.append(linkNode(u, [u])); else parent.append(u);
      }
    }
    if (last < text.length) parent.append(text.slice(last));
  }
  function inlineLines(lines, parent) {
    lines.forEach((ln, i) => { if (i) parent.append(document.createElement('br')); inline(ln, parent); });
  }
  const R_FENCE = /^\s*```\s*([\w+-]*)\s*$/, R_H = /^(#{1,4})\s+(.*)$/, R_HR = /^\s*([-*_])(\s*\1){2,}\s*$/, R_LI = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/, R_BQ = /^\s*>\s?(.*)$/;
  function md(text) {
    const frag = document.createDocumentFragment();
    const lines = String(text == null ? '' : text).replace(/\r\n?/g, '\n').split('\n');
    let i = 0;
    const isStart = (l) => R_FENCE.test(l) || R_H.test(l) || R_HR.test(l) || R_LI.test(l) || R_BQ.test(l);
    while (i < lines.length) {
      const l = lines[i];
      if (!l.trim()) { i++; continue; }
      let m;
      if ((m = R_FENCE.exec(l))) {
        const buf = []; i++;
        while (i < lines.length && !/^\s*```\s*$/.test(lines[i])) buf.push(lines[i++]);
        i++;
        const code = el('code', { text: buf.join('\n') });
        if (m[1]) code.dataset.lang = m[1];
        frag.append(el('pre', null, code)); continue;
      }
      if ((m = R_H.exec(l))) { const h = el('h' + Math.min(4, m[1].length)); inline(m[2], h); frag.append(h); i++; continue; }
      if (R_HR.test(l)) { frag.append(document.createElement('hr')); i++; continue; }
      if (R_BQ.test(l)) {
        const buf = [];
        while (i < lines.length && R_BQ.test(lines[i])) buf.push(R_BQ.exec(lines[i++])[1]);
        const bq = el('blockquote'); inlineLines(buf, bq); frag.append(bq); continue;
      }
      if ((m = R_LI.exec(l))) {
        const ordered = /\d/.test(m[2]);
        const list = el(ordered ? 'ol' : 'ul');
        while (i < lines.length && (m = R_LI.exec(lines[i]))) {
          const li = el('li'); inline(m[3], li);
          // devam satırları (girintili)
          i++;
          while (i < lines.length && lines[i].trim() && /^\s{2,}\S/.test(lines[i]) && !R_LI.test(lines[i])) { li.append(document.createElement('br')); inline(lines[i].trim(), li); i++; }
          list.append(li);
        }
        frag.append(list); continue;
      }
      const buf = [];
      while (i < lines.length && lines[i].trim() && (buf.length === 0 || !isStart(lines[i]))) buf.push(lines[i++]);
      const p = el('p'); inlineLines(buf, p); frag.append(p);
    }
    return frag;
  }
  SB.md = md;

  /* ---------- bildirim kutusu (toast) ---------- */
  SB.toast = function (msg, kind, opts) {
    const box = $('#toasts'); if (!box) return;
    const t = el('div', { cls: 'toast ' + (kind || 'info'), attrs: { role: kind === 'error' ? 'alert' : 'status' } });
    t.append(el('span', { text: String(msg) }));
    if (opts && opts.action) t.append(el('button', { cls: 'btn sm', text: opts.action.label, on: { click: () => { safe(opts.action.run); t.remove(); } } }));
    box.append(t);
    setTimeout(() => t.remove(), kind === 'error' ? 8000 : 4500);
  };

  /* ---------- ayar uygulama (tema, vurgu, yazı boyutu) ---------- */
  const ACCENTS = [['blue', 'Mavi', '#1556e4'], ['green', 'Yeşil', '#137337'], ['orange', 'Turuncu', '#a14a08'], ['purple', 'Mor', '#7e22ce'], ['red', 'Kırmızı', '#be123c']];
  const FSCALE = { small: 0.9, medium: 1, large: 1.15, xlarge: 1.3 };
  const FONTS = [['small', 'Küçük'], ['medium', 'Normal'], ['large', 'Büyük'], ['xlarge', 'Çok büyük']];
  function applySetting(k) {
    const root = document.documentElement;
    if (!k || k === 'theme') {
      const t = settings.get('theme', 'system');
      if (t === 'light' || t === 'dark') root.setAttribute('data-theme', t); else root.removeAttribute('data-theme');
      syncThemeBtn();
    }
    if (!k || k === 'accent') {
      const a = settings.get('accent', 'blue');
      if (a && a !== 'blue') root.setAttribute('data-accent', a); else root.removeAttribute('data-accent');
    }
    if (!k || k === 'fontsize') root.style.setProperty('--fs', String(FSCALE[settings.get('fontsize', 'medium')] || 1));
  }
  function syncThemeBtn() {
    const b = $('#btn-theme'); if (!b) return;
    const t = settings.get('theme', 'system');
    setIcon(b, t === 'light' ? 'sun' : t === 'dark' ? 'moon' : 'auto');
    const lbl = 'Tema: ' + (t === 'light' ? 'açık' : t === 'dark' ? 'koyu' : 'otomatik');
    b.setAttribute('aria-label', lbl); b.title = lbl;
  }
  function cycleTheme() {
    const order = ['system', 'light', 'dark']; const cur = settings.get('theme', 'system');
    const next = order[(order.indexOf(cur) + 1) % 3]; settings.set('theme', next);
    SB.toast('Tema: ' + (next === 'light' ? 'açık' : next === 'dark' ? 'koyu' : 'otomatik'));
  }

  /* ---------- durum ---------- */
  const S = {
    busy: false, archived: false, q: '', title: 'Yeni sohbet', atts: [], cards: new Map(), cmds: [], clientCmds: new Map(),
    uploadSeq: 0, notifSeen: null, lastFocus: null
  };
  const views = new Map(); let curView = null, viewCleanup = null;
  let log, q, chipsBox;

  /* ---------- panolar, bağlantılar ---------- */
  function copyText(t) {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(t);
    return new Promise((res, rej) => {
      const ta = el('textarea', { value: t }); ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.append(ta); ta.select();
      try { document.execCommand('copy') ? res() : rej(new Error('kopyalanamadı')); } catch (e) { rej(e); } finally { ta.remove(); }
    });
  }
  function openLink(url) {
    if (!SAFE_URL.test(url)) return;
    const a = el('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }); a.style.display = 'none'; document.body.append(a); a.click(); a.remove();
  }
  const obsUrl = (path) => 'obsidian://open?vault=SecondBrain&file=' + encodeURIComponent(path);
  SB.openNote = (path) => openLink(obsUrl(path));
  SB.openLink = openLink;

  /* ---------- mesaj çizimi ---------- */
  const KIND_TR = { note: 'Not', mail: 'Mail', file: 'Dosya', chat: 'Sohbet', item: 'Öğe' };
  const KIND_IC = { note: 'note', mail: 'mail', file: 'clip', chat: 'chat', item: 'spark' };
  function srcCard(s) {
    const head = el('span', { cls: 'src-t' }, [icon(KIND_IC[s.kind] || 'spark'), el('span', { cls: 'tt', text: s.title || s.path || 'Kaynak' })]);
    const metaT = [KIND_TR[s.kind] || s.kind, s.date].filter(Boolean).join(' · ');
    const kids = [head, metaT ? el('span', { cls: 'src-m', text: metaT }) : null, s.snippet ? el('span', { cls: 'src-s', text: s.snippet }) : null];
    if (s.url && SAFE_URL.test(s.url)) {
      const a = el('a', { cls: 'src', href: s.url, target: '_blank', rel: 'noopener noreferrer', title: 'Obsidian\'da aç' }, kids);
      return a;
    }
    const b = el('button', { cls: 'src', type: 'button', attrs: { 'aria-expanded': 'false' } }, kids);
    b.addEventListener('click', () => b.setAttribute('aria-expanded', b.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'));
    return b;
  }
  function actBtn(name, label, fn, pressed) {
    const b = el('button', { cls: 'ibtn', type: 'button', title: label, attrs: { 'aria-label': label } }, icon(name));
    if (pressed !== undefined) b.setAttribute('aria-pressed', pressed ? 'true' : 'false');
    b.addEventListener('click', (e) => fn(b, e));
    return b;
  }
  function fmtTime(ts) {
    if (!ts) return '';
    const d = new Date(typeof ts === 'number' && ts < 1e12 ? ts * 1000 : ts); if (isNaN(d)) return '';
    return d.toLocaleString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  }
  function react(m, reaction, extra) {
    if (!SB.has('/api/v2/msg/react') || !m.id) return Promise.resolve();
    return api('/api/v2/msg/react', Object.assign({ id: m.id, reaction }, extra || {}));
  }
  function renderMsg(m) {
    const role = m.role === 'user' ? 'user' : m.role === 'tool' ? 'tool' : m.error ? 'error' : 'assistant';
    const wrap = el('article', { cls: 'msg ' + (role === 'error' ? 'assistant error' : role), attrs: { 'data-role': role } });
    wrap._m = m; if (m.id) wrap.dataset.id = m.id;
    wrap.append(el('span', { cls: 'sr', text: role === 'user' ? 'Sen: ' : role === 'tool' ? 'Araç: ' : 'Asistan: ' }));
    if (m.voice) wrap.append(el('div', { cls: 'who' }, [icon('mic'), el('span', { text: 'sesli mesaj' })]));
    const bubble = el('div', { cls: 'bubble', title: fmtTime(m.ts) });
    if (role === 'user') bubble.append(el('div', { text: m.text || '', cls: 'plain' })); else bubble.append(md(m.text || ''));
    if (role === 'user') bubble.firstChild.style.whiteSpace = 'pre-wrap';
    wrap.append(bubble);
    const atts = (m.attachments || []).map((a) => (typeof a === 'string' ? a : a && (a.name || a.att_id))).filter(Boolean);
    if (atts.length) wrap.append(el('div', { cls: 'm-att' }, atts.map((n) => el('span', { cls: 'att-chip' }, [icon('clip'), el('span', { cls: 'n', text: String(n) })]))));
    if (role === 'assistant' && m.trace && m.trace.length) {
      wrap.append(el('details', { cls: 'trace' }, [el('summary', { text: 'Araç adımları (' + m.trace.length + ')' }), el('pre', { text: m.trace.join('\n') })]));
    }
    if (role === 'assistant' && m.sources && m.sources.length) {
      wrap.append(el('div', { cls: 'sources' }, [el('div', { cls: 'src-h', text: 'Kaynaklar (' + m.sources.length + ')' }), el('div', { cls: 'src-row' }, m.sources.map(srcCard))]));
    }
    if (role === 'user' || role === 'assistant') wrap.append(buildActions(wrap, m, role));
    if (m.error && m.retry) wrap.append(el('div', null, el('button', { cls: 'btn sm', type: 'button', text: 'Tekrar dene', on: { click: () => { wrap.remove(); m.retry(); } } })));
    return wrap;
  }
  function buildActions(wrap, m, role) {
    const bar = el('div', { cls: 'actions', attrs: { role: 'group', 'aria-label': 'Mesaj eylemleri' } });
    bar.append(actBtn('copy', 'Kopyala', async () => {
      try { await copyText(m.text || ''); SB.toast('Kopyalandı', 'ok'); } catch (e) { SB.toast('Kopyalanamadı', 'error'); }
      react(m, 'copy');
    }));
    if (role === 'user') {
      if (SB.has('/api/v2/msg/edit')) bar.append(actBtn('edit', 'Düzenle ve yeniden gönder', () => startEdit(wrap)));
    } else {
      if (SB.has('/api/v2/msg/react')) {
        const setR = (name, b) => async () => {
          const next = m.reaction === name ? null : name; m.reaction = next;
          $$('button[data-r]', bar).forEach((x) => x.setAttribute('aria-pressed', x.dataset.r === next ? 'true' : 'false'));
          const r = await react(m, next); if (failed(r) && m.id) SB.toast('Tepki kaydedilemedi', 'error');
        };
        [['up', 'Beğendim'], ['down', 'Beğenmedim'], ['pin', 'Sabitle']].forEach(([n, l]) => {
          const b = actBtn(n, l, setR(n), m.reaction === n); b.dataset.r = n; bar.append(b);
        });
      }
      if (SB.has('/api/v2/msg/regen')) bar.append(actBtn('refresh', 'Yeniden üret', () => regen(wrap)));
      if (SB.has('/api/v2/msg/to-note')) bar.append(actBtn('note', 'Nota çevir', async (b) => {
        if (!m.id) return SB.toast('Bu mesaj henüz kaydedilmedi', 'error');
        b.disabled = true; const r = await api('/api/v2/msg/to-note', { id: m.id }); b.disabled = false;
        if (failed(r)) return SB.toast('Not oluşturulamadı: ' + (r && r.error), 'error');
        SB.toast('Nota çevrildi: ' + r.path, 'ok', { action: { label: 'Aç', run: () => SB.openNote(r.path) } });
      }));
    }
    return bar;
  }
  function markLast() {
    $$('.msg.last', log).forEach((n) => n.classList.remove('last'));
    const all = $$('.msg.assistant', log); if (all.length) all[all.length - 1].classList.add('last');
  }
  function scrollDown(force) {
    const near = log.scrollHeight - log.scrollTop - log.clientHeight < 240;
    if (force || near) log.scrollTop = log.scrollHeight;
  }
  function clearWelcome() { const w = $('.welcome', log); if (w) w.remove(); }
  function appendMsg(m) {
    clearWelcome(); const n = renderMsg(m); log.append(n); markLast(); scrollDown(true); return n;
  }
  function typing() {
    clearWelcome();
    const t = el('div', { cls: 'msg assistant typing-row', attrs: { role: 'status', 'aria-label': 'Asistan yazıyor' } }, el('span', { cls: 'typing' }, [el('i'), el('i'), el('i')]));
    log.append(t); scrollDown(true); return t;
  }
  function welcome() {
    log.replaceChildren(); S.cards.clear(); setChips([]);
    const sugg = ['Bugün neler var?', 'Son notlarımı özetle', 'Açık görevlerim neler?'];
    const w = el('div', { cls: 'welcome' }, [
      el('h2', { text: 'Merhaba, nasıl yardımcı olayım?' }),
      el('p', { text: 'Kasadaki notlara, maillere ve takvime bakarım. / ile komutları, Ctrl+K ile paleti aç.' }),
      el('div', { cls: 'chips' }, sugg.map((s) => el('button', { cls: 'chip', type: 'button', text: s, on: { click: () => SB.sendMessage(s) } })))
    ]);
    log.append(w);
  }

  /* ---------- düzenle / yeniden üret ---------- */
  function startEdit(wrap) {
    if (S.busy) return SB.toast('Önceki cevap bekleniyor', 'info');
    const m = wrap._m; if (!m.id) return SB.toast('Bu mesaj henüz kaydedilmedi', 'error');
    const bubble = $('.bubble', wrap); const bar = $('.actions', wrap);
    const ta = el('textarea', { value: m.text || '', attrs: { 'aria-label': 'Mesajı düzenle' } });
    const box = el('div', { cls: 'edit-box' }, [ta, el('div', { cls: 'row' }, [
      el('button', { cls: 'btn', type: 'button', text: 'Vazgeç', on: { click: () => { box.replaceWith(bubble); bar.hidden = false; } } }),
      el('button', { cls: 'btn primary', type: 'button', text: 'Kaydet ve yeniden cevapla', on: { click: save } })
    ])]);
    bubble.replaceWith(box); bar.hidden = true; ta.focus();
    ta.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { e.stopPropagation(); box.replaceWith(bubble); bar.hidden = false; }
      else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); save(); }
    });
    async function save() {
      const text = ta.value.trim(); if (!text) return;
      m.text = text; bubble.replaceChildren(el('div', { text, cls: 'plain' })); bubble.firstChild.style.whiteSpace = 'pre-wrap';
      box.replaceWith(bubble); bar.hidden = false;
      let nx = wrap.nextElementSibling; while (nx) { const d = nx; nx = nx.nextElementSibling; d.remove(); }
      S.cards.clear(); setChips([]);
      bus.emit('message', { role: 'user', text, id: m.id, edited: true });
      await runTurn(() => api('/api/v2/msg/edit', { id: m.id, text }), { text, userEl: wrap });
    }
  }
  async function regen(wrap) {
    if (S.busy) return SB.toast('Önceki cevap bekleniyor', 'info');
    const m = wrap._m; if (!m.id) return SB.toast('Bu mesaj henüz kaydedilmedi', 'error');
    wrap.style.opacity = '.5'; setBusy(true);
    const t = typing(); let r;
    try { r = await api('/api/v2/msg/regen', { id: m.id }); } finally { t.remove(); setBusy(false); wrap.style.opacity = ''; }
    if (failed(r)) return SB.toast('Yeniden üretilemedi: ' + (r && r.error), 'error');
    const rep = normReply(r); const n = renderMsg(rep.msg); wrap.replaceWith(n); markLast();
    renderProposals(r.proposals || []); refreshChips(rep.msg.text);
    bus.emit('message', { role: 'assistant', text: rep.msg.text, id: rep.msg.id, regen: true });
  }

  /* ---------- gönderme ---------- */
  function setBusy(b) {
    S.busy = b; $('#btn-send').disabled = b; log.setAttribute('aria-busy', b ? 'true' : 'false');
  }
  function normReply(r) {
    let rep = r.reply;
    if (typeof rep === 'string' || rep == null) rep = { text: rep || '' };
    const msg = Object.assign({ role: 'assistant' }, rep);
    if (!msg.trace && r.trace) msg.trace = r.trace;
    if (!msg.sources && r.sources) msg.sources = r.sources;
    msg.text = msg.text == null ? '' : String(msg.text);
    return { msg };
  }
  async function runTurn(call, ctx) {
    setBusy(true); const t = typing(); let r;
    try { r = await call(); } finally { t.remove(); setBusy(false); }
    if (failed(r)) {
      const retry = ctx.text != null && !ctx.userEl._edited ? () => doSend(ctx.text, ctx.o || {}, true) : null;
      appendMsg({ role: 'assistant', error: true, text: 'Hata: ' + (r && r.error || 'bilinmeyen'), retry });
      return r;
    }
    if (r.user && r.user.id && ctx.userEl) { ctx.userEl._m.id = r.user.id; ctx.userEl.dataset.id = r.user.id; if (!$('.actions', ctx.userEl)) ctx.userEl.append(buildActions(ctx.userEl, ctx.userEl._m, 'user')); }
    const rep = normReply(r);
    appendMsg(rep.msg);
    renderProposals(r.proposals || []);
    if (r.conv && r.conv.title) setTitle(r.conv.title);
    refreshChips(rep.msg.text);
    bus.emit('message', { role: 'assistant', text: rep.msg.text, id: rep.msg.id, voice: !!(ctx.o && ctx.o.voice), sources: rep.msg.sources });
    if (SB.has('/api/v2/convs')) refreshConvs();
    return r;
  }
  function attIds(list) { return (list || []).map((a) => (typeof a === 'string' ? a : a && (a.id || a.att_id))).filter(Boolean); }
  async function doSend(text, o, isRetry) {
    closeView();
    const atts = o.attachments || [];
    const names = atts.map((a) => (typeof a === 'string' ? a : a && a.name)).filter(Boolean);
    const userEl = appendMsg({ role: 'user', text, voice: !!o.voice, attachments: names, ts: Date.now() });
    bus.emit('message', { role: 'user', text, voice: !!o.voice });
    setChips([]);
    const ids = attIds(atts);
    const call = () => api('/api/v2/chat', ids.length ? { text, attachments: ids } : { text });   // tek sohbet giriş noktası (D-30)
    return runTurn(call, { text, userEl, o });
  }
  SB.sendMessage = async function (text, o) {
    o = o || {}; text = String(text || '').trim();
    if (!text && !(o.attachments && o.attachments.length)) return null;
    if (S.busy) { SB.toast('Önceki cevap bekleniyor', 'info'); return null; }
    return doSend(text, o);
  };

  /* ---------- onay kartları ---------- */
  const KIND_P = { takvim: 'calendar', calendar: 'calendar', komut: 'terminal', bilgisayar: 'terminal', command: 'terminal', unut: 'archive', sil: 'archive', mail: 'mail', whatsapp: 'chat', sms: 'chat', mesaj: 'chat', not: 'note', gorev: 'check' };
  const KIND_TR_P = { takvim: 'Takvim', calendar: 'Takvim', komut: 'Komut', bilgisayar: 'Bilgisayar', unut: 'Unutma', sil: 'Silme', 'takvim-sil': 'Takvim silme', mail: 'Mail', whatsapp: 'WhatsApp (onaylanınca gönderilir)', sms: 'SMS', not: 'Not', gece: 'Gece koşusu', eylem: 'Eylem', kasa: 'Kasa' };
  function propCard(p) {
    const title = p.title || p.summary || 'Onay bekliyor', detail = p.detail || p.when || '';
    const kind = String(p.kind || 'takvim').toLowerCase();
    const card = el('section', { cls: 'prop', attrs: { 'aria-label': 'Onay gerekli: ' + title }, dataset: { id: p.id } });
    const head = el('div', { cls: 'prop-h' }, [el('span', { cls: 'ico' }, icon(KIND_P[kind] || 'spark')),
      el('div', null, [el('div', { cls: 'prop-k', text: (KIND_TR_P[kind] || kind) + ' · onay gerekli' }), el('div', { text: title })])]);
    card.append(head);
    if (detail) {
      const short = detail.length < 120 && detail.split('\n').length <= 2;
      const d = el('details', null, [el('summary', { text: 'Ayrıntı' }), el('pre', { text: detail })]);
      if (short) d.open = true; card.append(d);
    }
    const yes = el('button', { cls: 'btn primary', type: 'button', text: 'Onayla' });
    const no = el('button', { cls: 'btn', type: 'button', text: 'İptal' });
    const btns = el('div', { cls: 'prop-btns' }, [yes, no]); card.append(btns);
    card._p = p; card._title = title;
    const act = (ok) => decide(card, ok);
    yes.addEventListener('click', () => act(true)); no.addEventListener('click', () => act(false));
    card._yes = yes; card._no = no; card._btns = btns;
    return card;
  }
  async function decide(card, ok) {
    if (card._done || card._working) return;
    card._working = true; card._yes.disabled = card._no.disabled = true;
    const r = await api('/api/v2/approvals/decide', { id: card._p.id, ok });   // tek onay deposu (D-30)
    card._working = false;
    if (failed(r)) { card._yes.disabled = card._no.disabled = false; return SB.toast('İşlem yapılamadı: ' + (r && r.error), 'error'); }
    card._done = true; card.classList.add('done'); if (ok) card.classList.add('ok');
    card._btns.replaceWith(el('div', { cls: 'prop-res', attrs: { role: 'status' } }, [(ok ? 'Onaylandı' : 'İptal edildi') + (r.message ? ' — ' + r.message : '')]));
    $('.prop-k', card).textContent = (ok ? 'Onaylandı' : 'İptal edildi');
    renderProposals(r.proposals || []);
    bus.emit('approval', { id: card._p.id, ok, message: r.message });
    refreshChips(null, true);
    if (SB.has('/api/v2/notifications')) pollNotifs();
  }
  function renderProposals(list) {
    list.forEach((p) => {
      if (!p || !p.id || S.cards.has(p.id)) return;
      const c = propCard(p); S.cards.set(p.id, c); clearWelcome(); log.append(c);
    });
    scrollDown(true);
  }
  const pendingCards = () => Array.from(S.cards.values()).filter((c) => !c._done);

  /* ---------- hızlı cevap çipleri ---------- */
  function setChips(items) {
    chipsBox.replaceChildren();
    items.forEach((it) => chipsBox.append(el('button', { cls: 'chip' + (it.primary ? ' primary' : ''), type: 'button', text: it.label, on: { click: it.run } })));
  }
  let lastReplyText = '';
  function refreshChips(text, keep) {
    if (text != null) lastReplyText = text;
    const t = (lastReplyText || '').trim().replace(/[\s"'”’)\]*_`]+$/g, '');
    const pend = pendingCards(); const items = [];
    if (pend.length) {
      const c = pend[0];
      items.push({ label: 'Onayla' + (pend.length > 1 ? ' (' + pend.length + ' bekliyor)' : ''), primary: true, run: () => decide(c, true) });
      items.push({ label: 'İptal', run: () => decide(c, false) });
    } else if (keep && !text) { /* onaydan sonra çip yok */ }
    else if (/\?$/.test(t)) {
      items.push({ label: 'Evet', run: () => SB.sendMessage('Evet') }, { label: 'Hayır', run: () => SB.sendMessage('Hayır') },
        { label: 'Biraz açıkla', run: () => SB.sendMessage('Biraz daha açıklar mısın?') });
    } else if (t) {
      items.push({ label: 'Devam et', run: () => SB.sendMessage('Devam et') }, { label: 'Kısaca özetle', run: () => SB.sendMessage('Bunu kısaca özetle') });
    }
    setChips(items);
  }

  /* ---------- başlık ---------- */
  function setTitle(t) {
    S.title = t || 'Yeni sohbet';
    if (!curView) { $('#title').textContent = S.title; document.title = S.title + ' · Asistan'; }
  }

  /* ---------- sohbet geçmişi ---------- */
  let convTimer = 0, convToken = 0, convData = [];
  async function refreshConvs() {
    const list = $('#conv-list');
    if (!SB.has('/api/v2/convs')) { list.replaceChildren(el('div', { cls: 'empty', text: 'Sohbet geçmişi bu sunucuda henüz yok.' })); return; }
    const my = ++convToken;
    const qs = new URLSearchParams({ q: S.q, archived: S.archived ? '1' : '0', limit: '50' });
    const r = await api('/api/v2/convs?' + qs.toString());
    if (my !== convToken) return;
    if (failed(r) || !Array.isArray(r)) { list.replaceChildren(el('div', { cls: 'empty', text: 'Geçmiş yüklenemedi.' })); return; }
    convData = r; renderConvs();
  }
  function renderConvs() {
    const list = $('#conv-list');
    if (!convData.length) { list.replaceChildren(el('div', { cls: 'empty', text: S.q ? 'Eşleşen sohbet yok.' : S.archived ? 'Arşiv boş.' : 'Henüz sohbet yok.' })); return; }
    list.replaceChildren(...convData.map(convItem));
  }
  function convItem(c) {
    const row = el('div', { cls: 'conv' + (c.sid === SB.sid ? ' active' : ''), dataset: { sid: c.sid } });
    const main = el('button', { cls: 'conv-main', type: 'button', attrs: { 'aria-current': c.sid === SB.sid ? 'true' : 'false' } }, [
      el('span', { cls: 'conv-t' }, [c.title || 'Başlıksız', c.pinned ? el('span', { cls: 'pin', title: 'Sabitli' }, icon('pin')) : null]),
      c.preview ? el('span', { cls: 'conv-p', text: c.preview }) : null]);
    main.addEventListener('click', () => loadConv(c.sid));
    const more = el('button', { cls: 'ibtn conv-more', type: 'button', title: 'Seçenekler', attrs: { 'aria-label': 'Sohbet seçenekleri: ' + (c.title || ''), 'aria-haspopup': 'menu', 'aria-expanded': 'false' } }, icon('more'));
    more.addEventListener('click', (e) => { e.stopPropagation(); convMenu(c, more, row); });
    row.addEventListener('contextmenu', (e) => { e.preventDefault(); convMenu(c, more, row); });
    row.append(main, more); return row;
  }
  let menuEl = null, menuOpener = null;
  function closeMenu(refocus) {
    if (menuEl) { menuEl.remove(); menuEl = null; }
    if (menuOpener) { menuOpener.setAttribute('aria-expanded', 'false'); if (refocus) menuOpener.focus(); menuOpener = null; }
  }
  function convMenu(c, btn, row) {
    closeMenu();
    const items = [
      [c.pinned ? 'Sabitlemeyi kaldır' : 'Sabitle', 'pin', () => convUpdate(c, { pinned: !c.pinned })],
      ['Yeniden adlandır', 'edit', () => renameConv(c, row)],
      [c.archived ? 'Arşivden çıkar' : 'Arşivle', 'archive', async () => { await convUpdate(c, { archived: !c.archived }); if (c.sid === SB.sid && !c.archived) newConv(); }]
    ];
    menuEl = el('div', { cls: 'menu', attrs: { role: 'menu' } }, items.map(([l, ic, fn]) => el('button', { type: 'button', attrs: { role: 'menuitem' }, on: { click: () => { closeMenu(); fn(); } } }, [icon(ic), l])));
    document.body.append(menuEl); menuOpener = btn; btn.setAttribute('aria-expanded', 'true');
    const rc = btn.getBoundingClientRect(); const mw = menuEl.offsetWidth, mh = menuEl.offsetHeight;
    menuEl.style.left = Math.max(8, Math.min(innerWidth - mw - 8, rc.right - mw)) + 'px';
    menuEl.style.top = Math.max(8, Math.min(innerHeight - mh - 8, rc.bottom + 4)) + 'px';
    menuEl.querySelector('button').focus();
    menuEl.addEventListener('keydown', (e) => {
      const bs = $$('button', menuEl); const i = bs.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); bs[(i + 1) % bs.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); bs[(i - 1 + bs.length) % bs.length].focus(); }
      else if (e.key === 'Escape') { e.stopPropagation(); closeMenu(true); }
      else if (e.key === 'Tab') closeMenu();
    });
  }
  async function convUpdate(c, patch) {
    const r = await api('/api/v2/conv/update', Object.assign({ sid: c.sid }, patch));
    if (failed(r)) SB.toast('Güncellenemedi: ' + (r && r.error), 'error');
    else if (patch.archived === true) SB.toast('Arşive taşındı');
    if (patch.archived === true && c.sid === SB.sid) newConv();
    refreshConvs();
  }
  function renameConv(c, row) {
    const main = $('.conv-main', row); const input = el('input', { cls: 'rename', value: c.title || '', attrs: { 'aria-label': 'Sohbet adı' } });
    main.replaceWith(input); input.focus(); input.select(); let done = false;
    const finish = async (ok) => {
      if (done) return; done = true;
      const v = input.value.trim();
      if (ok && v && v !== c.title) {
        const r = await api('/api/v2/conv/update', { sid: c.sid, title: v });
        if (failed(r)) SB.toast('Adlandırılamadı: ' + (r && r.error), 'error'); else if (c.sid === SB.sid) setTitle(v);
      }
      refreshConvs();
    };
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') finish(true); else if (e.key === 'Escape') { e.stopPropagation(); finish(false); } });
    input.addEventListener('blur', () => finish(true));
  }
  async function loadConv(sid) {
    closeDrawer(); closeView();
    if (sid === SB.sid && $$('.msg', log).length) return;
    const r = await api('/api/v2/conv?sid=' + encodeURIComponent(sid));
    if (failed(r)) return SB.toast('Sohbet açılamadı: ' + (r && r.error), 'error');
    SB.sid = sid; settings.set('sid', sid);
    log.replaceChildren(); S.cards.clear(); setChips([]);
    const msgs = r.messages || [];
    if (!msgs.length) welcome();
    msgs.forEach((m) => log.append(renderMsg(Object.assign({}, m, { role: m.role }))));
    markLast(); scrollDown(true); setTitle(r.title || 'Sohbet'); renderConvs();
    refreshChips(null, true); lastReplyText = '';
    bus.emit('conv', { sid, title: r.title });
    q.focus();
  }
  async function newConv() {
    closeDrawer(); closeView();
    let sid = '';
    if (SB.has('/api/v2/conv/new')) { const r = await api('/api/v2/conv/new', {}); if (!failed(r) && r.sid) sid = r.sid; }
    if (!sid) sid = rand();
    SB.sid = sid; settings.set('sid', sid); lastReplyText = '';
    welcome(); setTitle('Yeni sohbet'); renderConvs(); bus.emit('conv', { sid, title: '' }); q.focus();
  }
  SB.newConversation = newConv; SB.openConversation = loadConv;

  /* ---------- görünümler ---------- */
  SB.registerView = function (name, def) { views.set(name, def); renderViewsMenu(); };
  function renderViewsMenu() {
    const box = $('#views-menu'); if (!box) return;
    if (!views.size) { box.replaceChildren(el('div', { cls: 'empty', text: 'Kayıtlı görünüm yok.' })); return; }
    box.replaceChildren(...Array.from(views.entries()).map(([n, d]) => {
      const ALIAS = { 'layout-dashboard': 'grid', 'share-2': 'spark', clock: 'calendar', user: 'chat', folder: 'note', layers: 'copy', 'alert-triangle': 'info', 'graduation-cap': 'spark', 'book-open': 'note', brain: 'spark', settings: 'settings' };
      const ik = d.icon && /^[a-z0-9-]+$/.test(d.icon) ? (ICONS[d.icon] ? d.icon : (ALIAS[d.icon] || 'spark')) : '';
      const ic = ik ? icon(ik) : el('span', { cls: 'vi', text: d.icon || '•', attrs: { 'aria-hidden': 'true' } });
      return el('button', { type: 'button', dataset: { view: n }, attrs: { 'aria-current': curView === n ? 'page' : 'false' }, on: { click: () => SB.openView(n) } }, [ic, el('span', { text: d.title || n })]);
    }));
  }
  SB.openView = function (name, params) {
    const d = views.get(name);
    if (!d) { SB.toast('Görünüm bulunamadı: ' + name, 'error'); return false; }
    closeOverlays(); closeDrawer();
    if (viewCleanup) { safe(viewCleanup); viewCleanup = null; }
    const v = $('#view'); v.replaceChildren(); $('#chat').hidden = true; v.hidden = false; $('#view-back').hidden = false;
    curView = name; $('#title').textContent = d.title || name; document.title = (d.title || name) + ' · Asistan';
    renderViewsMenu();
    const fail = (e) => { console.error(e); v.replaceChildren(el('div', { cls: 'empty', text: 'Görünüm yüklenemedi: ' + (e && e.message || e) })); };
    try { const out = d.render(v, params || {}); if (out && typeof out.then === 'function') out.then((f) => { if (typeof f === 'function') viewCleanup = f; }, fail); else if (typeof out === 'function') viewCleanup = out; } catch (e) { fail(e); }
    v.tabIndex = -1; v.focus({ preventScroll: true });
    bus.emit('view', { name, params: params || {} });
    return true;
  };
  SB.closeView = closeView;
  function closeView() {
    if (!curView) return;
    if (viewCleanup) { safe(viewCleanup); viewCleanup = null; }
    const prev = curView; curView = null;
    $('#view').hidden = true; $('#view').replaceChildren(); $('#chat').hidden = false; $('#view-back').hidden = true;
    setTitle(S.title); renderViewsMenu(); q.focus({ preventScroll: true });
    bus.emit('view', { name: null, previous: prev });
  }

  /* ---------- komutlar (eğik çizgi) ---------- */
  SB.registerCommand = function (c) {
    if (!c || !c.cmd) return; const cmd = '/' + String(c.cmd).replace(/^\//, '').toLowerCase();
    S.clientCmds.set(cmd, { cmd, desc: c.desc || '', args: c.args, run: c.run });
  };
  function allCmds() {
    const map = new Map();
    S.cmds.forEach((c) => map.set(c.cmd, c));
    S.clientCmds.forEach((c, k) => map.set(k, c));
    return Array.from(map.values()).sort((a, b) => a.cmd.localeCompare(b.cmd, 'tr'));
  }
  async function loadServerCmds() {
    if (!SB.has('/api/v2/commands')) return;
    const r = await api('/api/v2/commands');
    if (Array.isArray(r)) S.cmds = r.filter((c) => c && c.cmd).map((c) => ({ cmd: ('/' + String(c.cmd).replace(/^\//, '')).toLowerCase(), desc: c.desc || '', args: c.args, server: true }));
  }
  async function execSlash(text) {
    const m = /^\/(\S+)\s*([\s\S]*)$/.exec(text); if (!m) return false;
    const cmd = '/' + m[1].toLowerCase(), args = m[2].trim();
    const cc = S.clientCmds.get(cmd);
    if (cc && cc.run) { try { await cc.run(args); } catch (e) { SB.toast('Komut hatası: ' + e.message, 'error'); } return true; }
    if (S.cmds.some((c) => c.cmd === cmd) && SB.has('/api/v2/command')) {
      if (S.busy) { SB.toast('Önceki cevap bekleniyor', 'info'); return true; }
      closeView(); appendMsg({ role: 'user', text }); setBusy(true); const t = typing(); let r;
      try { r = await api('/api/v2/command', { cmd, args }); } finally { t.remove(); setBusy(false); }
      if (failed(r)) { appendMsg({ role: 'assistant', error: true, text: 'Hata: ' + (r && r.error) }); return true; }
      const rep = normReply({ reply: r.reply, sources: r.sources, trace: r.trace });
      if (rep.msg.text || (rep.msg.sources && rep.msg.sources.length)) { appendMsg(rep.msg); refreshChips(rep.msg.text); }
      if (r.proposals) renderProposals(r.proposals);
      if (r.open && r.open.view) SB.openView(r.open.view, r.open.params);
      if (r.sid && r.sid !== SB.sid) { SB.sid = r.sid; settings.set('sid', r.sid); }
      if (SB.has('/api/v2/convs')) refreshConvs();
      return true;
    }
    return false;
  }
  function builtins() {
    SB.registerCommand({ cmd: 'yeni', desc: 'Yeni sohbet başlat', run: () => newConv() });
    SB.registerCommand({ cmd: 'tema', desc: 'Temayı değiştir (otomatik, açık, koyu)', run: cycleTheme });
    SB.registerCommand({ cmd: 'ayarlar', desc: 'Görünüm ve cihaz ayarları', run: () => openSettings() });
    SB.registerCommand({ cmd: 'palet', desc: 'Komut paletini aç', run: () => openPalette() });
  }

  /* eğik çizgi önerileri */
  let slashIdx = 0, slashItems = [];
  function updateSlash() {
    const box = $('#slash'); const v = q.value;
    const m = /^\/(\S*)$/.exec(v);
    if (!m) { box.hidden = true; q.removeAttribute('aria-activedescendant'); return; }
    const key = '/' + m[1].toLowerCase();
    slashItems = allCmds().filter((c) => c.cmd.startsWith(key));
    if (!slashItems.length) { box.hidden = true; return; }
    slashIdx = Math.min(slashIdx, slashItems.length - 1);
    box.replaceChildren(...slashItems.map((c, i) => el('div', { cls: 'opt', id: 'sl-' + i, attrs: { role: 'option', 'aria-selected': i === slashIdx ? 'true' : 'false' }, on: { mousedown: (e) => { e.preventDefault(); pickSlash(i); } } },
      [el('span', { cls: 'c', text: c.cmd + (c.args ? ' ' + c.args : '') }), el('span', { cls: 'd', text: c.desc })])));
    box.hidden = false; q.setAttribute('aria-activedescendant', 'sl-' + slashIdx);
    const a = $('#sl-' + slashIdx); if (a && a.scrollIntoView) a.scrollIntoView({ block: 'nearest' });
  }
  function pickSlash(i) {
    const c = slashItems[i]; if (!c) return;
    q.value = c.cmd + ' '; $('#slash').hidden = true; q.removeAttribute('aria-activedescendant'); autosize(); q.focus();
  }

  /* ---------- yazma alanı ---------- */
  function autosize() { q.style.height = 'auto'; q.style.height = Math.min(q.scrollHeight, 200) + 'px'; }
  async function submitComposer() {
    const text = q.value.trim(); const hasAtt = S.atts.length > 0;
    if (!text && !hasAtt) return;
    if (S.busy) return SB.toast('Önceki cevap bekleniyor', 'info');
    if (S.atts.some((a) => a.status === 'busy')) return SB.toast('Ekler yükleniyor, bir saniye', 'info');
    if (text.startsWith('/') && !hasAtt) {
      q.value = ''; autosize(); $('#slash').hidden = true;
      if (await execSlash(text)) return;
      q.value = text; autosize();
    }
    const atts = S.atts.filter((a) => a.status === 'ok');
    q.value = ''; autosize(); $('#slash').hidden = true; S.atts = []; renderAtts();
    doSend(text || '(ek)', { attachments: atts });
  }

  /* ---------- ekler ---------- */
  function renderAtts() {
    const row = $('#atts');
    row.replaceChildren(...S.atts.map((a) => el('span', { cls: 'att-chip' + (a.status === 'err' ? ' err' : a.status === 'busy' ? ' busy' : ''), title: a.err || '' }, [
      icon('clip'), el('span', { cls: 'n', text: a.name + (a.status === 'busy' ? ' (yükleniyor)' : a.status === 'err' ? ' (hata)' : '') }),
      el('button', { type: 'button', attrs: { 'aria-label': a.name + ' ekini kaldır' }, on: { click: () => { S.atts = S.atts.filter((x) => x !== a); renderAtts(); } } }, icon('x'))])));
  }
  async function addFiles(files) {
    if (!SB.has('/api/v2/upload')) return SB.toast('Dosya ekleme bu sunucuda kapalı', 'error');
    for (const f of Array.from(files)) {
      let name = f.name || ('yapistirilan-' + Date.now() + '.' + ((f.type || '').split('/')[1] || 'bin'));
      if (name === 'image.png') name = 'yapistirilan-' + Date.now() + '.png';
      const a = { name, status: 'busy', id: '' }; S.atts.push(a); renderAtts();
      if (f.size > 30 * 1024 * 1024) { a.status = 'err'; a.err = 'En çok 30 MB'; renderAtts(); SB.toast(name + ': 30 MB sınırı aşıldı', 'error'); continue; }
      try {
        const res = await fetch('/api/v2/upload?sid=' + encodeURIComponent(SB.sid) + '&name=' + encodeURIComponent(name), { method: 'POST', headers: { 'X-SB': '1', 'Content-Type': 'application/octet-stream' }, body: f });
        const j = await res.json().catch(() => ({ error: 'Geçersiz yanıt' }));
        if (!res.ok || j.error) throw new Error(j.error || ('HTTP ' + res.status));
        a.id = j.att_id; a.name = j.name || name; a.status = 'ok'; a.kind = j.kind;
      } catch (e) { a.status = 'err'; a.err = e.message; SB.toast(name + ': yüklenemedi (' + e.message + ')', 'error'); }
      renderAtts();
    }
  }

  /* ---------- komut paleti ---------- */
  let palIdx = 0, palItems = [], palToken = 0, palTimer = 0;
  const PAL_TYPE = { note: 'Not', person: 'Kişi', project: 'Proje', command: 'Komut', conv: 'Sohbet', view: 'Görünüm' };
  function localPalette(term) {
    const t = term.toLowerCase(); const out = [];
    out.push({ type: 'command', label: 'Yeni sohbet', action: { cmd: '/yeni' } });
    views.forEach((d, n) => out.push({ type: 'view', label: d.title || n, action: { view: n } }));
    allCmds().forEach((c) => out.push({ type: 'command', label: c.cmd, sub: c.desc, action: { cmd: c.cmd } }));
    return out.filter((i) => !t || (i.label + ' ' + (i.sub || '')).toLowerCase().includes(t));
  }
  function palItem(it, i) {
    return el('div', { cls: 'opt', id: 'po-' + i, attrs: { role: 'option', 'aria-selected': i === palIdx ? 'true' : 'false' }, on: { mousedown: (e) => { e.preventDefault(); runPal(it); }, mousemove: () => { if (palIdx !== i) { palIdx = i; markPal(); } } } },
      [el('span', { cls: 't', text: PAL_TYPE[it.type] || it.type || '' }), el('span', { cls: 'l', text: it.label || '' }), it.sub ? el('span', { cls: 'd', text: it.sub }) : null]);
  }
  function markPal() {
    $$('#pal-list .opt').forEach((n, i) => n.setAttribute('aria-selected', i === palIdx ? 'true' : 'false'));
    const a = $('#po-' + palIdx); if (a && a.scrollIntoView) a.scrollIntoView({ block: 'nearest' });
    $('#pal-q').setAttribute('aria-activedescendant', 'po-' + palIdx);
  }
  async function searchPalette() {
    const term = $('#pal-q').value.trim(); const my = ++palToken;
    palItems = localPalette(term).slice(0, 30); palIdx = 0; paintPal();
    if (SB.has('/api/v2/palette')) {
      const r = await api('/api/v2/palette?q=' + encodeURIComponent(term));
      if (my !== palToken || !Array.isArray(r)) return;
      const seen = new Set(); palItems = r.concat(palItems).filter((i) => { const k = i.type + '|' + i.label; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 40); palIdx = 0; paintPal();
    }
  }
  function paintPal() {
    const box = $('#pal-list');
    if (!palItems.length) { box.replaceChildren(el('div', { cls: 'empty', text: 'Sonuç yok.' })); return; }
    box.replaceChildren(...palItems.map(palItem)); markPal();
  }
  function runPal(it) {
    closePalette(); const a = it.action || {};
    if (a.view) SB.openView(a.view, a.params);
    else if (a.cmd) { const c = a.cmd; setTimeout(async () => { if (!(await execSlash(c))) { q.value = c + ' '; autosize(); q.focus(); } }, 0); }
    else if (a.sid) loadConv(a.sid);
    else if (a.path) SB.openNote(a.path);
    else if (a.url) openLink(a.url);
  }
  function openPalette() {
    closeOverlays(); S.lastFocus = document.activeElement; $('#palette').hidden = false; const i = $('#pal-q'); i.value = ''; i.focus(); searchPalette();
  }
  function closePalette() { if ($('#palette').hidden) return; $('#palette').hidden = true; if (S.lastFocus && S.lastFocus.focus) S.lastFocus.focus(); }

  /* ---------- bildirim merkezi ---------- */
  let notifTimer = 0;
  async function pollNotifs() {
    if (!SB.has('/api/v2/notifications')) return;
    const r = await api('/api/v2/notifications?unread=1');
    if (!Array.isArray(r)) return;
    const unread = r.filter((n) => !n.read);
    const ids = new Set(unread.map((n) => n.id));
    if (S.notifSeen) unread.forEach((n) => { if (!S.notifSeen.has(n.id)) SB.toast(n.title + (n.body ? ': ' + n.body : ''), n.kind === 'error' ? 'error' : 'info'); });
    S.notifSeen = ids;
    const b = $('#bell-badge'); b.hidden = !unread.length; b.textContent = unread.length > 9 ? '9+' : String(unread.length);
    $('#btn-bell').setAttribute('aria-label', unread.length ? 'Bildirimler, ' + unread.length + ' okunmamış' : 'Bildirimler');
    if (!$('#notif').hidden) paintNotifs();
  }
  async function paintNotifs() {
    const r = await api('/api/v2/notifications'); const box = $('#notif-list');
    if (!Array.isArray(r)) { box.replaceChildren(el('div', { cls: 'empty', text: 'Bildirimler yüklenemedi.' })); return; }
    if (!r.length) { box.replaceChildren(el('div', { cls: 'empty', text: 'Bildirim yok.' })); return; }
    box.replaceChildren(...r.slice(0, 50).map((n) => el('button', { cls: 'nitem' + (n.read ? '' : ' unread'), type: 'button', on: { click: async () => {
      if (!n.read) { await api('/api/v2/notifications/read', { ids: [n.id] }); n.read = true; pollNotifs(); }
      if (n.link) { if (SAFE_URL.test(n.link)) openLink(n.link); else if (views.has(n.link)) { closeNotif(); SB.openView(n.link); } }
    } } }, [el('span', null, [el('span', { cls: 'nt', text: n.title || '' }), n.body ? el('span', { cls: 'nb', text: n.body }) : null, el('span', { cls: 'nd', text: (n.kind ? n.kind + ' · ' : '') + fmtTime(n.ts) })])])));
  }
  function openNotif() {
    closeOverlays(); $('#notif').hidden = false; $('#btn-bell').setAttribute('aria-expanded', 'true'); paintNotifs();
    const f = $('#notif-all'); f.focus();
  }
  function closeNotif() { if ($('#notif').hidden) return; $('#notif').hidden = true; $('#btn-bell').setAttribute('aria-expanded', 'false'); }

  /* ---------- ayarlar diyaloğu + telefon eşleme ---------- */
  let pairTimer = 0;
  function seg(box, items, current, onPick, swatch) {
    box.replaceChildren(...items.map(([val, label, color]) => {
      const b = el('button', { type: 'button', attrs: { role: 'radio', 'aria-checked': String(val) === String(current) ? 'true' : 'false', 'aria-label': label }, on: { click: () => { onPick(val); seg(box, items, val, onPick, swatch); } } },
        swatch ? [(() => { const i = el('i'); i.style.background = color; return i; })()] : label);
      if (swatch) b.title = label; return b;
    }));
  }
  async function refreshPair() {
    if (!SB.local) return;
    const r = await api('/api/remote', {}); const box = $('#pair-info');
    if (failed(r)) { box.replaceChildren('Telefon bilgisi alınamadı.'); return; }
    if (!r.ip) { box.replaceChildren('Tailscale kapalı: telefon bağlantısı yok.'); return; }
    const kids = [el('div', null, ['Adres: ', el('code', { text: 'http://' + r.ip + ':8765' })]), el('div', null, ['Eşleme kodu: ', el('code', { text: String(r.pin) })]), el('div', { text: 'Eşli cihaz: ' + r.devices })];
    if (r.devices) kids.push(el('button', { cls: 'btn danger sm', type: 'button', text: 'Telefon bağlantılarını kapat', on: { click: async () => { await api('/api/remote-revoke', {}); SB.toast('Telefon bağlantıları kapatıldı'); refreshPair(); } } }));
    box.replaceChildren(...kids);
  }
  function openSettings() {
    closeOverlays(); S.lastFocus = document.activeElement; $('#settings').hidden = false;
    seg($('#seg-theme'), [['system', 'Otomatik'], ['light', 'Açık'], ['dark', 'Koyu']], settings.get('theme', 'system'), (v) => settings.set('theme', v));
    seg($('#seg-accent'), ACCENTS, settings.get('accent', 'blue'), (v) => settings.set('accent', v), true);
    seg($('#seg-font'), FONTS, settings.get('fontsize', 'medium'), (v) => settings.set('fontsize', v));
    $('#srv-info').textContent = (SB.model ? 'Model: ' + SB.model + ' · ' : '') + SB.routes.size / 2 + ' API ucu · ' + (SB.local ? 'bilgisayar' : 'telefon');
    $('#pair-box').hidden = !SB.local; if (SB.local) { refreshPair(); pairTimer = setInterval(refreshPair, 30000); }
    $('#set-close').focus();
  }
  function closeSettings() {
    if ($('#settings').hidden) return; $('#settings').hidden = true; clearInterval(pairTimer);
    if (S.lastFocus && S.lastFocus.focus) S.lastFocus.focus();
  }

  /* ---------- çekmece, katmanlar ---------- */
  const mqNarrow = window.matchMedia('(max-width: 760px)');
  function openDrawer() { document.body.classList.add('drawer'); $('#scrim').hidden = false; S.lastFocus = document.activeElement; $('#new-chat').focus(); }
  function closeDrawer() { if (!document.body.classList.contains('drawer')) return; document.body.classList.remove('drawer'); $('#scrim').hidden = true; }
  function closeOverlays() { closeMenu(); closePalette(); closeNotif(); closeSettings(); $('#slash').hidden = true; }

  /* ---------- ses ---------- */
  let recording = false;
  function syncMic() {
    const b = $('#mic-btn'); const ok = !!(SB.voice && typeof SB.voice.start === 'function');
    b.hidden = !ok;
  }
  function setRec(on) { recording = on; }

  /* ---------- başlatma ---------- */
  function wire() {
    log = $('#log'); q = $('#q'); chipsBox = $('#chips');
    $$('[data-icon]').forEach((n) => { if (!n.firstChild) n.append(icon(n.dataset.icon)); });
    $('#composer').addEventListener('submit', (e) => { e.preventDefault(); submitComposer(); });
    q.addEventListener('input', () => { autosize(); slashIdx = 0; updateSlash(); });
    q.addEventListener('keydown', (e) => {
      const open = !$('#slash').hidden;
      if (open && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) { e.preventDefault(); slashIdx = (slashIdx + (e.key === 'ArrowDown' ? 1 : -1) + slashItems.length) % slashItems.length; updateSlash(); return; }
      if (open && (e.key === 'Tab' || (e.key === 'Enter' && !e.shiftKey && !/\s/.test(q.value)))) { if (!(e.key === 'Enter' && q.value.trim() !== '' && slashItems.some((c) => c.cmd === q.value.trim().toLowerCase()))) { e.preventDefault(); pickSlash(slashIdx); return; } }
      if (open && e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); $('#slash').hidden = true; return; }
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); submitComposer(); }
    });
    q.addEventListener('blur', () => setTimeout(() => { $('#slash').hidden = true; }, 120));
    q.addEventListener('paste', (e) => {
      const fs = e.clipboardData && e.clipboardData.files; if (fs && fs.length && SB.has('/api/v2/upload')) { e.preventDefault(); addFiles(fs); }
    });
    $('#btn-attach').addEventListener('click', () => $('#file-in').click());
    $('#file-in').addEventListener('change', (e) => { addFiles(e.target.files); e.target.value = ''; });
    // sürükle-bırak
    let dragN = 0; const hasFiles = (e) => e.dataTransfer && Array.from(e.dataTransfer.types || []).includes('Files');
    window.addEventListener('dragenter', (e) => { if (hasFiles(e) && SB.has('/api/v2/upload')) { dragN++; $('#drop').hidden = false; } });
    window.addEventListener('dragleave', (e) => { if (hasFiles(e)) { dragN = Math.max(0, dragN - 1); if (!dragN) $('#drop').hidden = true; } });
    window.addEventListener('dragover', (e) => { if (hasFiles(e)) e.preventDefault(); });
    window.addEventListener('drop', (e) => { if (!hasFiles(e)) return; e.preventDefault(); dragN = 0; $('#drop').hidden = true; if (SB.has('/api/v2/upload')) { closeView(); addFiles(e.dataTransfer.files); q.focus(); } });

    $('#new-chat').addEventListener('click', newConv);
    $('#conv-search').addEventListener('input', (e) => { clearTimeout(convTimer); S.q = e.target.value.trim(); convTimer = setTimeout(refreshConvs, 250); });
    const tabs = (arch) => { S.archived = arch; $('#tab-active').setAttribute('aria-selected', String(!arch)); $('#tab-archive').setAttribute('aria-selected', String(arch)); refreshConvs(); };
    $('#tab-active').addEventListener('click', () => tabs(false)); $('#tab-archive').addEventListener('click', () => tabs(true));
    $('#views-toggle').addEventListener('click', (e) => { const b = e.currentTarget; const o = b.getAttribute('aria-expanded') !== 'true'; b.setAttribute('aria-expanded', String(o)); $('#views-menu').hidden = !o; });
    $('#side-open').addEventListener('click', openDrawer); $('#side-close').addEventListener('click', closeDrawer); $('#scrim').addEventListener('click', closeDrawer);
    mqNarrow.addEventListener('change', closeDrawer);
    $('#view-back').addEventListener('click', closeView);
    $('#btn-palette').addEventListener('click', openPalette);
    $('#btn-theme').addEventListener('click', cycleTheme);
    $('#btn-bell').addEventListener('click', () => ($('#notif').hidden ? openNotif() : closeNotif()));
    $('#notif-all').addEventListener('click', async () => { await api('/api/v2/notifications/read', { ids: 'all' }); pollNotifs(); paintNotifs(); });
    $('#open-settings').addEventListener('click', openSettings); $('#set-close').addEventListener('click', closeSettings);
    $('#btn-phone').addEventListener('click', openSettings);
    $('#settings').addEventListener('mousedown', (e) => { if (e.target.id === 'settings') closeSettings(); });
    $('#palette').addEventListener('mousedown', (e) => { if (e.target.id === 'palette') closePalette(); });
    ['voice:start', 'voice:recording', 'voice:listening'].forEach((e) => bus.on(e, () => { syncMic(); setRec(true); }));
    ['voice:stop', 'voice:end', 'voice:idle', 'voice:error'].forEach((e) => bus.on(e, () => setRec(false)));

    bus.on('settings', (d) => { if (d && (d.key === 'theme' || d.key === 'accent' || d.key === 'fontsize')) applySetting(d.key); });
    bus.on('forget', (d) => {
      d = d || {}; let list = d.proposals || (d.proposal ? [d.proposal] : []);
      if (!list.length && d.proposal_id) list = [{ id: d.proposal_id, kind: 'unut', title: 'Unutma isteği', detail: d.found ? JSON.stringify(d.found) : '' }];
      if (list.length) { closeView(); renderProposals(list); refreshChips(null, true); }
    });
    const pq = $('#pal-q');
    pq.addEventListener('input', () => { clearTimeout(palTimer); palTimer = setTimeout(searchPalette, 120); });
    pq.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (palItems.length) { palIdx = (palIdx + (e.key === 'ArrowDown' ? 1 : -1) + palItems.length) % palItems.length; markPal(); } }
      else if (e.key === 'Enter') { e.preventDefault(); if (palItems[palIdx]) runPal(palItems[palIdx]); }
      else if (e.key === 'Tab') e.preventDefault();
    });
    // Tab tuzağı: ayarlar diyaloğu
    $('#settings').addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return; const f = $$('button:not([disabled]),input,select', $('#settings')).filter((n) => n.offsetParent !== null); if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });

    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === 'k') { e.preventDefault(); $('#palette').hidden ? openPalette() : closePalette(); return; }
      if (e.key === 'Escape') {
        if (menuEl) return closeMenu(true);
        if (!$('#palette').hidden) return closePalette();
        if (!$('#settings').hidden) return closeSettings();
        if (!$('#notif').hidden) { closeNotif(); $('#btn-bell').focus(); return; }
        if (document.body.classList.contains('drawer')) return closeDrawer();
        if (curView) return closeView();
      }
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey && !curView && !/^(INPUT|TEXTAREA|SELECT)$/.test((document.activeElement || {}).tagName || '') && !(document.activeElement || {}).isContentEditable) { q.focus(); }
    });
    document.addEventListener('mousedown', (e) => {
      if (menuEl && !menuEl.contains(e.target)) closeMenu();
      const n = $('#notif'); if (!n.hidden && !n.contains(e.target) && !$('#btn-bell').contains(e.target)) closeNotif();
    });
    document.addEventListener('visibilitychange', () => { if (!document.hidden) pollNotifs(); });
  }

  async function loadRoutes() {
    const r = await api('/api/v2/routes');
    if (r && Array.isArray(r.routes)) {
      r.routes.forEach((s) => { SB.routes.add(s); const p = String(s).split(' ')[1]; if (p) SB.routes.add(p); });
      SB.routeErrors = r.errors || {};
    }
  }

  async function init() {
    applySettings();
    wire(); builtins(); syncThemeBtn(); renderViewsMenu();
    $('#subtitle').textContent = SB.model ? 'Yerel asistan · ' + SB.model : 'Yerel asistan';
    $('#btn-phone').hidden = !SB.local;
    welcome();
    await loadRoutes();
    // yeteneğe göre düğmeleri göster
    $('#btn-attach').hidden = !SB.has('/api/v2/upload');
    $('#btn-bell').hidden = !SB.has('/api/v2/notifications');
    $('#btn-palette').hidden = false;
    syncMic();
    SB.bus.emit('ready');
    syncMic();
    loadServerCmds();
    await refreshConvs();
    if (SB.has('/api/v2/conv') && settings.get('sid', '')) {
      const r = await api('/api/v2/conv?sid=' + encodeURIComponent(SB.sid));
      if (!failed(r) && r.messages && r.messages.length) { SB.sid = r.sid || SB.sid; loadConvFromRecord(r); }
    }
    if (SB.has('/api/v2/notifications')) { pollNotifs(); notifTimer = setInterval(() => { if (!document.hidden) pollNotifs(); }, 30000); }
    setTimeout(syncMic, 1500);
  }
  function loadConvFromRecord(r) {
    log.replaceChildren(); S.cards.clear();
    (r.messages || []).forEach((m) => log.append(renderMsg(m)));
    markLast(); scrollDown(true); setTitle(r.title || 'Sohbet'); renderConvs();
  }
  function applySettings() { applySetting(null); }
  applySettings();

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
