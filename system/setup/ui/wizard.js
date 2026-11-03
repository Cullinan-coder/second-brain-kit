'use strict';
/* Adım bileşenleri (R.*) ve 12 adımlı sihirbaz kabuğu. Bileşenler ayarlar kipinde (settings.js) sekme içeriği olarak yeniden kullanılır.
   Ham HTML dizgesi yok; şifre alanları gönderimden sonra wipeSecrets() ile silinir. */
const STEPS = ['welcome', 'presets', 'features', 'profile', 'accounts', 'keys', 'models', 'mcp', 'data', 'phone', 'startup', 'summary'];
const NEEDS_REQS = ['accounts', 'keys', 'mcp', 'data'];
const R = {};

/* ================= ortak parçalar ================= */
function spinner() { return h('p', { class: 'muted', text: t('common.loading') }); }
function unavailableBox() { return h('p', { class: 'muted', text: t('err.unavailable') }); }
function normSecrets(d) {
  const out = {};
  const m = d && (d.secrets !== undefined ? d.secrets : d);
  if (Array.isArray(m)) m.forEach((x) => { if (typeof x === 'string') out[x] = true; else if (x) out[x.key || x.name] = x.set !== undefined ? !!x.set : (x.present !== undefined ? !!x.present : x.status !== 'yok'); });
  else if (m && typeof m === 'object') Object.entries(m).forEach(([k, v]) => { out[k] = v === true || v === 'var' || v === 'set' || !!(v && (v.set || v.present)); });
  return out;
}
async function loadSecrets() { const r = await api('/api/secrets'); return r.ok && r.data ? normSecrets(r.data) : null; }
/* sır satırı: yalnız POST /api/secret → keyring; değer gönderimden sonra silinir */
function secretRow(key, label, have, hint) {
  const input = h('input', { type: 'password', id: 'sec-' + key, autocomplete: 'off', placeholder: have ? t('keys.stored') : '' });
  const out = h('span', { class: 'msg muted', 'aria-live': 'polite' });
  const badge = h('span', { class: 'badge ' + (have ? 'ok' : ''), text: have ? t('keys.have') : t('keys.none') });
  const save = btn(t('keys.save'), async () => {
    if (!input.value) { msg(out, t('keys.empty'), 'warn'); return; }
    msg(out, t('hes.testing'));
    const r = await api('/api/secret', { key, value: input.value });
    wipeSecrets();
    if (!r.ok) { msg(out, unavailable(r), 'bad'); return; }
    const d = r.data || {};
    msg(out, (d.ok === false ? '✗ ' : '✓ ') + (d.message || t('keys.saved')), d.ok === false ? 'bad' : 'ok');
    badge.className = 'badge ok'; badge.textContent = t('keys.have');
  }, 'primary');
  return h('div', { class: 'field' }, h('label', { for: 'sec-' + key, text: label }),
    h('div', {}, input, hint ? h('small', { class: 'muted', text: hint }) : null, out), h('div', { class: 'row tight' }, badge, save));
}

/* ================= 1 · Hoş geldin ================= */
R.welcome = (box) => {
  box.append(h('div', { class: 'cards' },
    ['tr', 'en'].map((l) => h('button', {
      type: 'button', class: 'card', 'aria-pressed': String(S.lang === l), onclick: () => { if (S.lang !== l) setLang(l); },
    }, h('b', { text: l === 'tr' ? 'Türkçe' : 'English' })))));
  box.append(h('h3', { text: t('welcome.privacy') }),
    h('ul', { class: 'bullets' }, ['1', '2', '3', '4'].map((i) => h('li', { text: t('welcome.p.' + i) }))),
    h('p', { class: 'muted', text: t('welcome.license') }), h('p', { class: 'muted', text: t('welcome.skipnote') }));
};

/* ================= 2 · Hazır seçim ================= */
R.presets = (box) => {
  if (!S.presets) { box.append(unavailableBox()); return; }
  const info = h('p', { class: 'muted', 'aria-live': 'polite' });
  const warn = h('div', {});
  const refresh = () => {
    const c = counts();
    info.textContent = S.combineBusy ? t('common.loading') : t('presets.result', { m: c.mods, i: c.items });
    clear(warn);
    S.warnings.forEach((w) => warn.append(h('p', { class: 'warn', text: '⚠ ' + w })));
  };
  const axisBox = h('div', {});
  const draw = () => {
    clear(axisBox);
    AXES.forEach((ax) => {
      const cards = h('div', { class: 'cards' });
      S.presets.axes[ax].forEach((o) => {
        const rec = S.presets.recommended[ax] === o.id;
        cards.append(h('button', {
          type: 'button', class: 'card', 'aria-pressed': String(S.axes[ax] === o.id), onclick: async () => {
            S.axes[ax] = (ax === 'meslek' && S.axes[ax] === o.id) ? '' : o.id;
            draw(); S.combineBusy = true; refresh();
            await applyCombine();
            refresh(); saveWizardSoon();
          },
        }, h('b', { text: o.name }), rec ? h('span', { class: 'badge ok', text: t('presets.rec') }) : null, h('small', { text: o.desc })));
      });
      axisBox.append(h('h3', { text: t('axis.' + ax) }), h('p', { class: 'muted', text: t('axis.' + ax + '.d') }), cards);
    });
  };
  draw(); refresh();
  box.append(axisBox, info, warn);
};

/* ================= 3 · Bütün özellikler ================= */
function reqKinds(req) {
  const out = [];
  if (!req) return out;
  if (typeof req === 'string') return req.trim() && req.trim() !== '—' ? [{ kind: 'other', text: req }] : [];
  if (arr(req.accounts).length) out.push({ kind: 'acct', text: arr(req.accounts).map(idOf).join(', ') });
  if (arr(req.secrets).length) out.push({ kind: 'key', text: arr(req.secrets).map(idOf).join(', ') });
  const hw = req.hardware || {};
  const g = Object.keys(hw).filter((k) => /gpu|vram/i.test(k) && hw[k]);
  if (g.length) out.push({ kind: 'gpu', text: g.map((k) => k + (typeof hw[k] === 'number' ? ' ≥ ' + hw[k] : '')).join(', ') });
  return out;
}
function badgeEl(b) { return h('span', { class: 'badge req-' + b.kind, title: b.text, text: t('req.' + b.kind) }); }

