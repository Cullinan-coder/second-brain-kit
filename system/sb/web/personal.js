/* Faz 4a Paket P — kişisel işler görünümü `life`: harcama, abonelik, garanti, sağlık, bakım, ruh hali, okuma listesi, hediye */
(function () {
  "use strict";

  // Saf yardımcılar (node ile denenebilir)
  function money(totals) {
    const k = Object.keys(totals || {});
    return k.length ? k.map(function (c) { return Number(totals[c]).toFixed(2) + " " + c; }).join(", ") : "—";
  }
  function barPct(value, max) {
    return max > 0 ? Math.max(2, Math.min(100, Math.round((value / max) * 100))) : 0;
  }
  function daysLabel(d) {
    if (d == null) return "tarih yok";
    return d < 0 ? (-d) + " gün önce" : d === 0 ? "bugün" : d + " gün kaldı";
  }
  if (typeof module !== "undefined") module.exports = { money, barPct, daysLabel };
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
  function btn(label, fn, cls) { return h("button", { type: "button", class: "btn " + (cls || ""), onclick: fn, text: label }); }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  async function call(path, body) {
    try { const r = await window.SB.api(path, body); return r == null ? { error: "boş yanıt" } : r; }
    catch (e) { return { error: String(e && e.message || e) }; }
  }
  function field(ph, extra) { return h("input", Object.assign({ placeholder: ph, "aria-label": ph }, extra || {})); }
  function section(title, body) { return h("section", { class: "card" }, h("h3", { text: title }), body); }
  function empty(t) { return h("p", { class: "empty", text: t }); }
  function loading(box, path, paint) {
    box.append(h("p", { class: "muted", text: "Yükleniyor…" }));
    call(path).then(function (r) {
      box.replaceChildren();
      if (r && r.error) box.append(h("p", { role: "alert", text: r.error })); else paint(r);
    });
  }

  function spendingBox() {
    const box = h("div", {});
    loading(box, "/api/v2/spending", function (s) {
      if (!s.categories.length) return box.append(empty("Bu ay harcama kaydı yok."));
      const max = Math.max.apply(null, s.categories.map(function (c) { return c.totals.TRY || 0; }).concat([1]));
      box.append(h("p", { text: s.month + " toplam: " + money(s.total) }));
      s.categories.forEach(function (c) {
        const spent = c.totals.TRY || 0;
        box.append(h("div", { class: c.over ? "note-warn" : "" },
          h("div", { text: c.category + " — " + money(c.totals) + (c.limit ? " / limit " + c.limit + (c.over ? " (AŞILDI)" : "") : "") }),
          h("div", { class: "meter", role: "img", "aria-label": c.category + " çubuğu" },
            h("div", { class: c.over ? "meter-fill over" : "meter-fill", style: "width:" + barPct(spent, max) + "%" }))));
      });
    });
    return section("Harcama", box);
  }

  function listBox(title, path, emptyText, line) {
    const box = h("div", {});
    loading(box, path, function (rows) {
      if (!rows.length) return box.append(empty(emptyText));
      box.append(rows.map(function (r) { return h("p", { class: r.warn || r.soon ? "note-warn" : "" }, line(r)); }));
    });
    return section(title, box);
  }

  function healthBox() {
    const box = h("div", {});
    loading(box, "/api/v2/health/meds", function (r) {
      if (!r.meds.length && !r.appointments.length) return box.append(empty("İlaç planı ya da randevu yok (config/ilaclar.yaml, 40-Kaynaklar/Sağlık)."));
      r.meds.forEach(function (m) {
        box.append(h("p", {}, m.name + (m.dose ? " (" + m.dose + ")" : "") + " · " + m.times.join(", ") + (m.next ? " · sıradaki " + m.next : ""), " ",
          btn("Takvim önerisi", async function () {
            const x = await call("/api/v2/health/remind", { kind: "med", name: m.name });
            if (x.error) toast(x.error, "error"); else toast("Onay kartı hazır; onaylayınca takvime eklenir");
          })));
      });
      r.appointments.forEach(function (a) {
        box.append(h("p", {}, "Randevu · " + a.title + " · " + a.date + " (" + daysLabel(a.days_left) + ") ",
          btn("Takvim önerisi", async function () {
            const x = await call("/api/v2/health/remind", { kind: "appt", name: a.title });
            if (x.error) toast(x.error, "error"); else toast("Onay kartı hazır; onaylayınca takvime eklenir");
          })));
      });
    });
    return section("Sağlık (yalnız yerel)", box);
  }

  function moodBox() {
    const box = h("div", {}), out = h("div", { role: "status" });
    const level = h("select", { "aria-label": "Ruh hali" }, [1, 2, 3, 4, 5].map(function (n) { return h("option", { value: String(n), text: String(n) }); }));
    const note = field("Not");
    function paint() {
      out.replaceChildren(h("p", { class: "muted", text: "Yükleniyor…" }));
      call("/api/v2/mood?days=30").then(function (m) {
        out.replaceChildren(m.error ? h("p", { role: "alert", text: m.error })
          : m.series.length ? h("div", {}, h("p", { text: "30 gün ortalama: " + m.average + " (" + m.count + " gün)" }),
            h("p", { text: m.series.map(function (s) { return s.level; }).join(" ") })) : empty("Kayıt yok."));
      });
    }
    box.append(h("div", { class: "sbv-toolbar" }, level, note, btn("Kaydet", async function () {
      const r = await call("/api/v2/mood", { level: Number(level.value), note: note.value });
      if (r.error) return toast(r.error, "error");
      toast("Kaydedildi"); note.value = ""; paint();
    }, "primary")), out);
    paint();
    return section("Ruh hali", box);
  }

  function readingBox() {
    const box = h("div", {});
    const title = field("Başlık / bağlantı"), kind = h("select", { "aria-label": "Tür" },
      ["okunacak", "izlenecek"].map(function (k) { return h("option", { value: k, text: k }); }));
    loading(box, "/api/v2/reading-list", function (r) {
      ["okunacak", "izlenecek"].forEach(function (k) {
        box.append(h("h4", { text: k }), r[k].length ? r[k].map(function (i) { return h("p", { text: (i.done ? "✓ " : "• ") + i.title }); }) : empty("Boş."));
      });
      if (r.suggestions.length) box.append(h("h4", { text: "Öneriler" }), r.suggestions.map(function (s) { return h("p", { class: "muted", text: s.source + " · " + s.title }); }));
      box.append(h("div", { class: "sbv-toolbar" }, title, kind, btn("Ekle", async function () {
        const x = await call("/api/v2/reading-list", { title: title.value.trim(), kind: kind.value });
        if (x.error) return toast(x.error, "error");
        toast("Eklendi"); title.value = "";
      }, "primary")));
    });
    return section("Okuma ve izleme listesi", box);
  }

  function giftBox() {
    const person = field("Kişi"), idea = field("Fikir");
    const out = h("div", { role: "status" });
    const list = h("div", {});
    loading(list, "/api/v2/gifts", function (rows) {
      list.append(rows.length ? rows.map(function (g) {
        return h("p", { text: g.person + (g.days_left != null ? " (doğum günü " + daysLabel(g.days_left) + ")" : "") + ": " + g.ideas.join("; ") });
      }) : empty("Hediye fikri yok."));
    });
    return section("Hediye fikirleri", h("div", {}, list, h("div", { class: "sbv-toolbar" }, person, idea, btn("Ekle", async function () {
      const r = await call("/api/v2/gift", { person: person.value.trim(), idea: idea.value.trim() });
      if (r.error) return out.replaceChildren(h("p", { role: "alert", text: r.error }));
      out.replaceChildren(h("p", { text: "Eklendi: " + r.person })); idea.value = "";
    }, "primary")), out));
  }

  function renderLife(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Yaşam" })),
      spendingBox(),
      listBox("Abonelikler", "/api/v2/subscriptions", "Düzenli ödeme bulunamadı.", function (r) {
        return r.vendor + " · " + r.amount + " " + r.currency + " · son " + r.last + " · sonraki ~" + r.next + " (" + daysLabel(r.days_left) + ")";
      }),
      listBox("Garanti", "/api/v2/warranties", "Ürün faturası bulunamadı.", function (r) {
        return (r.warn ? "UYARI · " : "") + r.vendor + " — " + (r.expired ? "garanti bitti " : "bitiş ") + r.ends + " (" + daysLabel(r.days_left) + ")";
      }),
      healthBox(),
      listBox("Bakım", "/api/v2/maintenance", "Bakım kaydı yok (config/bakim.yaml).", function (r) {
        return (r.soon ? "YAKLAŞIYOR · " : "") + r.name + (r.due ? " — " + r.due + " (" + daysLabel(r.days_left) + ")" : "") + (r.km_left != null ? " · " + r.km_left + " km kaldı" : "");
      }),
      moodBox(), readingBox(), giftBox());
  }

  function init() { window.SB.registerView("life", { title: "Yaşam", icon: "heart", render: renderLife }); }
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
