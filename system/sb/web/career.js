/* Faz 3b Paket R — kariyer görünümleri: career (CRM, başvuru panosu, saat, finans, sözleşmeler), study-tools (ders notu, öğretici, kaynakça, yazım) */
(function () {
  "use strict";

  // Saf yardımcılar (node ile denenebilir)
  function money(totals) {
    const k = Object.keys(totals || {});
    return k.length ? k.map(function (c) { return Number(totals[c]).toFixed(2) + " " + c; }).join(", ") : "—";
  }
  function dueLabel(days) {
    if (days == null) return "bitiş tarihi yok";
    return days < 0 ? "bitti (" + (-days) + " gün önce)" : days === 0 ? "bugün bitiyor" : days + " gün kaldı";
  }
  if (typeof module !== "undefined") module.exports = { money, dueLabel };
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
      else if (k === "value") e.value = v;
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
  function field(ph, extra) { return h("input", Object.assign({ placeholder: ph, "aria-label": ph }, extra || {})); }
  function section(title, body) { return h("section", { class: "sbv-card" }, h("h3", { text: title }), body); }
  function pre(text) { return h("pre", { class: "sbv-pre", style: "white-space:pre-wrap" , text: text }); }
  function loading(box, path, paint) {
    box.append(h("p", { class: "sbv-muted", text: "Yükleniyor…" }));
    call(path).then(function (r) {
      box.replaceChildren();
      if (r && r.error) box.append(h("p", { role: "alert", text: r.error })); else paint(r);
    });
  }
  function asyncBtn(label, run, cls) {
    const b = btn(label, async function () { b.disabled = true; try { await run(); } finally { b.disabled = false; } }, cls);
    return b;
  }

  function crmBox() {
    const box = h("div", {});
    loading(box, "/api/v2/crm", function (rows) {
      if (!rows.length) return box.append(h("p", { class: "sbv-empty", text: "Müşteri yok (kişi notuna musteri: true ya da company ekle)." }));
      box.append(rows.map(function (r) {
        return h("p", {}, h("strong", { text: r.name }), r.company ? " (" + r.company + ")" : "",
          " · son iletişim " + (r.last_contact || "—") + " · açık iş " + r.open_jobs.length + " · fatura " + money(r.invoice_total));
      }));
    });
    return section("Müşteriler", box);
  }

  function boardBox() {
    const box = h("div", {});
    loading(box, "/api/v2/applications/board", function (b) {
      box.append(h("div", { class: "sbv-grid" }, b.columns.map(function (c) {
        return h("div", {}, h("h4", { text: c.status + " (" + c.items.length + ")" }),
          c.items.map(function (i) { return h("p", { class: "sbv-muted", text: i.title + (i.due ? " · " + i.due : "") }); }));
      })));
    });
    return section("Başvuru panosu", box);
  }

  function timeBox() {
    const project = field("Proje"), minutes = field("Dakika", { type: "number", min: "1" }), note = field("Not");
    const month = field("Ay (YYYY-AA)", { size: 9 });
    const out = h("div", { role: "status" });
    return section("Saat takibi", h("div", {},
      h("div", { class: "sbv-toolbar" }, project, minutes, note, btn("Kaydet", async function () {
        const r = await call("/api/v2/time", { project: project.value.trim(), minutes: Number(minutes.value), note: note.value });
        if (r.error) return toast(r.error, "error");
        toast("Kaydedildi"); minutes.value = ""; note.value = "";
      }, "sbv-primary")),
      h("div", { class: "sbv-toolbar" }, month, btn("Rapor", async function () {
        const q = "/api/v2/time/report?project=" + encodeURIComponent(project.value.trim()) + "&month=" + encodeURIComponent(month.value.trim());
        const r = await call(q);
        out.replaceChildren(r.error ? h("p", { text: r.error }) : pre(r.text));
      })), out));
  }

  function financeBox() {
    const box = h("div", {});
    loading(box, "/api/v2/finance", function (f) {
      box.append(f.months.length ? f.months.map(function (m) { return h("p", { text: m.month + ": " + money(m.totals) }); })
        : h("p", { class: "sbv-empty", text: "Fatura kaydı yok." }),
        h("h4", { text: "Yaklaşan vergi tarihleri" }),
        f.reminders.map(function (r) { return h("p", { class: "sbv-muted", text: r.date + " · " + r.kind + " (" + r.days_left + " gün)" }); }));
    });
    return section("Gelir/gider ve vergi", box);
  }

  function contractBox() {
    const box = h("div", {});
    loading(box, "/api/v2/contracts", function (rows) {
      if (!rows.length) return box.append(h("p", { class: "sbv-empty", text: "Sözleşme bulunamadı." }));
      box.append(rows.map(function (r) {
        return h("p", { class: r.warn ? "sbv-warn" : "" }, (r.warn ? "UYARI · " : "") + r.title + " — " + dueLabel(r.days_left));
      }));
    });
    return section("Sözleşmeler", box);
  }

  function renderCareer(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Kariyer" })), crmBox(), boardBox(), timeBox(), financeBox(), contractBox());
  }

  function tool(title, inputs, label, path, build, show) {
    const out = h("div", { role: "status" });
    return section(title, h("div", {}, h("div", { class: "sbv-toolbar" }, inputs,
      asyncBtn(label, async function () {
        out.replaceChildren(h("p", { class: "sbv-muted", text: "Çalışıyor…" }));
        const r = await call(path, build());
        out.replaceChildren(r.error ? h("p", { role: "alert", text: r.error }) : show(r));
      }, "sbv-primary")), out));
  }

  function renderStudyTools(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Çalışma araçları" })));
    const nc = field("Ders kodu", { size: 8 }), nsrc = field("Kaynak not yolu (isteğe bağlı)");
    wrap.append(tool("Ders notu üretici", [nc, nsrc], "Özetle", "/api/v2/course-notes",
      function () { return { code: nc.value.trim(), source_path: nsrc.value.trim() }; },
      function (r) { return h("div", {}, h("p", { class: "sbv-muted", text: "Yazıldı: " + r.path }), pre(r.text)); }));
    const tc = field("Ders kodu", { size: 8 }), tq = field("Sorun");
    wrap.append(tool("Öğretici (cevap vermez, ipucu verir)", [tc, tq], "İpucu al", "/api/v2/tutor",
      function () { return { code: tc.value.trim(), question: tq.value.trim() }; },
      function (r) { return pre(r.hint); }));
    const bt = field("Metin, DOI ya da URL");
    wrap.append(tool("Kaynakça", [bt], "Ekle", "/api/v2/bib",
      function () { return { text: bt.value.trim() }; },
      function (r) { return h("div", {}, h("p", { text: "APA: " + r.apa }), h("p", { text: "IEEE: " + r.ieee }), h("p", { class: "sbv-muted", text: "Eklendi: " + r.path })); }));
    const wp = field("Not yolu (örn. 10-Dersler/…/tez.md)");
    const wt = h("select", { "aria-label": "Görev" }, ["outline", "review", "expand"].map(function (t) { return h("option", { value: t, text: t }); }));
    wrap.append(tool("Yazım asistanı", [wp, wt], "Öner", "/api/v2/writing",
      function () { return { path: wp.value.trim(), task: wt.value }; },
      function (r) { return pre(r.suggestion); }));
  }

  function init() {
    window.SB.registerView("career", { title: "Kariyer", icon: "briefcase", render: renderCareer });
    window.SB.registerView("study-tools", { title: "Çalışma araçları", icon: "book", render: renderStudyTools });
  }
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