function buildTree(box) {
  clear(box);
  if (!S.catalog) { box.append(unavailableBox()); return; }
  const T = { mods: {}, q: '', cat: '', only: false };
  S.tree = T;
  const summary = h('span', { class: 'muted', 'aria-live': 'polite' });
  const search = h('input', { type: 'search', id: 'tree-q', placeholder: t('tree.search'), 'aria-label': t('tree.search') });
  const cat = h('select', { id: 'tree-cat', 'aria-label': t('tree.category') }, h('option', { value: '', text: t('tree.allcats') }),
    S.catalog.categories.map((c) => h('option', { value: c.id, text: c.name })));
  const only = h('input', { type: 'checkbox', id: 'tree-only' });
  const tools = h('div', { class: 'tree-tools' }, search, cat,
    h('label', { class: 'check inline' }, only, h('span', { text: t('tree.only') })),
    btn(t('tree.expand'), () => setOpen(true)), btn(t('tree.collapse'), () => setOpen(false)),
    btn(t('kur.all'), () => setAll(true)), btn(t('kur.none'), () => setAll(false)), summary);
  const list = h('div', { class: 'tree', id: 'tree' });
  const empty = h('p', { class: 'muted', hidden: true, text: t('tree.empty') });

  S.catalog.modules.forEach((m) => {
    const ref = { m, open: false, rows: [] };
    ref.cb = h('input', { type: 'checkbox', id: 'tm-' + m.id, 'aria-label': m.name, onchange: (e) => setModule(m, e.target.checked) });
    ref.count = h('span', { class: 'count muted' });
    ref.toggle = h('button', { type: 'button', class: 'ghost twisty', 'aria-expanded': 'false', 'aria-label': t('tree.toggle'), text: '▸', onclick: () => { ref.open = !ref.open; paintOpen(ref); } });
    ref.body = h('div', { class: 'mod-items', hidden: true });
    const mk = reqKinds(m.requires);
    const head = h('div', { class: 'mod-head' }, ref.toggle,
      h('label', { class: 'mod-title' }, ref.cb, h('span', {}, h('b', { text: m.name }), h('small', { class: 'muted', text: m.desc }))),
      h('span', { class: 'badges' }, mk.map(badgeEl)), ref.count);
    m.items.forEach((it) => {
      const row = { it };
      row.cb = h('input', { type: 'checkbox', id: 'ti-' + it.id, 'aria-label': it.name, onchange: (e) => setItem(m, it, e.target.checked) });
      const kinds = it.requires ? reqKinds(it.requires) : mk;
      row.el = h('label', { class: 'item' }, row.cb, h('span', { class: 'item-text' }, h('b', { text: it.name }),
        it.desc ? h('small', { class: 'muted', text: it.desc }) : null,
        h('span', { class: 'badges' }, it.cat ? h('span', { class: 'badge', text: String(it.cat) }) : null, kinds.map(badgeEl))));
      row.hay = (it.name + ' ' + it.desc + ' ' + it.cat).toLowerCase();
      ref.rows.push(row);
      ref.body.append(row.el);
    });
    ref.el = h('div', { class: 'mod', 'data-id': m.id }, head, ref.body);
    ref.hay = (m.name + ' ' + m.desc).toLowerCase();
    T.mods[m.id] = ref;
    list.append(ref.el);
  });

  function paintOpen(ref) {
    const forced = (T.q || T.only) && ref.shown > 0;
    const open = forced || ref.open;
    ref.body.hidden = !open;
    ref.toggle.textContent = open ? '▾' : '▸';
    ref.toggle.setAttribute('aria-expanded', String(open));
  }
  function paintModule(ref) {
    const m = ref.m, on = !!S.sel.modules[m.id];
    let n = 0;
    ref.rows.forEach((r) => {
      r.cb.checked = on && !!S.sel.items[r.it.id];
      r.cb.disabled = !on;
      r.el.classList.toggle('off', !on);
      if (r.cb.checked) n++;
    });
    ref.cb.checked = on;
    ref.el.classList.toggle('off', !on);
    ref.count.textContent = m.items.length ? t('tree.count', { n, m: m.items.length }) : '';
  }
  function paintSummary() {
    const c = counts();
    summary.textContent = t('tree.summary', { m: c.mods, mt: c.modTotal, i: c.items, it: c.total });
  }
  function filter() {
    const q = T.q.trim().toLowerCase();
    let any = false;
    Object.values(T.mods).forEach((ref) => {
      const catOk = !T.cat || ref.m.category === T.cat;
      const modHit = !q || ref.hay.includes(q);
      let shown = 0;
      ref.rows.forEach((r) => {
        const show = (!q || modHit || r.hay.includes(q)) && (!T.only || (S.sel.modules[ref.m.id] && S.sel.items[r.it.id]));
        r.el.hidden = !show;
        if (show) shown++;
      });
      ref.shown = shown;
      const modVisible = catOk && (q || T.only ? (shown > 0 || (modHit && !T.only && !ref.rows.length) || (modHit && T.only && !!S.sel.modules[ref.m.id] && !ref.rows.length)) : true);
      ref.el.hidden = !modVisible;
      if (modVisible) any = true;
      paintOpen(ref);
    });
    empty.hidden = any;
  }
  function setOpen(v) { Object.values(T.mods).forEach((ref) => { ref.open = v; paintOpen(ref); }); }
  function setModule(m, on) {
    const ref = T.mods[m.id];
    S.sel.modules[m.id] = on;
    if (!on) { S.memo[m.id] = m.items.map((i) => [i.id, !!S.sel.items[i.id]]); m.items.forEach((i) => { S.sel.items[i.id] = false; }); }
    else {
      const memo = S.memo[m.id];
      if (memo) memo.forEach(([id, v]) => { S.sel.items[id] = v; }); else m.items.forEach((i) => { S.sel.items[i.id] = true; });
      if (m.items.length && !m.items.some((i) => S.sel.items[i.id])) m.items.forEach((i) => { S.sel.items[i.id] = true; });
    }
    paintModule(ref); paintSummary(); if (T.only) filter(); saveWizardSoon();
  }
  function setItem(m, it, on) {
    S.sel.items[it.id] = on;
    paintModule(T.mods[m.id]); paintSummary(); if (T.only) filter(); saveWizardSoon();
  }
  function setAll(v) {
    const vis = Object.values(T.mods).filter((ref) => !ref.el.hidden);
    vis.forEach((ref) => setModule(ref.m, v));
    if (v) vis.forEach((ref) => ref.m.items.forEach((i) => { S.sel.items[i.id] = true; paintModule(ref); }));
    paintSummary(); if (T.only) filter();
  }
  let timer = null;
  search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => { T.q = search.value; filter(); }, 120); });
  cat.addEventListener('change', () => { T.cat = cat.value; filter(); });
  only.addEventListener('change', () => { T.only = only.checked; filter(); });
  Object.values(T.mods).forEach(paintModule);
  paintSummary();
  filter();
  box.append(tools, list, empty);
}
R.features = (box) => {
  if (S.warnings.length) S.warnings.forEach((w) => box.append(h('p', { class: 'warn', text: '⚠ ' + w })));
  const holder = h('div', {});
  box.append(holder);
  buildTree(holder);
};

