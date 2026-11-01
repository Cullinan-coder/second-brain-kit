/* Faz 4b Paket A — görünüm "automations": kural listesi, aç/kapa, kuru çalıştırma, yeni kural, bekleyen onaylar. Ham innerHTML yok. */
(function () {
  "use strict";

  const CSS = [
    ".au{display:grid;gap:var(--s3,12px);padding:var(--s3,12px);color:var(--fg,#222)}",
    ".au-card{background:var(--surface,#fff);border:1px solid var(--border,#ddd);border-radius:10px;padding:var(--s3,12px);overflow-wrap:anywhere}",
    ".au-muted{color:var(--muted,#666);font-size:.9em}",
    ".au-row{display:flex;gap:var(--s2,8px);align-items:center;flex-wrap:wrap}",
    ".au-btn{border:1px solid var(--border,#ccc);background:var(--surface,#fff);color:var(--fg,#222);border-radius:8px;padding:6px 10px;cursor:pointer}",
    ".au-btn:focus-visible,.au input:focus-visible,.au select:focus-visible{outline:2px solid var(--accent,#2563eb);outline-offset:2px}",
    ".au-warn{border-left:3px solid var(--accent,#d97706);padding-left:var(--s2,8px)}",
    ".au input,.au select{padding:6px;border:1px solid var(--border,#ccc);border-radius:6px;background:var(--surface,#fff);color:var(--fg,#222);max-width:100%}"
  ].join("\n");

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
  async function call(path, body) {
    try { const r = await window.SB.api(path, body); return r == null ? { error: "boş yanıt" } : r; }
    catch (e) { return { error: String(e && e.message || e) }; }
  }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  function btn(label, fn) { return h("button", { type: "button", class: "au-btn", onclick: fn, text: label }); }
  function ensureCss() {
    if (document.getElementById("au-css")) return;
    const s = document.createElement("style"); s.id = "au-css"; s.textContent = CSS; document.head.appendChild(s);
  }

  // saf yardımcı (node ile denenebilir): formdan kural nesnesi
  function buildRule(f) {
    const tetik = { tur: f.trigger };
    if (f.trigger === "zaman") { tetik.saat = f.saat || "09:00"; if (f.gun) tetik.gun = f.gun; }
    if (f.trigger === "webhook") tetik.ad = f.hook;
    if (f.trigger === "not_degisti") tetik.yol = f.yol || "";
    const eylem = { tur: f.action };
    if (f.action === "ozet") eylem.istem = f.text;
    else if (f.action === "bildirim") eylem.baslik = f.text;
    else if (f.action === "whatsapp_taslak") { eylem.kisi = f.kisi || ""; eylem.metin = f.text; }
    else if (f.action === "takvim_oner") eylem.baslik = f.text;
    else eylem.metin = f.text;
    return { ad: f.ad, tetik: tetik, kosul: { alan: "", iceren: f.iceren || "" }, eylem: eylem, acik: true };
  }

  function view(el) {
    ensureCss();
    const wrap = h("div", { class: "au" });
    el.replaceChildren(wrap);

    async function load() {
      wrap.replaceChildren(h("p", { class: "au-muted", role: "status", text: "Yükleniyor…" }));
      const [d, ap] = await Promise.all([call("/api/v2/automations"), call("/api/v2/approvals")]);
      if (d.error) { wrap.replaceChildren(h("p", { role: "alert", text: d.error })); return; }
      const out = [h("h2", { text: "Otomasyonlar" })];

      const pend = ap.approvals || [];
      out.push(h("div", { class: "au-card au-warn" }, h("h3", { text: "Bekleyen onaylar (" + pend.length + ")" }),
        pend.length ? pend.map(function (a) {
          return h("div", { class: "au-row" }, h("span", { text: a.baslik + " — " + a.ayrinti }),
            btn("Onayla", async function () { const r = await call("/api/v2/approvals/decide", { id: a.id, ok: true }); toast(r.error || r.sonuc); load(); }),
            btn("Reddet", async function () { const r = await call("/api/v2/approvals/decide", { id: a.id, ok: false }); toast(r.error || "Reddedildi"); load(); }));
        }) : h("p", { class: "au-muted", text: "Yok. Takvim ve WhatsApp eylemleri yalnız sen onaylayınca yürür." })));

      (d.rules || []).forEach(function (r) {
        const res = h("p", { class: "au-muted", role: "status" });
        out.push(h("div", { class: "au-card" },
          h("div", { class: "au-row" }, h("strong", { text: r.ad }),
            h("span", { class: "au-muted", text: r.tetik.tur + " → " + r.eylem.tur })),
          h("div", { class: "au-row" },
            btn(r.acik ? "Kapat" : "Aç", async function () { await call("/api/v2/automations", { id: r.id, acik: !r.acik }); load(); }),
            btn("Kuru çalıştır", async function () { const t = await call("/api/v2/automations/test", { id: r.id }); res.textContent = t.error || t.yapardi; })),
          res));
      });
      if (!(d.rules || []).length) out.push(h("p", { class: "au-muted", text: "Henüz kural yok." }));

      const f = {};
      function field(key, label, el2) { f[key] = el2; return h("label", { class: "au-row" }, label, el2); }
      function sel(opts) { return h("select", null, opts.map(function (o) { return h("option", { value: o, text: o }); })); }
      const form = h("form", { class: "au-card" }, h("h3", { text: "Yeni kural" }),
        field("ad", "Ad ", h("input", { type: "text", required: true })),
        field("trigger", "Tetik ", sel(d.triggers)), field("saat", "Saat (zaman) ", h("input", { type: "text", placeholder: "09:00" })),
        field("gun", "Gün (isteğe bağlı) ", h("input", { type: "text", placeholder: "pazartesi" })),
        field("hook", "Webhook adı ", h("input", { type: "text" })), field("yol", "Yol filtresi (not) ", h("input", { type: "text" })),
        field("iceren", "Koşul: içeren ", h("input", { type: "text" })),
        field("action", "Eylem ", sel(d.actions)), field("kisi", "Kişi (WhatsApp) ", h("input", { type: "text" })),
        field("text", "Metin / istem ", h("input", { type: "text", required: true })),
        h("p", { class: "au-muted", text: "Metinde {konu}, {gonderen}, {baslik}, {bitis} kullanılabilir. Webhook token: sb set-secret hook-<ad>" }),
        h("button", { type: "submit", class: "au-btn", text: "Ekle" }));
      form.addEventListener("submit", async function (ev) {
        ev.preventDefault();
        const vals = {}; Object.keys(f).forEach(function (k) { vals[k] = f[k].value; });
        const r = await call("/api/v2/automations", buildRule(vals));
        toast(r.error || "Kural eklendi"); if (!r.error) load();
      });
      out.push(form);
      wrap.replaceChildren.apply(wrap, out);
    }
    load();
  }

  function register() { window.SB.registerView("automations", { title: "Otomasyonlar", icon: "⚙️", render: view }); }
  if (window.SB && window.SB.registerView) register();
  else {
    let done = false;
    const go = function () { if (!done && window.SB && window.SB.registerView) { done = true; register(); } };
    document.addEventListener("DOMContentLoaded", go);
    window.addEventListener("load", go);
    const t = setInterval(function () { go(); if (done) clearInterval(t); }, 200);
    setTimeout(function () { clearInterval(t); }, 15000);
  }
  if (typeof module !== "undefined") module.exports = { buildRule: buildRule };
})();
