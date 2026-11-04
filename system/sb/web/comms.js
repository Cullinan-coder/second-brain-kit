/* Faz 3b Paket C — iletişim görünümleri: "inbox" (bekleyenler, takip, bülten, tarihler, ilişki sağlığı, aramalar) ve "drafts" (taslak/çeviri/özet).
   Mail salt okunur: yalnız taslak notu üretir, hiçbir şey göndermez. Ham innerHTML yok: yalnız textContent. */
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
  function btn(label, fn) { return h("button", { type: "button", class: "btn", onclick: fn, text: label }); }

  // ---- saf yardımcı (node ile denenebilir) ----
  function ageText(days) {
    days = Math.max(0, Math.round(days));
    if (days < 30) return days + " gün";
    if (days < 365) return Math.round(days / 30) + " ay";
    return (Math.round(days / 36.5) / 10) + " yıl";
  }

  function section(title, count, list, rowFn, empty) {
    const box = h("section", { class: "card", "aria-label": title }, h("h3", { text: title + (count != null ? " (" + count + ")" : "") }));
    if (!list || !list.length) box.append(h("p", { class: "muted", text: empty }));
    else list.forEach(function (it) { box.append(rowFn(it)); });
    return box;
  }

  // ---------- gelen kutusu ----------
  function inboxView(el) {
    ensureCss();
    const wrap = h("div", { class: "sbv stack" });
    el.replaceChildren(wrap);
    async function load() {
      wrap.replaceChildren(h("p", { class: "muted", role: "status", text: "Yükleniyor…" }));
      const r = await Promise.all([call("/api/v2/awaiting"), call("/api/v2/dates"), call("/api/v2/relationships"),
        call("/api/v2/newsletters"), call("/api/v2/calls/recent")]);
      const aw = r[0], dt = r[1], rel = r[2], nl = r[3], cl = r[4];
      wrap.replaceChildren(h("h2", { text: "İletişim" }));
      if (aw.error) { wrap.append(h("p", { role: "status", text: "Yüklenemedi: " + aw.error })); return; }
      wrap.append(section("Cevap bekleyenler", aw.count, aw.items, function (it) {
        return h("div", { class: "row" },
          h("span", { class: "cm-grow", text: it.to + " — " + (it.subject || "(konusuz)") }),
          h("span", { class: "muted", text: ageText(it.days) }),
          btn("Takip et", async function () {
            const res = await call("/api/v2/followup", { id: it.id, days: 3 });
            toast(res.error ? "Olmadı: " + res.error : "Takip görevi eklendi", res.error ? "error" : "ok");
          }));
      }, "Cevap bekleyen mail yok."));
      wrap.append(section("Önemli tarihler", dt.count, dt.items, function (it) {
        return h("div", { class: "row" }, h("span", { class: "cm-grow", text: it.name + " — " + it.kind }),
          h("span", { class: "muted", text: it.date + " (" + it.in_days + " gün)" }));
      }, "Önümüzdeki 30 günde kayıtlı tarih yok."));
      wrap.append(section("Uzun süredir konuşulmadı", rel.count, (rel.items || []).slice(0, 20), function (it) {
        return h("div", { class: "row" }, h("span", { class: "cm-grow", text: it.name }),
          h("span", { class: "muted", text: ageText(it.days) + " · " + it.channel }));
      }, "Herkesle yakın zamanda konuşulmuş."));
      wrap.append(section("Bülten temizliği önerisi", nl.count, nl.items, function (it) {
        return h("div", { class: "row" }, h("span", { class: "cm-grow", text: (it.name || it.sender) + " <" + it.sender + ">" }),
          h("span", { class: "muted", text: it.count + " mail, %" + Math.round(it.unread_ratio * 100) + " okunmamış · " + it.suggest }));
      }, "Öneri yok.").appendChild(h("p", { class: "muted", text: "Yalnız öneri; abonelikten çıkma yapılmaz." })).parentNode);
      wrap.append(section("Son aramalar (not ekle)", cl.count, cl.items, function (it) {
        return h("div", { class: "row" }, h("span", { class: "cm-grow", text: (it.name || it.number) + " · " + it.type }),
          h("span", { class: "muted", text: it.time }));
      }, "Son 24 saatte arama yok."));
    }
    load();
  }

  // ---------- taslaklar ----------
  function draftsView(el) {
    ensureCss();
    const wrap = h("div", { class: "sbv stack" });
    el.replaceChildren(wrap);
    const to = h("input", { class: "w-full", type: "text", placeholder: "Kime (ad ya da e-posta)", "aria-label": "Kime" });
    const subj = h("input", { class: "w-full", type: "text", placeholder: "Konu", "aria-label": "Konu" });
    const ctx = h("textarea", { class: "w-full", rows: "5", placeholder: "Ne yazılsın? (bağlam)", "aria-label": "Bağlam" });
    const out = h("div", { class: "cm-out", role: "status", "aria-live": "polite" });
    out.hidden = true;
    async function run(label, path, body, pick) {
      out.hidden = false; out.textContent = label + "…";
      const r = await call(path, body);
      out.textContent = r.error ? "Hata: " + r.error : pick(r);
    }
    const tid = h("input", { class: "w-full", type: "text", placeholder: "Zincir kimliği (thread_id)", "aria-label": "Zincir kimliği" });
    const tr = h("textarea", { class: "w-full", rows: "3", placeholder: "Çevrilecek metin", "aria-label": "Çevrilecek metin" });
    wrap.append(h("h2", { text: "Taslaklar" }),
      h("section", { class: "card", "aria-label": "Mail taslağı" }, h("h3", { text: "Mail taslağı (gönderilmez)" }), to, subj, ctx,
        h("div", { class: "row" }, btn("Taslak üret", function () {
          run("Üretiliyor", "/api/v2/draft", { to: to.value, subject: subj.value, context: ctx.value },
            function (r) { return r.text + "\n\nKaydedildi: " + r.path; });
        }))),
      h("section", { class: "card", "aria-label": "Zincir özeti" }, h("h3", { text: "Mail zinciri özeti" }), tid,
        h("div", { class: "row" }, btn("Özetle", function () {
          run("Özetleniyor", "/api/v2/thread-summary?thread_id=" + encodeURIComponent(tid.value), undefined, function (r) {
            return r.summary + "\n\nKararlar:\n- " + (r.decisions.join("\n- ") || "-") + "\n\nİstenenler:\n- " + (r.asks.join("\n- ") || "-");
          });
        }))),
      h("section", { class: "card", "aria-label": "Çeviri" }, h("h3", { text: "Çeviri" }), tr,
        h("div", { class: "row" }, btn("Türkçeye", function () { run("Çevriliyor", "/api/v2/translate", { text: tr.value, to: "tr" }, function (r) { return r.text; }); }),
          btn("İngilizceye", function () { run("Çevriliyor", "/api/v2/translate", { text: tr.value, to: "en" }, function (r) { return r.text; }); }))),
      out);
  }

  // ---------- kayıt ----------
  function register() {
    window.SB.registerView("inbox", { title: "İletişim", icon: "✉️", render: inboxView });
    window.SB.registerView("drafts", { title: "Taslaklar", icon: "📝", render: draftsView });
  }
  if (window.SB && window.SB.registerView) register();
  else {
    let done = false;
    const go = function () { if (!done && window.SB && window.SB.registerView) { done = true; register(); } };
    document.addEventListener("DOMContentLoaded", go);
    window.addEventListener("load", go);
    const t = setInterval(function () { go(); if (done) clearInterval(t); }, 200);
    setTimeout(function () { clearInterval(t); }, 15000);
  }
  if (typeof module !== "undefined") module.exports = { ageText: ageText };
})();
