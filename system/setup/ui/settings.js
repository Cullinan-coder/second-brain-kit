'use strict';
/* Ayarlar kipi (?mode=settings): sekmeli panel. Sihirbaz adım bileşenleri (R.*) yeniden kullanılır.
   Güncelle / Sağlık / Kaldır / Günlük eski panelden taşındı. Ham HTML dizgesi yok. */
const TABS = ['features', 'accounts', 'keys', 'models', 'mcp', 'data', 'phone', 'startup', 'update', 'health', 'uninstall', 'log'];
const SR = {};

SR.features = (box) => {
  R.features(box);
  const out = h('span', { class: 'msg muted', 'aria-live': 'polite' });
  const job = jobPanel();
  const go = btn(t('kur.apply'), async () => {
    go.disabled = true;
    const sel = selectionPayload();
    const r = await api('/api/apply', { selection: { axes: { ...S.axes }, ...sel }, preset: S.axes.meslek || '', ...sel, fields: {} });
    go.disabled = false;
    if (!r.ok && r.status !== 409) { msg(out, unavailable(r), 'bad'); return; }
    msg(out, r.status === 409 ? t('kur.busy') : t('kur.applying'));
    startWatch((d) => { const bad = arr(d && d.steps).some((s) => nstat(s.status) === 'hata'); msg(out, bad ? t('sum.failed') : t('sum.finished'), bad ? 'bad' : 'ok'); });
  }, 'primary');
  box.append(h('div', { class: 'row stick' }, go, out), job.el);
};
['accounts', 'keys', 'models', 'mcp', 'data', 'phone', 'startup'].forEach((id) => { SR[id] = (box) => R[id](box); });

SR.update = (box) => {
  const view = h('div', {});
  const out = h('p', { class: 'msg muted', 'aria-live': 'polite' });
  const job = jobPanel();
  const load = async () => {
    clear(view);
    const r = await api('/api/update');
    if (!r.ok || !r.data) { view.append(unavailableBox()); return; }
    const d = r.data;
    view.append(h('p', {}, t('upd.current') + ': ', h('b', { text: String(d.current || d.version || '—') })),
      h('p', {}, t('upd.latest') + ': ', h('b', { text: String(d.latest || '—') })));
    const avail = d.update_available !== undefined ? d.update_available : (d.available !== undefined ? d.available : (d.latest && d.current && d.latest !== d.current));
    view.append(h('p', { class: avail ? 'warn' : 'ok', text: avail ? t('upd.available') : t('upd.upToDate') }));
  };
  box.append(view, h('div', { class: 'row' }, btn(t('upd.check'), load), btn(t('upd.run'), async () => {
    const r = await api('/api/update', {});
    msg(out, r.ok ? t('upd.started') : unavailable(r), r.ok ? 'ok' : 'warn');
    if (r.ok) startWatch(load);
  }, 'primary')), out, job.el);
  load();
};

SR.health = (box) => {
  const view = h('div', {});
  const run = async () => {
    clear(view); view.append(spinner());
    const r = await api('/api/health');
    clear(view);
    if (!r.ok || !r.data) { view.append(unavailableBox()); return; }
    const list = Array.isArray(r.data) ? r.data : (r.data.rows || r.data.checks || r.data.items || []);
    if (!list.length) { view.append(h('p', { class: 'muted', text: t('sag.none') })); return; }
    const ul = h('ul', { class: 'steps' });
    list.forEach((c) => {
      const good = c.ok === true || c.status === 'ok' || c.status === 'tamam';
      ul.append(h('li', { 'data-s': good ? 'tamam' : (c.status === 'warn' ? 'calisiyor' : 'hata') }, h('b', { text: String(c.name || c.title || c.id || '') }), ' ' + String(c.hint || c.message || c.detail || '')));
    });
    view.append(ul);
  };
  box.append(btn(t('sag.run'), run, 'primary'), view);
};

SR.uninstall = (box) => {
  const out = h('pre', { class: 'log' });
  const confirmBox = h('input', { type: 'checkbox', id: 'un-confirm' });
  const run = async (confirm) => {
    if (confirm && !confirmBox.checked) { out.textContent = t('kal.needConfirm'); return; }
    const r = confirm ? await api('/api/uninstall', { confirm: true }) : await api('/api/uninstall');
    if (!r.ok || !r.data) { out.textContent = unavailable(r); return; }
    const d = r.data;
    const lines = d.plan || d.actions || d.log || d.items || [];
    const txt = (a) => (a && typeof a === 'object' ? (a.desc || a.id || JSON.stringify(a)) + (a.auto === false ? ' *' : '') : String(a));
    out.textContent = (Array.isArray(lines) ? lines.map(txt).join('\n') : String(lines)) || d.message || JSON.stringify(d, null, 2);
  };
  box.append(h('p', { text: t('kal.warn') }), h('div', { class: 'row' }, btn(t('kal.plan'), () => run(false))),
    h('label', { class: 'check' }, confirmBox, h('span', { text: t('kal.confirm') })),
    h('div', { class: 'row' }, btn(t('kal.do'), () => run(true), 'danger')), out);
};

SR.log = (box) => {
  const job = jobPanel();
  job.el.hidden = false;
  box.append(job.el, btn(t('log.refresh'), async () => { const r = await api('/api/progress'); if (r.ok && r.data) job.update(r.data); }));
  api('/api/progress').then((r) => { if (r.ok && r.data) job.update(r.data); });
};

function showTab(id) {
  S.tab = id;
  renderSettings();
}
async function renderSettings() {
  const tabs = $('tabs');
  clear(tabs);
  TABS.forEach((id) => tabs.append(h('button', { type: 'button', role: 'tab', 'aria-selected': String(id === S.tab), onclick: () => showTab(id), text: t('tab.' + id) })));
  const body = $('tab-body');
  clear(body);
  const wrap = h('div', { class: 'panel' });
  body.append(wrap);
  const id = S.tab;
  if (NEEDS_REQS.includes(id) && S.catalog) { wrap.append(spinner()); await loadReqs(); if (S.tab !== id) return; clear(wrap); }
  wrap.append(h('h2', { text: t('tab.' + id) }));
  SR[id](wrap);
}
async function startSettings(ok) {
  if (!ok) showBanner(t('err.unavailable'), 'warn');
  document.querySelector('.top .progress').hidden = true;
  const r = await api('/api/state');
  const s = r.ok && r.data ? r.data.selection : null;
  if (s && s.modules && S.catalog && !Array.isArray(s.modules)) {
    S.sel = { modules: {}, items: {} };
    S.catalog.modules.forEach((m) => {
      S.sel.modules[m.id] = s.modules[m.id] !== undefined ? !!s.modules[m.id] : m.on;
      m.items.forEach((i) => { S.sel.items[i.id] = s.items && s.items[i.id] !== undefined ? !!s.items[i.id] : S.sel.modules[m.id]; });
    });
  }
  const first = QS.get('tab');
  if (first && TABS.includes(first)) S.tab = first;
  renderSettings();
}