/* ================= 4 · Kişisel bilgiler ================= */
R.profile = (box) => {
  if (!S.profile.timezone) S.profile.timezone = guard(() => Intl.DateTimeFormat().resolvedOptions().timeZone) || '';
  const fields = [['name', 'profile.name', true], ['full_name', 'profile.full_name'], ['vault', 'profile.vault'], ['timezone', 'profile.timezone'], ['org', 'profile.org'], ['role', 'profile.role']];
  fields.forEach(([k, label, req]) => {
    const input = h('input', { type: 'text', id: 'pf-' + k, value: S.profile[k] || '', autocomplete: 'off', placeholder: k === 'vault' ? t('profile.vault.ph') : '', oninput: (e) => { S.profile[k] = e.target.value; saveWizardSoon(); } });
    box.append(h('div', { class: 'field' }, h('label', { for: 'pf-' + k, text: t(label) + (req ? ' *' : '') }), h('div', {}, input), h('span')));
  });
  box.append(h('p', { class: 'muted', text: t('profile.note') }));
};
async function saveProfile() {
  if (!S.profile.name.trim()) return true;
  const body = { name: S.profile.name.trim(), full_name: S.profile.full_name.trim() || S.profile.name.trim(), vault: S.profile.vault.trim(), timezone: S.profile.timezone.trim() };
  if (S.profile.org.trim()) body.org = S.profile.org.trim();
  if (S.profile.role.trim()) body.role = S.profile.role.trim();
  const r = await api('/api/profile/basic', body);
  if (!r.ok && r.status !== 404) { showBanner(unavailable(r), 'warn'); return false; }
  return true;
}

/* ================= 5 · Hesaplar ================= */
const IMAP_PRESETS = { gmail: ['imap.gmail.com', 993], outlook: ['outlook.office365.com', 993], icloud: ['imap.mail.me.com', 993], yandex: ['imap.yandex.com', 993], custom: ['', 993] };
const SCOPES = ['gmail', 'calendar', 'contacts', 'drive'];
const SERVICE_GUIDES = { spotify: 4, telegram: 4, tailscale: 4, github: 3 };
const SERVICE_SECRETS = { spotify: [['spotify_client_id', 'svc.spotify.id'], ['spotify_client_secret', 'svc.spotify.secret']], telegram: [['telegram_token', 'svc.telegram.token']], github: [['github_pat', 'svc.github.pat']], tailscale: [] };

