/* Paket M: PWA kaydı, çevrimdışı kuyruk (IndexedDB), "kuyrukta N" göstergesi, push aboneliği. Ham HTML yok. */
(function () {
  'use strict';
  const QDB = 'sb-mobile', QST = 'queue';

  function openDb() {
    return new Promise((res, rej) => {
      const r = indexedDB.open(QDB, 1);
      r.onupgradeneeded = () => r.result.createObjectStore(QST, { keyPath: 'id', autoIncrement: true });
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
  }
  function tx(mode, fn) {
    return openDb().then((db) => new Promise((res, rej) => {
      const t = db.transaction(QST, mode); let out;
      Promise.resolve(fn(t.objectStore(QST))).then((v) => { out = v; });
      t.oncomplete = () => { db.close(); res(out); };
      t.onerror = () => { db.close(); rej(t.error); };
    }));
  }
  const reqP = (r) => new Promise((res, rej) => { r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
  const all = () => tx('readonly', (s) => reqP(s.getAll()));
  const add = (item) => tx('readwrite', (s) => reqP(s.add(item)));
  const del = (id) => tx('readwrite', (s) => reqP(s.delete(id)));

  let flushing = false, badge = null;

  async function updateBadge() {
    let n = 0;
    try { n = (await all()).length; } catch (e) { /* IndexedDB yok */ }
    if (!badge && n) {
      badge = document.createElement('div');
      badge.setAttribute('role', 'status'); badge.setAttribute('aria-live', 'polite');
      badge.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:9999;padding:6px 12px;border-radius:16px;background:#374151;color:#fff;font:14px system-ui';
      document.body.appendChild(badge);
    }
    if (badge) { badge.textContent = 'Kuyrukta ' + n; badge.hidden = n === 0; }
    return n;
  }

  /* Tek bir kuyruk öğesini gönderir; true = bitti (silinebilir), false = sonra yeniden dene. */
  async function send(item) {
    try {
      if (item.kind === 'chat') {
        const r = await window.SB.api('/api/v2/chat', { text: item.text });
        return !(r && r.error && !r.status);               // ağ hatası (durum kodu yok) -> yeniden dene
      }
      if (item.kind === 'share') {
        const fd = new FormData();
        Object.keys(item.body || {}).forEach((k) => fd.append(k, item.body[k]));
        if (item.file) fd.append('files', item.file, item.fname || 'paylasim');
        const r = await fetch('/api/v2/share', { method: 'POST', headers: { 'X-SB': '1' }, body: fd });
        return r.ok || (r.status >= 400 && r.status < 500);
      }
    } catch (e) { return false; }
    return true;
  }

  async function flush() {
    if (flushing || navigator.onLine === false) return;
    flushing = true;
    try {
      const items = (await all()).sort((a, b) => a.id - b.id);   // sırayla; biri takılırsa dur
      let done = 0;
      for (const it of items) {
        if (!(await send(it))) break;
        await del(it.id); done++;
      }
      if (done && window.SB && window.SB.toast) window.SB.toast(done + ' bekleyen öğe gönderildi', 'ok');
    } catch (e) { /* sonra */ } finally { flushing = false; updateBadge(); }
  }

  async function enqueueChat(text) {
    await add({ kind: 'chat', text: String(text), ts: Date.now() });
    if (window.SB && window.SB.toast) window.SB.toast('Çevrimdışı: mesaj kuyruğa alındı', 'info');
    updateBadge();
  }

  function wrapSend() {
    const SB = window.SB;
    if (!SB || !SB.sendMessage || SB.sendMessage._queued) return;
    const orig = SB.sendMessage;
    SB.sendMessage = function (text, o) {
      const t = String(text || '').trim();
      if (navigator.onLine === false && t && !(o && o.attachments && o.attachments.length)) { enqueueChat(t); return Promise.resolve(null); }
      return orig.apply(this, arguments);
    };
    SB.sendMessage._queued = true;
  }

  /* ---- push ---- */
  function b64uToBytes(s) {
    const p = '='.repeat((4 - s.length % 4) % 4), b = atob((s + p).replace(/-/g, '+').replace(/_/g, '/'));
    return Uint8Array.from(b, (c) => c.charCodeAt(0));
  }
  async function enablePush() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return { ok: false, reason: 'Tarayıcı push desteklemiyor' };
    if (!window.isSecureContext) return { ok: false, reason: 'HTTPS gerekli (Tailscale serve --https)' };
    const st = await window.SB.api('/api/v2/push/status');
    if (!st || !st.available || !st.public_key) return { ok: false, reason: 'Sunucuda pywebpush yok' };
    if ((await Notification.requestPermission()) !== 'granted') return { ok: false, reason: 'İzin verilmedi' };
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64uToBytes(st.public_key) });
    const r = await window.SB.api('/api/v2/push/subscribe', { subscription: sub.toJSON() });
    return r && r.ok ? { ok: true } : { ok: false, reason: (r && r.error) || 'Abonelik kaydedilemedi' };
  }

  function init() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => null);
      navigator.serviceWorker.addEventListener('message', (e) => {
        if (e.data && e.data.type === 'queued') updateBadge();
        if (e.data && e.data.type === 'flush') flush();
      });
    }
    window.addEventListener('online', flush);
    wrapSend(); updateBadge(); flush();
    if (window.SB) window.SB.mobile = { flush, enqueueChat, enablePush, queueSize: updateBadge };
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(init, 0)); else setTimeout(init, 0);
})();
