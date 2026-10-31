/* Faz 2 Paket E — hafıza düzenleyici görünümü (153) */
(function () {
  "use strict";

  // Saf yardımcı: bağlam etiketi "(bağlam: proje=X | kişi=Y)" ayrıştır
  function parseContext(text) {
    const m = /\(bağlam:\s*([^)]*)\)/i.exec(String(text || ""));
    if (!m) return {};
    const out = {};
    m[1].split("|").forEach(function (p) {
      const i = p.indexOf("=");
      if (i > 0) out[p.slice(0, i).trim()] = p.slice(i + 1).trim();
    });
    return out;
  }
  const SCOPES = [["all", "Hepsi"], ["hafiza", "Hafıza"], ["kurallar", "Kurallar"], ["kisi", "Kişiler"], ["proje", "Projeler"], ["kavram", "Kavramlar"], ["ogrenim", "Öğrenimler"]];
  if (typeof module !== "undefined") module.exports = { parseContext, SCOPES };
  if (typeof window === "undefined") return;

  function h(tag, props) {
    const e = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (k) {
      const v = props[k];
      if (v == null || v === false) return;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k.slice(0, 2) === "on" && typeof v === "function") e.addEventListener(k.slice(2), v);
      else if (k === "value" || k === "checked" || k === "selected" || k === "disabled") e[k] = v;
      else e.setAttribute(k, v === true ? "" : v);
    });
    for (let i = 2; i < arguments.length; i++) put(e, arguments[i]);
    return e;
  }
  function put(e, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) c.forEach(function (x) { put(e, x); });
    else e.appendChild(c.nodeType ? c : document.createTextNode(String(c)));
  }
  function btn(label, fn, cls) { return h("button", { type: "button", class: "sbv-btn " + (cls || ""), onclick: fn, text: label }); }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  async function call(path, body) {
    try { const r = await window.SB.api(path, body); return r == null ? { error: "boş yanıt" } : r; }
    catch (e) { return { error: String(e && e.message || e) }; }
  }
  function hasRoute(m, p) {
    const r = window.SB && window.SB.routes;
    return !r || typeof r.has !== "function" || r.size === 0 || r.has(m + " " + p);
  }

  function render(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    if (!hasRoute("GET", "/api/v2/memory")) {
      wrap.append(h("div", { class: "sbv-empty", role: "status" }, h("p", { text: "Hafıza ucu bulunamadı." })));
      return;
    }
    let scope = "all", timer = 0;
    const q = h("input", { type: "search", placeholder: "Hafızada ara…", "aria-label": "Hafızada ara" });
    const sel = h("select", { "aria-label": "Kapsam", onchange: function () { scope = sel.value; refresh(); } },
      SCOPES.map(function (s) { return h("option", { value: s[0], text: s[1] }); }));
    const listEl = h("div", { class: "sbv-memlist", "aria-live": "polite" });
    const prefsEl = h("div");
    q.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(refresh, 250); });

    async function refresh() {
      listEl.replaceChildren(h("p", { class: "sbv-muted", text: "Yükleniyor…" }));
      const qs = new URLSearchParams({ scope: scope });
      if (q.value.trim()) qs.set("q", q.value.trim());
      const rows = await call("/api/v2/memory?" + qs.toString());
      if (rows.error) return listEl.replaceChildren(h("p", { class: "sbv-muted", text: "Yüklenemedi: " + rows.error }));
      const arr = Array.isArray(rows) ? rows : (rows.items || []);
      if (!arr.length) return listEl.replaceChildren(h("p", { class: "sbv-muted", text: "Kayıt yok." }));
      listEl.replaceChildren.apply(listEl, arr.map(row));
    }

    function row(m) {
      const textEl = h("div", { class: "sbv-memtext", text: m.text });
      const box = h("article", { class: "sbv-memrow" });
      const meta = h("small", { class: "sbv-muted", text: [m.scope, m.source_path ? m.source_path + (m.line ? ":" + m.line : "") : "", m.added || "", m.context || ""].filter(Boolean).join(" · ") });
      function view() {
        box.replaceChildren(textEl, meta, h("div", { class: "sbv-actions" },
          btn("Düzenle", edit), btn("Sil", del), btn("Unut…", forget)));
      }
      function edit() {
        const ta = h("textarea", { rows: "3", "aria-label": "Hafıza metni" });
        ta.value = m.text;
        box.replaceChildren(ta, h("div", { class: "sbv-actions" },
          btn("Kaydet", async function () {
            const t = ta.value.trim(); if (!t) return;
            const r = await call("/api/v2/memory/update", { id: m.id, text: t });
            if (r.error) toast(r.error, "error"); else { toast("Güncellendi"); refresh(); }
          }, "sbv-primary"), btn("Vazgeç", view)));
        ta.focus();
      }
      function del() {
        box.replaceChildren(h("p", { text: "Bu satır silinsin mi? (Silinen hafıza arşive taşınır.)" }), textEl,
          h("div", { class: "sbv-actions" }, btn("Evet, sil", async function () {
            const r = await call("/api/v2/memory/delete", { id: m.id });
            if (r.error) toast(r.error, "error"); else { toast("Silindi (arşive taşındı)"); refresh(); }
          }, "sbv-danger"), btn("Vazgeç", view)));
      }
      function forget() { askForget(m.text.slice(0, 80)); }
      view();
      return box;
    }

    async function askForget(prefill) {
      const topic = window.prompt("Neyi unutayım? (konu)", prefill || "");
      if (!topic || !topic.trim()) return;
      const r = await call("/api/v2/forget", { sid: window.SB.sid, topic: topic.trim() });
      if (r.error) return toast(r.error, "error");
      const f = r.found || {};
      toast("Bulundu — hafıza: " + (f.memory || 0) + ", not: " + (f.notes || 0) + ", belge: " + (f.docs || 0) + ", sohbet: " + (f.convs || 0) + ". Onay kartı sohbette.");
      if (window.SB.bus) window.SB.bus.emit("forget", r);
    }

    // Ekleme formu
    const addScope = h("select", { "aria-label": "Yeni kayıt kapsamı" }, SCOPES.slice(1).map(function (s) { return h("option", { value: s[0], text: s[1] }); }));
    const addText = h("input", { placeholder: "Yeni hafıza satırı…", "aria-label": "Yeni hafıza" });
    const addCtx = h("input", { placeholder: "Bağlam (isteğe bağlı: proje=X)", "aria-label": "Bağlam" });
    const addForm = h("div", { class: "sbv-toolbar" }, addScope, addText, addCtx, btn("Ekle", async function () {
      const t = addText.value.trim(); if (!t) return;
      const body = { scope: addScope.value, text: t };
      if (addCtx.value.trim()) body.context = addCtx.value.trim();
      const r = await call("/api/v2/memory/add", body);
      if (r.error) toast(r.error, "error"); else { addText.value = addCtx.value = ""; toast("Eklendi"); refresh(); }
    }, "sbv-primary"));

    // Aday tercihler (152)
    async function loadPrefs() {
      if (!hasRoute("GET", "/api/v2/prefs/candidates")) return;
      const c = await call("/api/v2/prefs/candidates");
      const arr = Array.isArray(c) ? c : [];
      if (!arr.length) return prefsEl.replaceChildren();
      prefsEl.replaceChildren(h("section", { class: "sbv-card" }, h("h3", { text: "Öğrendiğim aday tercihler" }),
        arr.map(function (p) {
          return h("div", { class: "sbv-memrow" }, h("div", { text: p.text || p.pref || JSON.stringify(p) }), h("div", { class: "sbv-actions" },
            btn("Onayla", async function () { await call("/api/v2/prefs/decide", { id: p.id, ok: true }); loadPrefs(); refresh(); }, "sbv-primary"),
            btn("Reddet", async function () { await call("/api/v2/prefs/decide", { id: p.id, ok: false }); loadPrefs(); })));
        })));
    }

    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Hafıza" })),
      h("div", { class: "sbv-toolbar" }, sel, q, btn("Konuyu unut…", function () { askForget(q.value); })),
      addForm, prefsEl, listEl);
    refresh();
    loadPrefs();
  }

  function init() { window.SB.registerView("memory", { title: "Hafıza", icon: "brain", render: render }); }
  if (window.SB && window.SB.registerView) init();
  else {
    let done = false;
    const go = function () { if (!done && window.SB && window.SB.registerView) { done = true; init(); } };
    document.addEventListener("DOMContentLoaded", go);
    window.addEventListener("load", go);
    const t = setInterval(function () { go(); if (done) clearInterval(t); }, 200);
    setTimeout(function () { clearInterval(t); }, 15000);
  }
})();