function googleGuide() {
  const N = 7;
  let i = 1;
  const card = h('div', { class: 'gscreen' });
  const draw = () => {
    clear(card);
    card.append(h('div', { class: 'gframe' }, h('span', { class: 'gnum', text: String(i) }),
      h('div', {}, h('p', { class: 'muted', text: t('g.screen', { n: i, m: N }) }), h('h4', { text: t('g.' + i + '.t') }), h('p', { text: t('g.' + i + '.x') }))),
    h('div', { class: 'row' }, btn(t('wiz.prev'), () => { i--; draw(); }, 'ghost', { disabled: i <= 1 }),
      btn(t('wiz.next'), () => { i++; draw(); }, 'primary', { disabled: i >= N })));
  };
  draw();
  return card;
}
function googleConnect() {
  const alias = h('input', { type: 'text', id: 'g-alias', value: 'ana', autocomplete: 'off' });
  const on = (s) => S.sel.modules[s] !== false;
  const boxes = SCOPES.map((s) => { const cb = h('input', { type: 'checkbox', id: 'gs-' + s }); cb.checked = on(s) || s === 'gmail'; return cb; });
  const out = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  const go = btn(t('g.connect'), async () => {
    go.disabled = true; msg(out, t('g.connecting'));
    const scopes = SCOPES.filter((s, k) => boxes[k].checked);
    const r = await api('/api/account/google', { alias: alias.value.trim() || 'ana', scopes });
    go.disabled = false;
    if (!r.ok) { msg(out, unavailable(r), 'bad'); return; }
    const d = r.data || {};
    msg(out, d.ok === false ? '✗ ' + (d.error || d.message || t('err.generic')) : '✓ ' + t('g.connected', { email: d.email || '' }), d.ok === false ? 'bad' : 'ok');
    document.dispatchEvent(new CustomEvent('sb-accounts'));
  }, 'primary');
  return h('div', { class: 'panelbox' }, h('h4', { text: t('g.connect.h') }), h('p', { class: 'muted', text: t('g.connect.d') }),
    h('div', { class: 'field' }, h('label', { for: 'g-alias', text: t('acc.alias') }), h('div', {}, alias), h('span')),
    h('div', { class: 'row' }, SCOPES.map((s, k) => h('label', { class: 'check inline' }, boxes[k], h('span', { text: t('scope.' + s) })))),
    h('div', { class: 'row' }, go), out);
}
function imapForm(onSaved) {
  const preset = h('select', { id: 'im-preset' }, Object.keys(IMAP_PRESETS).map((k) => h('option', { value: k, text: t('imap.' + k) })));
  const f = {};
  [['alias', 'acc.alias', 'text'], ['host', 'imap.host', 'text'], ['port', 'imap.port', 'text'], ['user', 'imap.user', 'text'], ['password', 'imap.password', 'password']].forEach(([k, , type]) => {
    f[k] = h('input', { type, id: 'im-' + k, autocomplete: 'off' });
  });
  const fill = () => { const p = IMAP_PRESETS[preset.value]; if (p[0] || preset.value === 'custom') f.host.value = p[0]; f.port.value = String(p[1]); };
  preset.addEventListener('change', fill);
  fill();
  f.alias.value = 'posta';
  const out = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  const save = btn(t('imap.save'), async () => {
    if (!f.user.value || !f.password.value || !f.host.value) { msg(out, t('imap.missing'), 'warn'); return; }
    save.disabled = true; msg(out, t('hes.testing'));
    const r = await api('/api/account/imap', { alias: f.alias.value.trim() || 'posta', preset: preset.value, host: f.host.value.trim(), port: parseInt(f.port.value, 10) || 993, user: f.user.value.trim(), password: f.password.value });
    wipeSecrets();
    save.disabled = false;
    if (!r.ok) { msg(out, unavailable(r), 'bad'); return; }
    const d = r.data || {};
    msg(out, (d.ok === false ? '✗ ' : '✓ ') + (d.message || ''), d.ok === false ? 'bad' : 'ok');
    if (d.ok !== false) onSaved();
  }, 'primary');
  const row = (k, label) => h('div', { class: 'field' }, h('label', { for: 'im-' + k, text: t(label) }), h('div', {}, f[k]), h('span'));
  return h('div', { class: 'panelbox' }, h('h4', { text: t('imap.h') }), h('p', { class: 'muted', text: t('imap.d') }),
    h('div', { class: 'field' }, h('label', { for: 'im-preset', text: t('imap.preset') }), h('div', {}, preset), h('span')),
    row('alias', 'acc.alias'), row('host', 'imap.host'), row('port', 'imap.port'), row('user', 'imap.user'), row('password', 'imap.password'),
    h('div', { class: 'row' }, save), out);
}
function serviceGuides(secrets) {
  return h('div', {}, Object.keys(SERVICE_GUIDES).map((id) => {
    const body = h('div', {}, h('ol', { class: 'guide' }, Array.from({ length: SERVICE_GUIDES[id] }, (_, k) => h('li', { text: t('wiz.' + id + '.' + (k + 1)) }))),
      SERVICE_SECRETS[id].map(([key, label]) => secretRow(key, t(label), !!(secrets && secrets[key]))));
    return h('details', { class: 'howto' }, h('summary', { text: t('wiz.' + id + '.name') }), body);
  }));
}
R.accounts = (box) => {
  if (S.reqs && S.reqs.accounts.length) box.append(h('p', { class: 'hintline', text: t('acc.needed', { list: S.reqs.accounts.join(', ') }) }));
  const list = h('div', { class: 'acc-list' });
  const load = async () => {
    clear(list); list.append(spinner());
    const r = await api('/api/accounts');
    clear(list);
    if (!r.ok || !r.data) { list.append(unavailableBox()); return; }
    const rows = arr(r.data.accounts !== undefined ? r.data.accounts : r.data);
    if (!rows.length) { list.append(h('p', { class: 'muted', text: t('acc.none') })); return; }
    rows.forEach((a) => {
      const alias = a.alias || a.name || '';
      list.append(h('div', { class: 'acc' }, h('b', { text: alias }), h('span', { class: 'muted', text: [a.kind || a.type || a.provider, a.email || a.user].filter(Boolean).join(' · ') }),
        btn(t('acc.remove'), async () => {
          if (!window.confirm(t('acc.confirm', { alias }))) return;
          const rr = await api('/api/account/remove', { alias });
          showBanner(rr.ok ? t('acc.removed') : unavailable(rr), rr.ok ? 'ok' : 'warn');
          load();
        }, 'ghost danger-text')));
    });
  };
  const onAcc = () => { if (list.isConnected) load(); };
  document.addEventListener('sb-accounts', onAcc);
  box.append(h('h3', { text: t('acc.list') }), list);
  load();
  box.append(h('h3', { text: t('g.title') }), h('p', { class: 'muted', text: t('g.intro') }), googleGuide(), googleConnect());
  box.append(h('h3', { text: t('imap.title') }), imapForm(load));
  const svc = h('div', {});
  box.append(h('h3', { text: t('svc.title') }), svc);
  loadSecrets().then((s) => svc.append(serviceGuides(s)));
};

/* ================= 6 · API anahtarları ================= */
const API_KEYS = [['openai', 'OpenAI'], ['anthropic', 'Anthropic'], ['gemini', 'Gemini'], ['openrouter', 'OpenRouter'], ['groq', 'Groq'], ['deepseek', 'DeepSeek'], ['mistral', 'Mistral']];
R.keys = (box) => {
  box.append(h('p', { class: 'muted', text: t('hes.intro') }));
  const wrap = h('div', {});
  box.append(wrap, h('p', { class: 'muted', text: t('keys.test.note') }));
  loadSecrets().then((s) => {
    const have = (k) => !!(s && s[k]);
    API_KEYS.forEach(([id, label]) => wrap.append(secretRow('api-' + id, label, have('api-' + id))));
    const extra = arr(S.reqs && S.reqs.fields).filter((f) => f.secret && !String(f.key).startsWith('api-') && !API_KEYS.some(([id]) => 'api-' + id === f.key));
    if (extra.length) {
      wrap.append(h('h3', { text: t('keys.extra') }));
      extra.forEach((f) => wrap.append(secretRow(f.key, L(f.label) || f.key, have(f.key), L(f.help))));
    }
    if (!s) wrap.prepend(h('p', { class: 'muted', text: t('keys.nostatus') }));
  });
};

