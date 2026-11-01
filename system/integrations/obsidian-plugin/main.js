'use strict';
const { Plugin, ItemView, Notice, Modal, Setting, PluginSettingTab, requestUrl } = require('obsidian');

const VIEW = 'sb-assistant-view';
const DEFAULTS = { baseUrl: 'http://127.0.0.1:8765' };
const DOWN = 'Second Brain sunucusuna ulaşılamadı. Asistan çalışıyor mu? (127.0.0.1:8765)';

function rid() { return 'obs' + Math.random().toString(36).slice(2, 12); }

async function call(plugin, path, body) {
  const url = plugin.settings.baseUrl.replace(/\/+$/, '') + path;
  const opt = { url, headers: { 'X-SB': '1' }, throw: false };
  if (body !== undefined) { opt.method = 'POST'; opt.contentType = 'application/json'; opt.body = JSON.stringify(Object.assign({ sid: plugin.sid }, body)); }
  else opt.url += (path.includes('?') ? '&' : '?') + 'sid=' + encodeURIComponent(plugin.sid);
  let r;
  try { r = await requestUrl(opt); } catch (e) { return { error: DOWN }; }
  let j; try { j = r.json; } catch (e) { return { error: 'Geçersiz yanıt (' + r.status + ')' }; }
  if (r.status >= 400 && !(j && j.error)) return { error: 'HTTP ' + r.status };
  return j;
}

