/* Paket M: kabuk önbelleği (statik dosyalar), ağ-önce API (API yanıtları ÖNBELLEĞE ALINMAZ), paylaşım hedefi, push. */
'use strict';
const CACHE = 'sb-shell-v2';
const SHELL = ['/', '/static/design.css', '/static/components.css', '/static/views.css', '/static/app.js', '/static/mobile.js', '/static/icon.svg', '/manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => Promise.all(SHELL.map((u) => c.add(u).catch(() => null)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

/* ---- IndexedDB kuyruğu (mobile.js ile ortak: sb-mobile/queue) ---- */
function openDb() {
  return new Promise((res, rej) => {
    const r = indexedDB.open('sb-mobile', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('queue', { keyPath: 'id', autoIncrement: true });
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}
async function enqueue(item) {
  const db = await openDb();
  await new Promise((res, rej) => { const t = db.transaction('queue', 'readwrite'); t.objectStore('queue').add(item); t.oncomplete = res; t.onerror = () => rej(t.error); });
  db.close();
  const cs = await self.clients.matchAll({ includeUncontrolled: true });
  cs.forEach((c) => c.postMessage({ type: 'queued' }));
}

async function handleShare(request) {
  let fd;
  try { fd = await request.formData(); } catch (e) { return Response.redirect('/', 303); }
  try {
    const r = await fetch('/api/v2/share', { method: 'POST', headers: { 'X-SB': '1' }, body: fd });
    if (r.ok) return Response.redirect('/?shared=1', 303);
    if (r.status >= 400 && r.status < 500) return Response.redirect('/?shared=0', 303);   // yeniden denemek işe yaramaz
  } catch (e) { /* ağ yok: kuyruğa */ }
  const fields = {}; let file = null, fname = '';
  for (const [k, v] of fd.entries()) {
    if (typeof v === 'string') fields[k] = v; else if (!file) { file = v; fname = v.name || 'paylasim'; }
  }
  await enqueue({ kind: 'share', body: fields, file, fname, ts: Date.now() });
  return Response.redirect('/?queued=1', 303);
}

self.addEventListener('fetch', (e) => {
  const req = e.request, url = new URL(req.url);
  if (url.origin !== location.origin) return;
  // Paylaşım GET /share önizleme sayfasına gider; kullanıcı 'Beyne at'a basmadan hiçbir şey kaydedilmez
  // (POST yakalamak siteler arası formla kasaya veri yazdırmaya açıktı).
  if (req.method !== 'GET') return;
  if (url.pathname.startsWith('/api/')) return;                 // ağ önce, önbelleksiz: tarayıcıya bırak
  if (url.pathname === '/' || url.pathname.startsWith('/static/') || url.pathname === '/manifest.webmanifest') {
    e.respondWith(fetch(req).then((r) => {
      if (r.ok) { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
      return r;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then((m) => m || new Response('Çevrimdışı', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }))));
  }
});

self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = { title: 'Beyin', body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'Beyin', { body: d.body || '', icon: '/static/icon.svg', data: { link: d.link || '/' } }));
});
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const link = (e.notification.data && e.notification.data.link) || '/';
  const target = /^\/(?!\/)/.test(link) ? link : '/';           // yalnız aynı kaynak
  e.waitUntil(self.clients.matchAll({ type: 'window' }).then((cs) => {
    for (const c of cs) { if ('focus' in c) { c.navigate(target).catch(() => null); return c.focus(); } }
    return self.clients.openWindow(target);
  }));
});
self.addEventListener('sync', (e) => {
  if (e.tag === 'sb-queue') e.waitUntil(self.clients.matchAll({ includeUncontrolled: true }).then((cs) => cs.forEach((c) => c.postMessage({ type: 'flush' }))));
});