/* ================= 7 · Modeller ================= */
function hwView(box) {
  const out = h('div', {});
  box.append(out);
  const load = async () => {
    clear(out); out.append(spinner());
    const r = await api('/api/hardware');
    clear(out);
    if (!r.ok || !r.data) { out.append(h('p', { class: 'muted', text: t('model.none') })); return null; }
    const d = r.data.hardware || r.data;
    const num = (v, u) => (v == null || v === '' ? '—' : (typeof v === 'number' ? Math.round(v * 10) / 10 + ' ' + u : String(v)));
    const gpu = d.gpu && typeof d.gpu === 'object' ? [d.gpu.name, d.gpu.vram_gb != null ? d.gpu.vram_gb + ' GB' : ''].filter(Boolean).join(' · ') : d.gpu;
    const cells = [['model.ram', num(d.ram_gb != null ? d.ram_gb : d.ram, 'GB')],
      ['model.cpu', d.cpu_name || (d.cpu_cores != null ? d.cpu_cores + ' ' + t('model.cores') : d.cpu || '—')],
      ['model.gpu', gpu || (d.vram_gb != null ? num(d.vram_gb, 'GB') : '—')], ['model.disk', num(d.disk_free_gb != null ? d.disk_free_gb : d.disk, 'GB')]];
    out.append(h('div', { class: 'hw' }, cells.map(([k, v]) => h('div', {}, h('b', { text: t(k) }), String(v)))));
    const rec = r.data.recommend || r.data.recommended || d.recommended;
    if (rec) {
      out.append(h('p', {}, h('b', { text: t('model.rec') + ': ' }), typeof rec === 'object' ? [rec.profile, rec.model].filter(Boolean).join(' · ') : String(rec)));
      if (rec.why) out.append(h('p', { class: 'muted', text: String(rec.why) }));
    }
    return rec && typeof rec === 'object' ? rec : null;
  };
  return { load, el: out };
}
R.models = (box) => {
  const hw = hwView(box);
  box.append(btn(t('model.refresh'), () => hw.load()));
  const oll = h('div', { class: 'panelbox' });
  const job = jobPanel();
  const out = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  let rec = null;
  const drawOllama = async () => {
    clear(oll); oll.append(h('h4', { text: t('oll.title') }), spinner());
    const r = await api('/api/ollama');
    clear(oll); oll.append(h('h4', { text: t('oll.title') }));
    if (!r.ok || !r.data) { oll.append(unavailableBox()); return; }
    const d = r.data;
    const installed = d.installed !== undefined ? !!d.installed : !!d.ok;
    oll.append(h('p', { class: installed ? 'ok' : 'warn', text: installed ? t('oll.installed') : t('oll.missing') }));
    if (!installed) {
      oll.append(h('p', { class: 'muted', text: t('oll.installNote') }), btn(t('oll.install'), async () => {
        const rr = await api('/api/ollama/install', {});
        msg(out, rr.ok ? t('oll.installing') : unavailable(rr), rr.ok ? 'muted' : 'bad');
        if (rr.ok) startWatch(drawOllama);
      }, 'primary'));
    }
    const models = arr(d.models).map((m) => (typeof m === 'object' ? m.name || m.model : m));
    oll.append(h('p', { class: 'muted', text: models.length ? t('oll.models', { list: models.join(', ') }) : t('oll.nomodels') }));
    const name = h('input', { type: 'text', id: 'pull-name', placeholder: t('oll.pull.ph'), autocomplete: 'off' });
    const pull = async (n) => {
      if (!n) return;
      const rr = await api('/api/models/pull', { name: n });
      msg(out, rr.ok ? t('oll.pulling', { name: n }) : unavailable(rr), rr.ok ? 'muted' : 'bad');
      if (rr.ok) startWatch(drawOllama);
    };
    oll.append(h('div', { class: 'row' }, name, btn(t('oll.pull'), () => pull(name.value.trim()), 'primary')));
    const names = rec ? [rec.model, rec.vision_model].filter(Boolean) : [];
    if (names.length) oll.append(h('div', { class: 'row' }, h('span', { class: 'muted', text: t('oll.suggested') }), names.map((n) => btn(n, () => pull(n)))));
  };
  hw.load().then((r) => { rec = r; drawOllama(); });
  box.append(oll, out, job.el);
  const gpu = h('input', { type: 'checkbox', id: 'voice-gpu' });
  const vout = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  box.append(h('div', { class: 'panelbox' }, h('h4', { text: t('voice.title') }), h('p', { class: 'muted', text: t('voice.d') }),
    h('label', { class: 'check inline' }, gpu, h('span', { text: t('voice.gpu') })),
    h('div', { class: 'row' }, btn(t('voice.install'), async () => {
      const rr = await api('/api/voice/setup', { gpu: gpu.checked });
      msg(vout, rr.ok ? t('voice.started') : unavailable(rr), rr.ok ? 'muted' : 'bad');
      if (rr.ok) startWatch(null);
    }, 'primary')), vout));
};

