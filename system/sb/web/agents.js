/* Faz 4b Paket J — ajan görünümleri: agents (pazar + çalıştır + çıktı), agent-runs (izleme paneli, gece raporu) */
(function () {
  "use strict";

  function runLabel(r) {
    return (r.ajan || "?") + " · " + (r.durum || "?") + " · " + (r.adim || 0) + " adım" + (r.reddedilen ? " · " + r.reddedilen + " red" : "");
  }
  if (typeof module !== "undefined") module.exports = { runLabel };
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
  async function call(path, body) {
    try { const r = await window.SB.api(path, body); return r == null ? { error: "boş yanıt" } : r; }
    catch (e) { return { error: String(e && e.message || e) }; }
  }
  function section(title, body) { return h("section", { class: "sbv-card" }, h("h3", { text: title }), body); }
  function pre(text) { return h("pre", { class: "sbv-pre", style: "white-space:pre-wrap", text: text }); }
  function loading(box, path, paint) {
    box.append(h("p", { class: "sbv-muted", text: "Yükleniyor…" }));
    call(path).then(function (r) {
      box.replaceChildren();
      if (r && r.error) box.append(h("p", { role: "alert", text: r.error })); else paint(r);
    });
  }

  function agentCard(a) {
    if (a.durum === "yakında") return h("div", { class: "sbv-card" }, h("strong", { text: a.ad }), h("p", { class: "sbv-muted", text: a.aciklama }));
    const input = h("input", { placeholder: "Girdi", "aria-label": "Girdi " + a.ad });
    const web = a.id === "arastirmaci" ? h("input", { type: "checkbox", "aria-label": "Web de ara" }) : null;
    const out = h("div", { role: "status" });
    const run = btn("Çalıştır", async function () {
      run.disabled = true;
      out.replaceChildren(h("p", { class: "sbv-muted", text: "Çalışıyor…" }));
      const r = await call("/api/v2/agents/run", { id: a.id, input: input.value.trim(), web: !!(web && web.checked) });
      out.replaceChildren(r.error ? h("p", { role: "alert", text: r.error })
        : h("div", {}, h("p", { class: "sbv-muted", text: "Sonuç notu: " + r.cikti + " (" + runLabel(r) + ")" }), pre(r.text)));
      run.disabled = false;
    }, "sbv-primary");
    return h("div", { class: "sbv-card" }, h("strong", { text: a.ad }),
      h("p", { class: "sbv-muted", text: a.aciklama + " · araçlar: " + a.araclar.join(", ") }),
      h("div", { class: "sbv-toolbar" }, input, web, web ? h("span", { text: "web" }) : null, run), out);
  }

  function codeBox() {
    const task = h("input", { placeholder: "Gece yapılacak kod işi", "aria-label": "Kod işi" });
    const where = h("input", { placeholder: "Klasör (isteğe bağlı)", "aria-label": "Klasör" });
    const out = h("div", { role: "status" });
    return section("Kod ajanı (yalnız gece listesine ekler)", h("div", {}, h("div", { class: "sbv-toolbar" }, task, where,
      btn("Gece listesine ekle", async function () {
        const r = await call("/api/v2/agents/code", { task: task.value.trim(), where: where.value.trim() });
        out.replaceChildren(h("p", { role: r.error ? "alert" : "status", text: r.error || r.message }));
      }, "sbv-primary")), out));
  }

  function renderAgents(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const box = h("div", {});
    loading(box, "/api/v2/agents", function (rows) { box.append(rows.map(agentCard)); });
    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Ajanlar" })), box, codeBox());
  }

  function renderRuns(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const runs = h("div", {}), night = h("div", {});
    loading(runs, "/api/v2/agent-runs", function (rows) {
      runs.append(rows.length ? rows.map(function (r) {
        return h("p", { class: r.durum === "hata" ? "sbv-warn" : "" }, (r.baslangic || "") + " · " + runLabel(r) + (r.cikti ? " → " + r.cikti : ""));
      }) : h("p", { class: "sbv-empty", text: "Henüz ajan çalışması yok." }));
    });
    loading(night, "/api/v2/night-report", function (r) {
      night.append(h("p", { text: r.summary }),
        r.failed.length ? h("div", {}, h("h4", { text: "Hatalı" }), r.failed.map(function (t) { return h("p", { class: "sbv-warn", text: t }); })) : null,
        h("h4", { text: "Onay bekleyen değişiklikler" }),
        r.approvals.length ? r.approvals.map(function (a) { return h("p", { class: "sbv-muted", text: a.oge + " · " + a.islem + " " + a.ayrinti }); })
          : h("p", { class: "sbv-empty", text: "Yok." }),
        r.log_tail.length ? pre(r.log_tail.join("\n")) : null);
    });
    wrap.append(h("header", { class: "sbv-head" }, h("h2", { text: "Ajan izleme" })), section("Çalışmalar", runs), section("Gece raporu", night));
  }

  function init() {
    window.SB.registerView("agents", { title: "Ajanlar", icon: "bot", render: renderAgents });
    window.SB.registerView("agent-runs", { title: "Ajan izleme", icon: "activity", render: renderRuns });
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
