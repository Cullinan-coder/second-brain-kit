/* Faz 4a Paket G — "privacy" görünümü: veri haritası, bulut sayaçları, izin profili, denetim günlüğü, yedekler, dışa aktarma.
   Ham innerHTML yok: yalnız textContent. Şifreleme/geri yükleme arayüzde YOK (yalnız CLI). */
(function () {
  "use strict";


  function h(tag, attrs) {
    const e = document.createElement(tag);
    for (const k in (attrs || {})) {
      const v = attrs[k];
      if (k === "text") e.textContent = v;
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), v);
      else if (v != null && v !== false) e.setAttribute(k, v === true ? "" : v);
    }
    for (let i = 2; i < arguments.length; i++) {
      const c = arguments[i];
      if (c == null || c === false) continue;
      if (Array.isArray(c)) c.forEach(function (x) { if (x != null) e.append(x.nodeType ? x : document.createTextNode(String(x))); });
      else e.append(c.nodeType ? c : document.createTextNode(String(c)));
    }
    return e;
  }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  async function call(path, body) {
    try {
      const r = await window.SB.api(path, body);
      return r == null ? { error: "boş yanıt" } : r;
    } catch (e) { return { error: String(e && e.message || e) }; }
  }
  function ensureCss() { /* stiller components.css içinde */ }
  function btn(label, fn, extra) { return h("button", { type: "button", class: "btn" + (extra ? " " + extra : ""), onclick: fn, text: label }); }

  // saf yardımcı (node ile denenebilir)
  function fmtBytes(n) {
    if (n == null) return "—";
    if (n < 1024) return n + " B";
    if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
    return (n / 1048576).toFixed(1) + " MB";
  }

  function card(title) { return h("section", { class: "card", "aria-label": title }, h("h3", { text: title })); }

  function privacyView(el) {
    ensureCss();
    const wrap = h("div", { class: "sbv stack" });
    el.replaceChildren(wrap);

    async function load() {
      wrap.replaceChildren(h("p", { class: "muted", role: "status", text: "Yükleniyor…" }));
      const [d, bk] = await Promise.all([call("/api/v2/privacy"), call("/api/v2/backups")]);
      if (d.error) { wrap.replaceChildren(h("p", { role: "status", text: "Yüklenemedi: " + d.error })); return; }
      wrap.replaceChildren(h("h2", { text: "Gizlilik" }));

      const mapC = card("Veri nerede?");
      const vf = d.data_map.vault || {};
      const max = Math.max.apply(null, [1].concat(Object.keys(vf).map(function (k) { return vf[k].bytes; })));
      Object.keys(vf).sort().forEach(function (k) {
        mapC.append(h("div", { class: "row" }, h("span", { text: k + " · " + vf[k].notes + " not · " + fmtBytes(vf[k].bytes) }),
          h("div", { class: "meter-fill", style: "width:" + Math.max(2, Math.round(120 * vf[k].bytes / max)) + "px", "aria-hidden": "true" })));
      });
      mapC.append(h("p", { class: "muted", text: "Gizli (private) not: " + d.private_notes }));
      (d.data_map.data || []).forEach(function (f) { mapC.append(h("div", { class: "muted", text: f.name + " · " + (f.note || fmtBytes(f.bytes)) })); });
      wrap.append(mapC);

      const cloud = card("Buluta giden");
      cloud.append(h("p", { text: "Son " + d.usage.days + " günde " + d.usage.calls + " bulut çağrısı." }));
      Object.keys(d.usage.tasks).forEach(function (t) { cloud.append(h("div", { class: "muted", text: t + ": " + d.usage.tasks[t] })); });
      cloud.append(h("p", { class: "muted", text: "Açık bulut sağlayıcıları: " + (d.providers.cloud.join(", ") || "yok (hepsi yerel)") }));
      cloud.append(h("p", { class: "muted", text: "Kişi bilgisi maskeleme: " + (d.mask_contacts ? "açık" : "kapalı") }));
      wrap.append(cloud);

      const perm = card("İzin profili");
      const row = h("div", { class: "row", role: "group", "aria-label": "Profil" });
      Object.keys(d.permissions.profiles).forEach(function (p) {
        row.append(btn(p, async function () {
          const r = await call("/api/v2/permissions", { profile: p });
          toast(r.error ? "Seçilemedi: " + r.error : "Profil: " + p, r.error ? "error" : "ok");
          load();
        }, p === d.permissions.profile ? "on" : ""));
      });
      perm.append(row);
      const need = d.permissions.needs_approval;
      perm.append(h("p", { class: "muted", text: Object.keys(need).map(function (a) { return a + ": " + (need[a] ? "onay ister" : "serbest"); }).join(" · ") }));
      wrap.append(perm);

      const aud = card("Denetim günlüğü");
      const q = h("input", { type: "search", placeholder: "Ara…", "aria-label": "Günlükte ara" });
      const list = h("div", { "aria-live": "polite" });
      async function search() {
        const r = await call("/api/v2/audit?limit=50&q=" + encodeURIComponent(q.value));
        list.replaceChildren();
        if (r.error) { list.append(h("p", { text: "Yüklenemedi: " + r.error })); return; }
        if (!r.entries.length) list.append(h("p", { class: "muted", text: "Kayıt yok." }));
        r.entries.forEach(function (e) { list.append(h("div", { class: "pv-log", text: [e.ts, e.actor, e.action, e.path, e.detail].filter(Boolean).join(" · ") })); });
      }
      q.addEventListener("keydown", function (ev) { if (ev.key === "Enter") search(); });
      aud.append(h("div", { class: "row" }, q, btn("Ara", search)), list);
      wrap.append(aud);
      search();

      const bkc = card("Yedekler");
      bkc.append(h("div", { class: "row" }, btn("Şimdi yedekle", async function () {
        const r = await call("/api/v2/backups/create", {});
        toast(r.error ? "Yedeklenemedi: " + r.error : "Yedek alındı", r.error ? "error" : "ok");
        load();
      }), btn("Kasayı dışa aktar", async function () {
        const r = await call("/api/v2/export", { scope: "vault" });
        toast(r.error ? "Aktarılamadı: " + r.error : "Hazır: " + r.name, r.error ? "error" : "ok");
      }), btn("Hepsini dışa aktar", async function () {
        const r = await call("/api/v2/export", { scope: "all" });
        toast(r.error ? "Aktarılamadı: " + r.error : "Hazır: " + r.name, r.error ? "error" : "ok");
      })));
      (bk.zips || []).forEach(function (z) { bkc.append(h("div", { class: "muted", text: z.name + " · " + fmtBytes(z.bytes) + " · " + z.kind })); });
      (bk.commits || []).slice(0, 5).forEach(function (c) { bkc.append(h("div", { class: "muted", text: "git " + c })); });
      bkc.append(h("p", { class: "muted", text: "Geri yükleme ve şifreleme yalnız komut satırından: sb restore <yedek> --confirm" }));
      wrap.append(bkc);
    }
    load();
  }

  function register() { window.SB.registerView("privacy", { title: "Gizlilik", icon: "🔒", render: privacyView }); }
  if (window.SB && window.SB.registerView) register();
  else {
    let done = false;
    const go = function () { if (!done && window.SB && window.SB.registerView) { done = true; register(); } };
    document.addEventListener("DOMContentLoaded", go);
    window.addEventListener("load", go);
    const t = setInterval(function () { go(); if (done) clearInterval(t); }, 200);
    setTimeout(function () { clearInterval(t); }, 15000);
  }
  if (typeof module !== "undefined") module.exports = { fmtBytes: fmtBytes };
})();
