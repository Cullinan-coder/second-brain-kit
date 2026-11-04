/* Faz 3a Paket K — okul görünümleri: courses (ders panosu + GANO + senaryo), study (çalışma planı) */
(function () {
  "use strict";

  // Saf yardımcı (node ile denenebilir): kalan gün
  function daysLeft(iso, now) {
    if (!iso) return null;
    const a = Date.parse(iso + "T00:00:00"), b = (now || new Date()).setHours(0, 0, 0, 0);
    return isNaN(a) ? null : Math.round((a - b) / 86400000);
  }
  if (typeof module !== "undefined") module.exports = { daysLeft };
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
  function whenLabel(ev) {
    if (!ev) return "—";
    const n = daysLeft(ev.date);
    return ev.date + (n == null ? "" : n === 0 ? " (bugün)" : n > 0 ? " (" + n + " gün)" : " (geçti)") + " · " + (ev.title || "");
  }

  function courseCard(c, onPlan) {
    const exams = (c.exams || []).filter(function (e) { return daysLeft(e.date) >= 0; });
    return h("section", { class: "card" },
      h("h3", { text: c.code + " " + c.name }),
      c.grade ? h("p", { class: "muted", text: "Not: " + c.grade }) : null,
      h("p", { text: "Sıradaki: " + whenLabel(c.next_due) }),
      exams.length ? h("p", { text: "Sınav: " + exams.map(function (e) { return e.date; }).join(", ") }) : null,
      h("p", { class: "muted", text: c.files_count + " dosya · son hareket " + (c.last_activity || "—") }),
      h("div", { class: "sbv-actions" }, btn("Çalışma planı", function () { onPlan(c.code); })));
  }

  function gpaBox(box) {
    const out = h("p", { role: "status", class: "muted" });
    const code = h("input", { placeholder: "Ders kodu", "aria-label": "Ders kodu", size: 8 });
    const grade = h("select", { "aria-label": "Harf notu" }, ["AA", "BA", "BB", "CB", "CC", "DC", "DD", "FD", "FF"].map(function (g) { return h("option", { value: g, text: g }); }));
    const kredi = h("input", { placeholder: "AKTS (yeni ders)", "aria-label": "AKTS", size: 6, type: "number" });
    const changes = [];
    const list = h("div", { class: "muted" });
    function paint() { list.textContent = changes.map(function (c) { return c.code + "=" + c.grade; }).join(", "); }
    const form = h("div", { class: "sbv-toolbar" }, code, grade, kredi,
      btn("Ekle", function () {
        if (!code.value.trim()) return;
        const c = { code: code.value.trim().toUpperCase(), grade: grade.value };
        if (kredi.value) c.credits = Number(kredi.value);
        changes.push(c); code.value = ""; paint();
      }),
      btn("Hesapla", async function () {
        if (!changes.length) return toast("Önce bir değişiklik ekle", "error");
        const r = await call("/api/v2/gpa/what-if", { changes: changes });
        out.textContent = r.error ? r.error : "Senaryo GANO: " + r.gpa + " (şu an " + r.current + ", fark " + r.delta + ")";
      }, "primary"),
      btn("Temizle", function () { changes.length = 0; paint(); out.textContent = ""; }));
    box.append(h("h4", { text: "Senaryo (ya olursa)" }), form, list, out);
  }

  function renderCourses(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Dersler" })));
    const gbox = h("section", { class: "card" }, h("p", { class: "muted", text: "GANO yükleniyor…" }));
    const grid = h("div", { class: "grid" });
    wrap.append(gbox, grid);
    call("/api/v2/gpa").then(function (g) {
      if (g.error) { gbox.replaceChildren(h("p", { text: g.error })); return; }
      gbox.replaceChildren(h("h3", { text: "GANO" }),
        h("p", { text: g.gpa == null ? "Henüz not girilmemiş (config/notlar.yaml)" : g.gpa + " · " + g.credits + " AKTS" }),
        (g.terms || []).map(function (t) { return h("p", { class: "muted", text: t.term + ": " + (t.gpa == null ? "—" : t.gpa) }); }));
      gpaBox(gbox);
    });
    call("/api/v2/courses").then(function (cs) {
      if (cs.error) { grid.replaceChildren(h("p", { text: cs.error })); return; }
      if (!cs.length) { grid.replaceChildren(h("p", { class: "empty", text: "Ders bulunamadı." })); return; }
      cs.sort(function (a, b) { return String((a.next_due || {}).date || "9999").localeCompare(String((b.next_due || {}).date || "9999")); });
      grid.replaceChildren(cs.map(function (c) {
        return courseCard(c, function (code) { window.__sbStudyCode = code; window.SB.openView("study", { code: code }); });
      }));
    });
  }

  function renderStudy(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const code = h("input", { placeholder: "Ders kodu", "aria-label": "Ders kodu", value: window.__sbStudyCode || "" });
    const exam = h("input", { type: "date", "aria-label": "Sınav tarihi" });
    const hours = h("input", { type: "number", min: "0.5", max: "16", step: "0.5", value: "2", "aria-label": "Günlük saat" });
    const res = h("div", {});
    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Çalışma planı" })),
      h("div", { class: "sbv-toolbar" }, code, exam, hours, btn("Plan oluştur", async function () {
        const r = await call("/api/v2/study-plan", { code: code.value.trim(), exam_date: exam.value, hours_per_day: Number(hours.value) });
        if (r.error) return res.replaceChildren(h("p", { text: r.error }));
        toast("Plan notu yazıldı: " + r.path);
        res.replaceChildren(h("p", { class: "muted", text: r.topics + " konu · " + r.path }),
          h("ul", {}, r.plan.map(function (p) { return h("li", {}, h("strong", { text: p.date + " " }), p.hours + " sa — " + p.topics.join("; ")); })));
      }, "primary")), res);
  }

  function init() {
    window.SB.registerView("courses", { title: "Dersler", icon: "book", render: renderCourses });
    window.SB.registerView("study", { title: "Çalışma planı", icon: "calendar", render: renderStudy });
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