/* ================= 8 · MCP ================= */
R.mcp = (box) => {
  const list = h('div', { class: 'cards wide' });
  const out = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  const job = jobPanel();
  const load = async () => {
    clear(list); list.append(spinner());
    const r = await api('/api/mcp');
    clear(list);
    let cat = S.catalog ? S.catalog.mcps : [];
    let installed = [];
    if (r.ok && r.data) {
      const c = r.data.catalog || r.data.mcps;
      if (Array.isArray(c) && c.length) cat = c.map(normMcp);
      installed = arr(r.data.installed).map(idOf);
    } else if (!cat.length) { list.append(unavailableBox()); return; }
    const need = S.reqs ? S.reqs.mcps : [];
    cat.sort((a, b) => (need.includes(b.id) ? 1 : 0) - (need.includes(a.id) ? 1 : 0));
    cat.forEach((m) => list.append(mcpCard(m, installed.includes(m.id) || installed.includes(m.name), need.includes(m.id), out, job, load)));
  };
  box.append(h('p', { class: 'muted', text: t('mcp.intro') }), list, out, job.el, customMcp(out, load));
  load();
};
function mcpCard(m, installed, needed, out, job, reload) {
  const inputs = m.env.map((e) => h('input', { type: e.secret ? 'password' : 'text', id: 'mcp-' + m.id + '-' + e.key, autocomplete: 'off', placeholder: e.key }));
  const doc = m.docs_url && /^https?:\/\//.test(m.docs_url) ? h('a', { href: m.docs_url, target: '_blank', rel: 'noopener noreferrer', text: t('mcp.docs') }) : null;
  const actions = [];
  if (installed) {
    actions.push(btn(t('mcp.remove'), async () => {
      if (!window.confirm(t('mcp.confirm', { name: m.name }))) return;
      const r = await api('/api/mcp/remove', { name: m.id });
      msg(out, r.ok ? t('mcp.removed') : unavailable(r), r.ok ? 'ok' : 'bad');
      reload();
    }, 'ghost'));
  } else if (m.install) {
    actions.push(btn(t('mcp.install'), async () => {
      const env = {};
      m.env.forEach((e, k) => { if (inputs[k].value) env[e.key] = inputs[k].value; });
      const r = await api('/api/mcp/install', { id: m.id, env });
      wipeSecrets();
      msg(out, r.ok ? t('mcp.installing', { name: m.name }) : unavailable(r), r.ok ? 'muted' : 'bad');
      if (r.ok) startWatch(reload);
    }, 'primary'));
  } else {
    actions.push(h('span', { class: 'muted', text: t('mcp.docsonly') }));
  }
  return h('div', { class: 'card static' }, h('b', { text: m.name }), needed ? h('span', { class: 'badge ok', text: t('mcp.needed') }) : null,
    installed ? h('span', { class: 'badge ok', text: t('mcp.installed') }) : null, h('small', { text: m.desc }),
    !installed && m.install ? m.env.map((e, k) => h('label', { class: 'miniField' }, h('span', { text: e.label }), inputs[k])) : null,
    m.note ? h('small', { class: 'muted', text: m.note }) : null, h('div', { class: 'row tight' }, actions, doc));
}
function customMcp(out, reload) {
  const f = {
    name: h('input', { type: 'text', id: 'cm-name', autocomplete: 'off' }), command: h('input', { type: 'text', id: 'cm-command', autocomplete: 'off' }),
    args: h('input', { type: 'text', id: 'cm-args', autocomplete: 'off' }), env: h('textarea', { id: 'cm-env', rows: '3', 'data-secret': 'true', placeholder: 'KEY=value' }),
  };
  const row = (k, label) => h('div', { class: 'field' }, h('label', { for: 'cm-' + k, text: t(label) }), h('div', {}, f[k]), h('span'));
  return h('div', { class: 'panelbox' }, h('h4', { text: t('mcp.custom') }), h('p', { class: 'muted', text: t('mcp.custom.d') }),
    row('name', 'mcp.custom.name'), row('command', 'mcp.custom.command'), row('args', 'mcp.custom.args'), row('env', 'mcp.custom.env'),
    h('div', { class: 'row' }, btn(t('mcp.custom.add'), async () => {
      if (!f.name.value.trim() || !f.command.value.trim()) { msg(out, t('mcp.custom.missing'), 'warn'); return; }
      const env = {};
      f.env.value.split('\n').forEach((ln) => { const i = ln.indexOf('='); if (i > 0) env[ln.slice(0, i).trim()] = ln.slice(i + 1).trim(); });
      const r = await api('/api/mcp/custom', { name: f.name.value.trim(), command: f.command.value.trim(), args: f.args.value.split(/\s+/).filter(Boolean), env });
      wipeSecrets();
      msg(out, r.ok ? t('mcp.custom.ok') : unavailable(r), r.ok ? 'ok' : 'bad');
      if (r.ok) reload();
    }, 'primary')));
}

