/* Faz 3a Paket V — verimlilik görünümleri: "plan" (bugün) ve "board" (kanban). Ham innerHTML yok: yalnız textContent / SB.md. */
(function () {
  "use strict";

  const CSS = [
    ".pl{display:grid;gap:var(--s3,12px);padding:var(--s3,12px);color:var(--fg,#222)}",
    ".pl h2,.pl h3{margin:0 0 var(--s2,8px)}",
    ".pl-card{background:var(--surface,#fff);border:1px solid var(--border,#ddd);border-radius:10px;padding:var(--s3,12px);min-width:0;overflow-wrap:anywhere}",
    ".pl-muted{color:var(--muted,#666);font-size:.9em}",
    ".pl-row{display:flex;gap:var(--s2,8px);align-items:center;flex-wrap:wrap}",
    ".pl-btn{border:1px solid var(--border,#ccc);background:var(--surface,#fff);color:var(--fg,#222);border-radius:8px;padding:6px 10px;cursor:pointer}",
    ".pl-btn:focus-visible,.pl-kcard:focus-visible{outline:2px solid var(--accent,#2563eb);outline-offset:2px}",
    ".pl-btn.on{background:var(--accent,#2563eb);color:#fff;border-color:var(--accent,#2563eb)}",
    ".pl-warn{border-left:3px solid var(--accent,#d97706);padding-left:var(--s2,8px);margin:4px 0}",
    ".pl-slot{display:grid;grid-template-columns:7.5em 1fr;gap:var(--s2,8px);padding:4px 0;border-bottom:1px solid var(--border,#eee)}",
    ".pl-slot.mola{opacity:.6}.pl-slot.etkinlik{font-weight:600}",
    ".pl-timer{font-size:2em;font-variant-numeric:tabular-nums}",
    ".pl-board{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:var(--s3,12px);padding:var(--s3,12px)}",
    ".pl-col{background:var(--surface,#fff);border:1px solid var(--border,#ddd);border-radius:10px;padding:var(--s2,8px);min-height:8em}",
    ".pl-col.over{outline:2px dashed var(--accent,#2563eb)}",
    ".pl-kcard{border:1px solid var(--border,#ddd);border-radius:8px;padding:var(--s2,8px);margin:var(--s2,8px) 0;cursor:grab;background:var(--surface,#fff)}",
    ".pl-kcard.blocked{opacity:.55}"
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
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  async function call(path, body) {
    try {
      const r = await window.SB.api(path, body);
      return r == null ? { error: "boş yanıt" } : r;
    } catch (e) { return { error: String(e && e.message || e) }; }
  }
  function ensureCss() {
    if (document.getElementById("pl-css")) return;
    const s = document.createElement("style"); s.id = "pl-css"; s.textContent = CSS; document.head.appendChild(s);
  }
  function btn(label, fn, extra) { return h("button", { type: "button", class: "pl-btn" + (extra ? " " + extra : ""), onclick: fn, text: label }); }

  // ---- saf yardımcı (node ile denenebilir) ----
  function fmtClock(sec) {
    sec = Math.max(0, Math.round(sec));
    return String(Math.floor(sec / 60)).padStart(2, "0") + ":" + String(sec % 60).padStart(2, "0");
  }
  const NEXT = { todo: "doing", doing: "done", done: "todo" };

  // ---------- bugün ----------
  function planView(el) {
    ensureCss();
    const wrap = h("div", { class: "pl" });
    el.replaceChildren(wrap);
    let timer = null;

    async function load() {
      wrap.replaceChildren(h("p", { class: "pl-muted", role: "status", text: "Yükleniyor…" }));
      const d = await call("/api/v2/plan/today");
      if (d.error) { wrap.replaceChildren(h("p", { role: "status", text: "Yüklenemedi: " + d.error })); return; }
      wrap.replaceChildren(h("h2", { text: "Bugün" }));
      const top = h("section", { class: "pl-card", "aria-label": "En önemli 3 iş" }, h("h3", { text: "En önemli 3 iş" }));
      if (!d.top3.length) top.append(h("p", { class: "pl-muted", text: "Açık görev yok." }));
      d.top3.forEach(function (t, i) {
        top.append(h("div", { class: "pl-row" }, h("strong", { text: (i + 1) + ". " + t.text }),
          h("span", { class: "pl-muted", text: t.reason || "" }),
          btn("Odaklan", function () { startPomodoro(t); })));
      });
      wrap.append(top);
      if (d.warnings.length) {
        wrap.append(h("section", { class: "pl-card", role: "alert", "aria-label": "Uyarılar" }, h("h3", { text: "Uyarılar" }),
          d.warnings.map(function (w) { return h("div", { class: "pl-warn", text: w }); })));
      }
      const tl = h("section", { class: "pl-card", "aria-label": "Zaman çizelgesi" }, h("h3", { text: "Plan" }));
      if (!d.plan.length) tl.append(h("p", { class: "pl-muted", text: "Plan boş." }));
      d.plan.forEach(function (s) {
        tl.append(h("div", { class: "pl-slot " + s.kind }, h("span", { text: s.start + "–" + s.end }),
          h("span", null, s.title + " ", s.kind === "görev" ? btn("Takvime blokla", function () { block(s); }) : null)));
      });
      wrap.append(tl);
      wrap.append(pomodoroBox(), moodBox(d.mood));
    }

    async function block(s) {
      const day = new Date().toISOString().slice(0, 10);
      const r = await call("/api/v2/plan/block", { title: s.title, start: day + "T" + s.start, end: day + "T" + s.end });
      toast(r.error ? "Blok önerilemedi: " + r.error : "Onay kartı hazır; sohbetten onayla.", r.error ? "error" : "ok");
    }

    const pomo = { task: null, left: 25 * 60, total: 25 * 60 };
    const clock = h("div", { class: "pl-timer", role: "timer", "aria-live": "off", text: fmtClock(pomo.left) });
    const label = h("span", { class: "pl-muted", text: "Görev seçilmedi" });
    function startPomodoro(t) {
      pomo.task = t; label.textContent = t.text; resetTimer(); runTimer();
    }
    function resetTimer() { if (timer) clearInterval(timer); timer = null; pomo.left = pomo.total; clock.textContent = fmtClock(pomo.left); }
    function runTimer() {
      if (timer) return;
      timer = setInterval(async function () {
        pomo.left -= 1; clock.textContent = fmtClock(pomo.left);
        if (pomo.left <= 0) {
          clearInterval(timer); timer = null;
          const r = await call("/api/v2/plan/pomodoro", { task_id: pomo.task ? pomo.task.id : "", minutes: Math.round(pomo.total / 60) });
          toast(r.error ? "Kaydedilemedi: " + r.error : "Odak kaydedildi.", r.error ? "error" : "ok");
          resetTimer();
        }
      }, 1000);
    }
    function pomodoroBox() {
      return h("section", { class: "pl-card", "aria-label": "Pomodoro" }, h("h3", { text: "Pomodoro" }), clock, label,
        h("div", { class: "pl-row" }, btn("Başlat", runTimer), btn("Sıfırla", resetTimer),
          btn("25 dk", function () { pomo.total = 25 * 60; resetTimer(); }), btn("50 dk", function () { pomo.total = 50 * 60; resetTimer(); })));
    }
    function moodBox(cur) {
      const labels = ["Çok düşük", "Düşük", "Orta", "İyi", "Çok iyi"];
      return h("section", { class: "pl-card", "aria-label": "Ruh hali" }, h("h3", { text: "Bugün nasılsın?" }),
        h("div", { class: "pl-row" }, labels.map(function (l, i) {
          return btn((i + 1) + " · " + l, async function () {
            const r = await call("/api/v2/plan/mood", { level: i + 1 });
            toast(r.error ? r.error : "Kaydedildi; plan güncelleniyor.", r.error ? "error" : "ok");
            if (!r.error) load();
          }, cur === i + 1 ? "on" : "");
        })));
    }
    load();
    return function cleanup() { if (timer) clearInterval(timer); };
  }

  // ---------- kanban ----------
  function boardView(el) {
    ensureCss();
    const wrap = h("div", { class: "pl-board" });
    el.replaceChildren(wrap);

    async function move(id, to) {
      const r = await call("/api/v2/tasks/move", { id: id, to: to });
      if (r.error) toast(r.error, "error");
      load();
    }
    function card(c, col) {
      const k = h("div", { class: "pl-kcard" + (c.blocked ? " blocked" : ""), draggable: "true", tabindex: "0", "data-id": c.id,
        "aria-label": c.text + (c.blocked ? " (engelli)" : "") + ". Taşımak için Sağ/Sol ok." },
        h("div", { text: c.text }),
        h("div", { class: "pl-muted", text: [c.due ? "son " + c.due : "", c.project, c.repeat ? "↻ " + c.repeat : "", c.blocked ? "engelli: " + c.after : ""].filter(Boolean).join(" · ") }));
      k.addEventListener("dragstart", function (e) { e.dataTransfer.setData("text/plain", c.id); e.dataTransfer.effectAllowed = "move"; });
      k.addEventListener("keydown", function (e) {
        const order = ["todo", "doing", "done"], i = order.indexOf(col);
        if (e.key === "ArrowRight" && i < 2) { e.preventDefault(); move(c.id, order[i + 1]); }
        else if (e.key === "ArrowLeft" && i > 0) { e.preventDefault(); move(c.id, order[i - 1]); }
        else if (e.key === "Enter") { e.preventDefault(); move(c.id, NEXT[col]); }
      });
      return k;
    }
    function addBox() {
      const input = h("input", { type: "text", placeholder: "Yeni görev…", "aria-label": "Yeni görev", maxlength: "120" });
      const due = h("input", { type: "date", "aria-label": "Son tarih" });
      const go = async function () {
        const text = input.value.trim(); if (!text) return;
        const r = await call("/api/v2/tasks/add", { text: text, due: due.value || undefined });
        if (r.error) toast(r.error, "error"); else { input.value = ""; load(); }
      };
      input.addEventListener("keydown", function (e) { if (e.key === "Enter") go(); });
      return h("div", { class: "pl-row" }, input, due, btn("Ekle", go));
    }
    async function load() {
      const d = await call("/api/v2/tasks/board");
      if (d.error) { wrap.replaceChildren(h("p", { role: "status", text: "Yüklenemedi: " + d.error })); return; }
      wrap.replaceChildren();
      d.columns.forEach(function (col) {
        const box = h("section", { class: "pl-col", "aria-label": col.title }, h("h3", { text: col.title + " (" + col.cards.length + ")" }));
        if (col.id === "todo") box.append(addBox());
        col.cards.forEach(function (c) { box.append(card(c, col.id)); });
        box.addEventListener("dragover", function (e) { e.preventDefault(); box.classList.add("over"); });
        box.addEventListener("dragleave", function () { box.classList.remove("over"); });
        box.addEventListener("drop", function (e) {
          e.preventDefault(); box.classList.remove("over");
          const id = e.dataTransfer.getData("text/plain"); if (id) move(id, col.id);
        });
        wrap.append(box);
      });
    }
    load();
  }

  // ---------- kayıt ----------
  function register() {
    window.SB.registerView("plan", { title: "Bugün planı", icon: "📅", render: planView });
    window.SB.registerView("board", { title: "Görev panosu", icon: "🗂️", render: boardView });
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
  if (typeof module !== "undefined") module.exports = { fmtClock: fmtClock };
})();