/* güvenli, küçük markdown: yalnız textContent / createEl */
function renderText(parent, text) {
  String(text == null ? '' : text).split('\n').forEach((ln, i) => {
    if (i) parent.createEl('br');
    const re = /\*\*([^*\n]+)\*\*|`([^`\n]+)`/g; let last = 0, m;
    while ((m = re.exec(ln))) {
      if (m.index > last) parent.appendText(ln.slice(last, m.index));
      if (m[1] != null) parent.createEl('strong', { text: m[1] }); else parent.createEl('code', { text: m[2] });
      last = re.lastIndex;
    }
    if (last < ln.length) parent.appendText(ln.slice(last));
  });
}

class ResultModal extends Modal {
  constructor(app, title, fill) { super(app); this.t = title; this.fill = fill; }
  onOpen() { this.titleEl.setText(this.t); this.contentEl.addClass('sb-modal'); this.fill(this.contentEl); }
  onClose() { this.contentEl.empty(); }
}

class SBView extends ItemView {
  constructor(leaf, plugin) { super(leaf); this.plugin = plugin; }
  getViewType() { return VIEW; }
  getDisplayText() { return 'Second Brain'; }
  getIcon() { return 'brain'; }
  async onOpen() {
    const root = this.contentEl; root.empty(); root.addClass('sb-chat');
    this.log = root.createDiv({ cls: 'sb-log' });
    const row = root.createDiv({ cls: 'sb-input' });
    this.ta = row.createEl('textarea', { attr: { rows: '2', placeholder: 'Beyne sor… (Ctrl+Enter gönder)' } });
    this.btn = row.createEl('button', { text: 'Gönder' });
    this.btn.addEventListener('click', () => this.send());
    this.ta.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); this.send(); } });
    this.bubble('assistant', 'Merhaba, notlarına dayanarak cevaplarım.');
  }
  bubble(role, text) {
    const b = this.log.createDiv({ cls: 'sb-msg sb-' + role });
    renderText(b, text); this.log.scrollTop = this.log.scrollHeight; return b;
  }
  sources(box, list) {
    if (!Array.isArray(list) || !list.length) return;
    const wrap = box.createDiv({ cls: 'sb-sources' });
    list.forEach((s) => {
      const c = wrap.createEl('button', { cls: 'sb-source', text: s.title || s.path || 'kaynak' });
      if (s.snippet) c.setAttr('title', String(s.snippet).slice(0, 200));
      c.addEventListener('click', () => {
        if (s.kind === 'note' && s.path) this.app.workspace.openLinkText(s.path, '', false);
        else new Notice((s.kind || 'kaynak') + ': ' + (s.title || ''));
      });
    });
  }
  async ask(text) {
    this.bubble('user', text);
    const wait = this.bubble('assistant', '…');
    this.btn.disabled = true;
    const r = await call(this.plugin, '/api/v2/chat', { text });
    this.btn.disabled = false;
    wait.empty();
    if (!r || r.error) { renderText(wait, r && r.error ? r.error : DOWN); wait.addClass('sb-err'); return; }
    renderText(wait, (r.reply && r.reply.text) || '(boş cevap)');
    this.sources(wait, r.reply && r.reply.sources);
    if (r.proposals && r.proposals.length) wait.createDiv({ cls: 'sb-note', text: r.proposals.length + ' onay bekleyen öneri var (asistan penceresinde onayla).' });
    this.log.scrollTop = this.log.scrollHeight;
  }
  send() { const t = this.ta.value.trim(); if (!t) return; this.ta.value = ''; this.ask(t); }
}

class SBSettings extends PluginSettingTab {
  constructor(app, plugin) { super(app, plugin); this.plugin = plugin; }
  display() {
    this.containerEl.empty();
    new Setting(this.containerEl).setName('Sunucu adresi').setDesc('Yalnız yerel asistan (varsayılan http://127.0.0.1:8765).')
      .addText((t) => t.setValue(this.plugin.settings.baseUrl).onChange(async (v) => { this.plugin.settings.baseUrl = v.trim() || DEFAULTS.baseUrl; await this.plugin.saveData(this.plugin.settings); }));
  }
}

module.exports = class SBPlugin extends Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULTS, await this.loadData());
    this.sid = rid();
    this.registerView(VIEW, (leaf) => new SBView(leaf, this));
    this.addRibbonIcon('brain', 'Second Brain', () => this.openView());
    this.addSettingTab(new SBSettings(this.app, this));
    this.addCommand({ id: 'open-chat', name: 'Sohbet panelini aç', callback: () => this.openView() });
    this.addCommand({ id: 'ask-selection', name: 'Beyne sor (seçili metinle)', editorCallback: async (ed) => {
      const sel = ed.getSelection().trim();
      if (!sel) { new Notice('Önce bir metin seç.'); return; }
      const v = await this.openView(); if (v) v.ask(sel);
    } });
    this.addCommand({ id: 'summarize-note', name: 'Bu notu özetle', callback: async () => {
      const f = this.app.workspace.getActiveFile();
      if (!f) { new Notice('Açık not yok.'); return; }
      const txt = (await this.app.vault.cachedRead(f)).slice(0, 6000);
      const v = await this.openView(); if (v) v.ask('Şu notu kısaca özetle (ana noktalar, kararlar, yapılacaklar):\n[NOT: ' + f.basename + ']\n' + txt);
    } });
    this.addCommand({ id: 'similar-notes', name: 'Benzer notlar', callback: async () => {
      const f = this.app.workspace.getActiveFile();
      if (!f) { new Notice('Açık not yok.'); return; }
      const body = (await this.app.vault.cachedRead(f)).replace(/^---[\s\S]*?---/, '').trim().slice(0, 300);
      const r = await call(this, '/api/v2/search?k=8&q=' + encodeURIComponent(f.basename + ' ' + body), undefined);
      if (!Array.isArray(r)) { new Notice((r && r.error) || DOWN); return; }
      new ResultModal(this.app, 'Benzer notlar', (el) => {
        if (!list.length) el.createEl('p', { text: 'Benzer not bulunamadı.' });
        list.forEach((s) => {
          const d = el.createDiv({ cls: 'sb-sim' });
          const b = d.createEl('button', { cls: 'sb-source', text: s.title || s.path });
          b.addEventListener('click', () => { if (s.path) this.app.workspace.openLinkText(s.path, '', false); });
          if (s.snippet) d.createEl('div', { cls: 'sb-note', text: String(s.snippet).slice(0, 160) });
        });
      }).open();
    } });
    this.addCommand({ id: 'today-plan', name: 'Bugünün planı', callback: async () => {
      const r = await call(this, '/api/v2/plan/today');
      if (!r || r.error) { new Notice((r && r.error) || DOWN); return; }
      new ResultModal(this.app, 'Bugünün planı', (el) => {
        el.createEl('h4', { text: 'En önemli 3' });
        const ul = el.createEl('ul');
        (r.top3 || []).forEach((t) => ul.createEl('li', { text: t.text + (t.reason ? ' — ' + t.reason : '') }));
        if (!(r.top3 || []).length) ul.createEl('li', { text: 'Görev yok.' });
        el.createEl('h4', { text: 'Akış' });
        const pl = el.createEl('ul');
        (r.plan || []).forEach((p) => pl.createEl('li', { text: p.start + '–' + p.end + '  ' + p.title + ' (' + p.kind + ')' }));
        (r.warnings || []).forEach((w) => el.createDiv({ cls: 'sb-note sb-err', text: String(w) }));
      }).open();
    } });
  }
  async openView() {
    let leaf = this.app.workspace.getLeavesOfType(VIEW)[0];
    if (!leaf) { leaf = this.app.workspace.getRightLeaf(false); await leaf.setViewState({ type: VIEW, active: true }); }
    this.app.workspace.revealLeaf(leaf);
    return leaf.view instanceof SBView ? leaf.view : null;
  }
  onunload() { this.app.workspace.detachLeavesOfType(VIEW); }
};