/* ================= 9 · Veri yükleme ================= */
function previewView(d) {
  const box = h('div', { class: 'preview' });
  if (d == null) return box;
  if (typeof d === 'string') { box.append(h('pre', { class: 'log small', text: d })); return box; }
  const sum = d.summary !== undefined ? d.summary : (d.preview !== undefined ? d.preview : d);
  if (typeof sum === 'string') { box.append(h('pre', { class: 'log small', text: sum })); return box; }
  const rows = Object.entries(sum || {}).filter(([k]) => k !== 'ok');
  const dl = h('dl', { class: 'kv' });
  rows.forEach(([k, v]) => dl.append(h('dt', { text: k }), h('dd', { text: typeof v === 'object' ? JSON.stringify(v) : String(v) })));
  box.append(dl);
  return box;
}
function sourceCard(s, after) {
  const state = { file: null, name: '' };
  const status = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  const prog = h('div', { class: 'progress sm indeterminate', hidden: true }, h('div', { class: 'fill' }));
  const prev = h('div', {});
  const fileIn = h('input', { type: 'file', class: 'sr-only', id: 'file-' + s.id, 'aria-label': t('data.choose') });
  const run = btn(t('data.run'), async () => {
    run.disabled = true; msg(status, t('data.importing'));
    const r = await api('/api/import/run', { source: s.id, file: state.name });
    if (!r.ok) { run.disabled = false; msg(status, unavailable(r), 'bad'); return; }
    msg(status, t('data.running'));
    startWatch((d) => { run.disabled = false; const bad = arr(d && d.steps).some((x) => nstat(x.status) === 'hata'); msg(status, bad ? t('err.generic') : t('data.done'), bad ? 'bad' : 'ok'); after(); });
  }, 'primary', { disabled: true });
  const prevBtn = btn(t('data.preview'), async () => {
    clear(prev); msg(status, t('common.loading'));
    const r = await api('/api/import/preview', { source: s.id, file: state.name });
    if (!r.ok) { msg(status, unavailable(r), 'bad'); return; }
    msg(status, t('data.previewed'), 'ok');
    prev.append(previewView(r.data));
    run.disabled = false;
  }, 'ghost', { disabled: true });
  const take = async (file) => {
    if (!file) return;
    state.file = file; state.name = file.name;
    clear(prev); run.disabled = true; prevBtn.disabled = true; prog.hidden = false;
    msg(status, t('data.uploading', { name: file.name, mb: (file.size / 1048576).toFixed(1) }));
    const r = await uploadRaw(s.id, file);
    prog.hidden = true;
    if (!r.ok) { msg(status, unavailable(r), 'bad'); return; }
    state.name = (r.data && (r.data.name || r.data.file)) || file.name;
    msg(status, t('data.uploaded', { name: state.name }), 'ok');
    prevBtn.disabled = false;
  };
  const drop = h('div', { class: 'drop', tabindex: '0', role: 'button', 'aria-label': t('data.drop') },
    h('span', { text: t('data.drop') }), h('small', { class: 'muted', text: s.formats.length ? t('data.formats', { list: s.formats.join(', ') }) : '' }), fileIn);
  const open = () => fileIn.click();
  drop.addEventListener('click', open);
  drop.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
  ['dragenter', 'dragover'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', (e) => take(e.dataTransfer && e.dataTransfer.files[0]));
  fileIn.addEventListener('click', (e) => e.stopPropagation());
  fileIn.addEventListener('change', () => { take(fileIn.files[0]); fileIn.value = ''; });
  return h('article', { class: 'srccard', 'data-id': s.id },
    h('h4', { text: s.name }), h('p', { class: 'muted', text: s.desc }),
    s.how_to ? h('details', { class: 'howto' }, h('summary', { text: t('data.howto') }), h('div', { class: 'howto-body' }, paras(s.how_to))) : null,
    s.connector ? h('p', { class: 'muted small', text: t('data.connector', { name: s.connector }) }) : null,
    drop, prog, status, h('div', { class: 'row' }, prevBtn, run), prev);
}
R.data = (box) => {
  if (!S.catalog || !S.catalog.sources.length) { box.append(unavailableBox()); return; }
  let all = false;
  const wrap = h('div', { class: 'src-list' });
  const hist = h('div', { class: 'panelbox' });
  const loadHist = async () => {
    clear(hist); hist.append(h('h4', { text: t('data.history') }));
    const r = await api('/api/imports');
    const rows = r.ok && r.data ? arr(r.data.imports !== undefined ? r.data.imports : r.data) : null;
    if (rows == null) { hist.append(unavailableBox()); return; }
    if (!rows.length) { hist.append(h('p', { class: 'muted', text: t('data.history.none') })); return; }
    hist.append(h('ul', { class: 'plain' }, rows.slice(0, 40).map((x) => h('li', { text: typeof x === 'string' ? x : [x.source, x.file || x.name, x.status || x.when || x.date, x.count != null ? t('data.count', { n: x.count }) : ''].filter(Boolean).join(' · ') }))));
  };
  const draw = () => {
    clear(wrap);
    const list = S.catalog.sources.filter((s) => all || sourceNeeded(s.id));
    if (!list.length) wrap.append(h('p', { class: 'muted', text: t('data.nonneeded') }));
    list.forEach((s) => wrap.append(sourceCard(s, loadHist)));
  };
  const needed = S.reqs && S.reqs.imports.length;
  const toggle = h('input', { type: 'checkbox', id: 'data-all', onchange: (e) => { all = e.target.checked; draw(); } });
  box.append(h('p', { class: 'muted', text: t('data.intro') }),
    needed ? h('label', { class: 'check inline' }, toggle, h('span', { text: t('data.showall', { n: S.catalog.sources.length }) })) : null, wrap, hist);
  draw(); loadHist();
};

/* ================= 10 · Telefon ================= */
R.phone = (box) => {
  const view = h('div', { class: 'panelbox' });
  const load = async () => {
    clear(view); view.append(spinner());
    const r = await api('/api/phone');
    clear(view);
    if (!r.ok || !r.data) { view.append(unavailableBox()); return; }
    const d = r.data;
    const tsOk = d.tailscale && typeof d.tailscale === 'object' ? d.tailscale : { installed: d.tailscale_installed, connected: d.tailscale_connected };
    view.append(h('ul', { class: 'plain' },
      h('li', {}, t('phone.installed') + ': ', h('b', { class: tsOk.installed ? 'ok' : 'warn', text: tsOk.installed ? t('common.yes') : t('common.no') })),
      h('li', {}, t('phone.connected') + ': ', h('b', { class: tsOk.connected ? 'ok' : 'warn', text: tsOk.connected ? t('common.yes') : t('common.no') }))));
    if (d.address) view.append(h('p', {}, t('phone.address') + ': ', h('code', { text: String(d.address) })));
    if (d.pair_code || d.code) view.append(h('p', {}, t('phone.code') + ': ', h('code', { class: 'big', text: String(d.pair_code || d.code) })));
    if (!d.address && !d.pair_code && !d.code) view.append(h('p', { class: 'muted', text: t('phone.noserver') }));
  };
  box.append(h('p', { class: 'muted', text: t('phone.intro') }), view, btn(t('phone.refresh'), load));
  box.append(h('details', { class: 'howto' }, h('summary', { text: t('wiz.tailscale.name') }),
    h('ol', { class: 'guide' }, [1, 2, 3, 4].map((k) => h('li', { text: t('wiz.tailscale.' + k) })))));
  load();
};

/* ================= 11 · Başlangıç ================= */
R.startup = (box) => {
  const on = h('input', { type: 'checkbox', id: 'auto-on' });
  const mini = h('input', { type: 'checkbox', id: 'auto-min' });
  const out = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  on.checked = S.auto.on; mini.checked = S.auto.minimized;
  const sync = () => { S.auto.on = on.checked; S.auto.minimized = mini.checked; mini.disabled = !on.checked; saveWizardSoon(); };
  on.addEventListener('change', sync); mini.addEventListener('change', sync);
  mini.disabled = !on.checked;
  api('/api/autostart').then((r) => {
    if (!r.ok || !r.data || MODE !== 'settings') return;
    on.checked = !!r.data.on; mini.checked = r.data.minimized !== false; sync();
  });
  box.append(h('p', { class: 'muted', text: t('auto.intro') }),
    h('label', { class: 'check big' }, on, h('span', {}, h('b', { text: t('auto.on') }), h('small', { class: 'muted', text: t('auto.on.d') }))),
    h('label', { class: 'check' }, mini, h('span', { text: t('auto.min') })), h('p', { class: 'muted', text: t('auto.consent') }));
  if (MODE === 'settings') {
    box.append(h('div', { class: 'row' }, btn(t('auto.save'), async () => {
      const r = await api('/api/autostart', { on: S.auto.on, minimized: S.auto.minimized });
      msg(out, r.ok ? t('auto.saved') : unavailable(r), r.ok ? 'ok' : 'bad');
    }, 'primary')), out);
  }
};
async function applyAutostart() {
  if (!S.auto.on) return;                       // otomatik başlatma YALNIZ kullanıcı "evet" derse
  await api('/api/autostart', { on: true, minimized: S.auto.minimized });
}

/* ================= 12 · Özet → Kur ================= */
R.summary = (box) => {
  const c = counts();
  const body = h('div', {});
  const rows = STEPS.slice(0, 11).map((id, i) => {
    const st = S.skipped[id] ? 'skipped' : (S.visited[id] ? 'done' : 'todo');
    return h('li', { 'data-st': st }, h('button', { type: 'button', class: 'link', text: t('step.' + id + '.t'), onclick: () => goStep(i) }),
      h('span', { class: 'muted', text: ' — ' + t('sum.' + st) }));
  });
  box.append(h('div', { class: 'hw' }, [['sum.modules', c.mods + '/' + c.modTotal], ['sum.items', c.items + '/' + c.total], ['sum.name', S.profile.name || '—'],
    ['sum.auto', S.auto.on ? t('common.yes') : t('common.no')]].map(([k, v]) => h('div', {}, h('b', { text: t(k) }), String(v)))));
  box.append(h('h3', { text: t('sum.steps') }), h('ul', { class: 'plain sumlist' }, rows));
  if (STEPS.slice(0, 11).some((id) => S.skipped[id])) box.append(h('p', { class: 'muted', text: t('sum.later') }));
  const job = jobPanel();
  const fin = h('div', { class: 'panelbox', hidden: true });
  const out = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  const go = btn(t('sum.install'), async () => {
    go.disabled = true;
    await saveProfile();
    await applyAutostart();
    const sel = selectionPayload();
    const r = await api('/api/apply', { selection: { axes: { ...S.axes }, ...sel }, preset: S.axes.meslek || '', ...sel, fields: {} });
    wipeSecrets();
    if (!r.ok && r.status !== 409) { go.disabled = false; msg(out, unavailable(r), 'bad'); return; }
    msg(out, t('kur.applying'));
    S.applied = true;
    startWatch((d) => {
      const stp = arr(d && d.steps).map((s) => nstat(s.status));
      const failed = stp.includes('hata') || !!(d && d.error);
      go.disabled = false;
      if (failed) { msg(out, t('sum.failed'), 'bad'); return; }
      msg(out, t('sum.finished'), 'ok');
      clear(fin);
      fin.append(h('h4', { text: t('sum.done.h') }), h('p', { text: t('sum.done.d') }),
        btn(t('sum.open'), () => { window.open(location.protocol + '//127.0.0.1:8765/', '_blank'); }, 'primary'), btn(t('sum.tour'), startTour));
      fin.hidden = false;
      startTour();
    });
  }, 'primary big', { id: 'btn-install' });
  box.append(h('div', { class: 'row' }, go), out, job.el, fin, body);
};

/* ================= sihirbaz kabuğu ================= */
function saveWizardSoon() {
  if (MODE !== 'wizard') return;
  clearTimeout(S.saveTimer);
  S.saveTimer = setTimeout(saveWizard, 500);
}
async function saveWizard() {
  const sel = selectionPayload();
  await api('/api/wizard', { step: S.step + 1, data: { visited: S.visited, skipped: S.skipped, axes: S.axes, modules: sel.modules, items: sel.items, profile: S.profile, auto: S.auto, lang: S.lang } });
}
async function startWizard(ok) {
  if (!ok) showBanner(t('err.unavailable'), 'warn');
  const r = await api('/api/wizard');
  const d = r.ok && r.data && r.data.data ? r.data.data : null;
  const step = r.ok && r.data ? Number(r.data.step) || 0 : 0;
  if (d && step > 1 && S.catalog) {
    Object.assign(S.axes, d.axes || {});
    S.visited = d.visited || {}; S.skipped = d.skipped || {};
    Object.assign(S.profile, d.profile || {}); Object.assign(S.auto, d.auto || {});
    if (d.modules) {
      S.sel = { modules: {}, items: {} };
      S.catalog.modules.forEach((m) => { S.sel.modules[m.id] = !!d.modules[m.id]; m.items.forEach((i) => { S.sel.items[i.id] = !!(d.items && d.items[i.id]); }); });
    }
    S.step = Math.min(STEPS.length - 1, Math.max(0, step - 1));
    showBanner(t('wiz.resumed', { n: S.step + 1 }), 'ok', { label: t('wiz.restart'), fn: restartWizard });
  } else if (S.presets && S.catalog) {
    await applyCombine();
  }
  renderWizard();
}
async function restartWizard() {
  S.step = 0; S.visited = {}; S.skipped = {}; S.axes = { meslek: '', donanim: '', gizlilik: '', yogunluk: '' };
  await loadPresets();
  if (S.catalog) await applyCombine();
  showBanner('');
  goStep(0);
}
async function goStep(n) {
  S.step = Math.max(0, Math.min(STEPS.length - 1, n));
  renderWizard();
  saveWizardSoon();
}
async function nextStep(skip) {
  const id = STEPS[S.step];
  if (skip) S.skipped[id] = true;
  else { delete S.skipped[id]; S.visited[id] = true; if (id === 'profile' && !(await saveProfile())) return; }
  if (skip) S.visited[id] = true;
  goStep(S.step + 1);
}
let renderToken = 0;
async function renderWizard() {
  const token = ++renderToken;
  const id = STEPS[S.step];
  const nav = $('stepnav');
  clear(nav);
  STEPS.forEach((sid, i) => {
    const st = S.skipped[sid] ? 'skipped' : (S.visited[sid] ? 'done' : (i === S.step ? 'current' : 'todo'));
    nav.append(h('li', { 'data-st': i === S.step ? 'current' : st }, h('button', { type: 'button', class: 'link', 'aria-current': i === S.step ? 'step' : false, onclick: () => goStep(i) },
      h('span', { class: 'dot', text: st === 'done' ? '✓' : (st === 'skipped' ? '–' : String(i + 1)) }), h('span', { text: t('step.' + sid + '.t') }))));
  });
  const pct = Math.round((S.step / (STEPS.length - 1)) * 100);
  $('fill').style.width = pct + '%'; $('pct').textContent = pct + '%'; $('bar').setAttribute('aria-valuenow', String(pct));
  $('stepcount').textContent = t('wiz.step', { n: S.step + 1, m: STEPS.length });
  const body = $('step-body');
  clear(body);
  body.append(h('h2', { text: t('step.' + id + '.t') }), h('p', { class: 'lead', text: t('step.' + id + '.d') }));
  const inner = h('div', { class: 'step-inner' });
  body.append(inner);
  if (NEEDS_REQS.includes(id) && S.catalog) { inner.append(spinner()); await loadReqs(); if (token !== renderToken) return; clear(inner); }
  R[id](inner);
  body.scrollTop = 0;
  const last = S.step === STEPS.length - 1;
  $('nav-back').disabled = S.step === 0;
  $('nav-skip').hidden = last || id === 'welcome';
  $('nav-next').hidden = last;
  $('nav-next').textContent = t('wiz.next');
}
function initWizardNav() {
  $('nav-back').addEventListener('click', () => goStep(S.step - 1));
  $('nav-skip').addEventListener('click', () => nextStep(true));
  $('nav-next').addEventListener('click', () => nextStep(false));
}
window.addEventListener('DOMContentLoaded', initWizardNav);
