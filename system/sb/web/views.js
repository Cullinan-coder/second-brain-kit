/* Faz 2 Paket E — görünümler: dashboard, graph, timeline, person, project, cards, settings, errors, learn, journal */
(function () {
  "use strict";

  // ---------- saf yardımcılar (node ile denenebilir) ----------

  // Kuvvet yönlendirmeli yerleşimin tek adımı. nodes: {x,y,vx,vy,fixed}, edges: {a,b,w} (indeks)
  function forceStep(nodes, edges, o) {
    o = o || {};
    const k = o.k || 60, alpha = o.alpha == null ? 1 : o.alpha;
    const gravity = o.gravity == null ? 0.02 : o.gravity, damping = o.damping || 0.85;
    const cx = o.cx || 0, cy = o.cy || 0, n = nodes.length;
    const maxd2 = (k * 6) * (k * 6), k2 = k * k * alpha;
    const fx = new Float64Array(n), fy = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < n; j++) {
        const b = nodes[j];
        let dx = a.x - b.x, dy = a.y - b.y;
        let d2 = dx * dx + dy * dy;
        if (d2 > maxd2) continue;
        if (d2 < 0.01) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = 0.5; }
        const f = k2 / d2;
        fx[i] += dx * f; fy[i] += dy * f; fx[j] -= dx * f; fy[j] -= dy * f;
      }
    }
    for (const e of edges) {
      const a = nodes[e.a], b = nodes[e.b];
      if (!a || !b) continue;
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const w = Math.min(3, e.w || 1);
      const f = (d - k) * 0.06 * w * alpha / d;
      fx[e.a] += dx * f; fy[e.a] += dy * f; fx[e.b] -= dx * f; fy[e.b] -= dy * f;
    }
    let energy = 0;
    for (let i = 0; i < n; i++) {
      const a = nodes[i];
      if (a.fixed) { a.vx = a.vy = 0; continue; }
      fx[i] += (cx - a.x) * gravity; fy[i] += (cy - a.y) * gravity;
      a.vx = (a.vx + fx[i]) * damping; a.vy = (a.vy + fy[i]) * damping;
      const sp = Math.sqrt(a.vx * a.vx + a.vy * a.vy);
      if (sp > 40) { a.vx *= 40 / sp; a.vy *= 40 / sp; }
      a.x += a.vx; a.y += a.vy;
      energy += a.vx * a.vx + a.vy * a.vy;
    }
    return energy;
  }

  // SM-2 düğme -> not (0..5)
  const GRADE_MAP = { tekrar: 1, zor: 3, iyi: 4, kolay: 5 };
  function gradeFor(label) {
    if (typeof label === "number") return Math.max(0, Math.min(5, Math.round(label)));
    const g = GRADE_MAP[String(label || "").toLowerCase().replace(/İ/g, "i")];
    return g == null ? 4 : g;
  }

  function safeUrl(u) {
    try {
      const x = new URL(String(u), "http://x.invalid");
      return ["http:", "https:", "obsidian:"].includes(x.protocol) ? String(u) : "";
    } catch (e) { return ""; }
  }
  function obsidianUrl(path) {
    return "obsidian://open?vault=SecondBrain&file=" + encodeURIComponent(String(path || ""));
  }
  function qs(obj) {
    const p = new URLSearchParams();
    Object.keys(obj).forEach(function (k) { if (obj[k] !== undefined && obj[k] !== null && obj[k] !== "") p.set(k, obj[k]); });
    const s = p.toString();
    return s ? "?" + s : "";
  }
  const KIND_COLORS = { kisi: "#e07a5f", proje: "#3d85c6", ders: "#81b29a", kavram: "#c9a227", other: "#8a8f98" };
  function kindColor(k) { return KIND_COLORS[k] || KIND_COLORS.other; }

  const api_ = { forceStep, gradeFor, safeUrl, obsidianUrl, qs, kindColor };
  if (typeof module !== "undefined") module.exports = api_;
  if (typeof window === "undefined") return;
  window.SBViews = api_;

  // ---------- DOM yardımcıları ----------
  function h(tag, props) {
    const e = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (k) {
      const v = props[k];
      if (v == null || v === false) return;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k.slice(0, 2) === "on" && typeof v === "function") e.addEventListener(k.slice(2), v);
      else if (k === "value" || k === "checked" || k === "disabled" || k === "selected") e[k] = v;
      else e.setAttribute(k, v === true ? "" : v);
    });
    for (let i = 2; i < arguments.length; i++) add(e, arguments[i]);
    return e;
  }
  function add(e, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) c.forEach(function (x) { add(e, x); });
    else e.appendChild(c.nodeType ? c : document.createTextNode(String(c)));
  }
  function link(label, url) {
    const u = safeUrl(url);
    if (!u) return document.createTextNode(String(label));
    return h("a", { href: u, target: "_blank", rel: "noopener noreferrer", text: label });
  }
  function btn(label, fn, cls) {
    return h("button", { type: "button", class: "sbv-btn " + (cls || ""), onclick: fn, text: label });
  }
  function noteLink(title, path) { return link(title || path, obsidianUrl(path)); }
  function section(title, body, cls) {
    return h("section", { class: "sbv-card " + (cls || ""), "aria-label": title }, h("h3", { text: title }), body);
  }
  function list(items, fn) {
    if (!items || !items.length) return h("p", { class: "sbv-muted", text: "Boş." });
    return h("ul", { class: "sbv-list" }, items.map(function (x) { return h("li", null, fn(x)); }));
  }
  function md(text) {
    const SB = window.SB;
    if (SB && SB.md) return SB.md(String(text || ""));
    return h("span", { text: String(text || "") });
  }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  function hasRoute(method, path) {
    const r = window.SB && window.SB.routes;
    if (!r || typeof r.has !== "function" || r.size === 0) return true;
    return r.has(method + " " + path);
  }
  async function call(path, body) {
    try {
      const r = await window.SB.api(path, body);
      return r == null ? { error: "boş yanıt" } : r;
    } catch (e) { return { error: String(e && e.message || e) }; }
  }
  function emptyState(el, msg) {
    el.replaceChildren(h("div", { class: "sbv-empty", role: "status" }, h("p", { text: msg })));
  }
  // Ortak yükleyici: uç yoksa/hata varsa boş durum, yoksa render(data)
  async function load(el, path, render) {
    const base = path.split("?")[0];
    if (!hasRoute("GET", base)) return emptyState(el, "Bu görünüm için sunucu ucu yok (" + base + ").");
    el.replaceChildren(h("p", { class: "sbv-muted", role: "status", text: "Yükleniyor…" }));
    const r = await call(path);
    if (r.error) return emptyState(el, "Yüklenemedi: " + r.error);
    if (r.available === false) return emptyState(el, r.hint || "Bu özellik kurulu değil.");
    try { render(r); } catch (e) { emptyState(el, "Gösterilemedi: " + e.message); }
  }
  function openNote(path) { window.location.href = obsidianUrl(path); }
  // Genel öğe: metin / {title,path,date,snippet}
  function itemNode(x, kind) {
    if (x == null) return "";
    if (typeof x === "string") {
      if (kind === "proje") return btn(x, function () { window.SB.openView("project", { name: x }); }, "sbv-linkbtn");
      if (kind === "kisi") return btn(x, function () { window.SB.openView("person", { name: x }); }, "sbv-linkbtn");
      return document.createTextNode(x);
    }
    const label = x.title || x.subject || x.text || x.name || x.snippet || "";
    const head = x.path ? noteLink(label || x.path, x.path) : document.createTextNode(label);
    return h("span", null, x.date ? h("span", { class: "sbv-date", text: x.date + " " }) : null, head,
      x.snippet && x.snippet !== label ? h("span", { class: "sbv-muted", text: " — " + x.snippet }) : null,
      x.from ? h("span", { class: "sbv-muted", text: " · " + x.from }) : null);
  }
  function head(title, extra) {
    return h("header", { class: "sbv-head" }, h("h2", { text: title }), extra || null);
  }

  // ---------- kayıt ----------
  function whenSB(fn) {
    if (window.SB && window.SB.registerView) return fn();
    let done = false;
    const go = function () { if (!done && window.SB && window.SB.registerView) { done = true; fn(); } };
    document.addEventListener("DOMContentLoaded", go);
    window.addEventListener("load", go);
    const t = setInterval(function () { go(); if (done) clearInterval(t); }, 200);
    setTimeout(function () { clearInterval(t); }, 15000);
  }
  function reg(name, title, icon, render) {
    window.SB.registerView(name, { title: title, icon: icon, render: render });
  }

  // ---------- dashboard ----------
  function dashboard(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    load(wrap, "/api/v2/dashboard", function (d) {
      wrap.replaceChildren(head(d.greeting || "Bugün"));
      const grid = h("div", { class: "sbv-grid" });
      grid.append(
        section("Bugün", list(d.today, function (x) { return [h("strong", { text: (x.time || "") + " " }), x.title]; })),
        section("Yaklaşan", list(d.due, function (x) { return [h("span", { class: "sbv-date", text: (x.date || "") + " " }), x.path ? noteLink(x.title, x.path) : x.title]; })),
        section("Görevler", list(d.tasks, function (x) { return [x.path ? noteLink(x.text, x.path) : x.text, x.due ? h("span", { class: "sbv-muted", text: " (" + x.due + ")" }) : null]; })),
        section("Son notlar", list(d.recent, function (x) { return [noteLink(x.title, x.path), h("span", { class: "sbv-muted", text: " " + (x.updated || "") })]; }))
      );
      const st = d.stats || {};
      const stats = h("div", { class: "sbv-stats" }, Object.keys(st).map(function (k) {
        return h("div", { class: "sbv-stat" }, h("b", { text: String(st[k]) }), h("span", { text: k }));
      }));
      grid.append(section("Durum", [h("p", { text: "Gelen kutusu: " + (d.inbox_count || 0) }), stats]));
      if (d.approvals && d.approvals.length) grid.append(section("Onay bekleyen", list(d.approvals, function (x) { return itemNode(x); })));
      if (d.suggestions && d.suggestions.length) {
        grid.append(section("Öneriler", h("div", { class: "sbv-chips" }, d.suggestions.map(function (s) {
          return btn(s, function () { if (window.SB.sendMessage) window.SB.sendMessage(s); }, "sbv-chip");
        }))));
      }
      if (d.reflection && d.reflection.text) grid.append(section("Yansıma" + (d.reflection.date ? " · " + d.reflection.date : ""), md(d.reflection.text)));
      wrap.append(grid);
    });
  }

  // ---------- graf ----------
  function graph(el, params) {
    params = params || {};
    const state = { center: params.center || "", depth: params.depth || 1, kinds: new Set(["kisi", "proje", "ders", "kavram"]), limit: 300 };
    const wrap = h("div", { class: "sbv sbv-graphwrap" });
    el.replaceChildren(wrap);
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const canvas = h("canvas", { class: "sbv-canvas", tabindex: "0", role: "img", "aria-label": "Bilgi grafı. Oklarla kaydır, + ve - ile yakınlaştır." });
    const preview = h("div", { class: "sbv-preview", "aria-live": "polite" });
    const status = h("span", { class: "sbv-muted", role: "status" });
    let nodes = [], edges = [], raf = 0, alpha = 1, view = { s: 1, tx: 0, ty: 0 }, hover = -1, drag = null, dead = false;

    function redraw() {
      const ctx = canvas.getContext("2d");
      const dpr = window.devicePixelRatio || 1;
      const w = canvas.clientWidth, hh = canvas.clientHeight;
      if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(hh * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(hh * dpr); }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, hh);
      const col = getComputedStyle(canvas).color || "#888";
      ctx.save();
      ctx.translate(view.tx + w / 2, view.ty + hh / 2);
      ctx.scale(view.s, view.s);
      ctx.strokeStyle = col; ctx.globalAlpha = 0.25; ctx.lineWidth = 1 / view.s;
      ctx.beginPath();
      for (const e of edges) { const a = nodes[e.a], b = nodes[e.b]; if (a && b) { ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); } }
      ctx.stroke();
      ctx.globalAlpha = 1;
      const showAll = view.s > 0.9;
      ctx.font = (12 / view.s) + "px sans-serif"; ctx.textAlign = "center";
      nodes.forEach(function (n, i) {
        ctx.fillStyle = kindColor(n.kind);
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, 6.2832); ctx.fill();
        if (i === hover) { ctx.strokeStyle = col; ctx.lineWidth = 2 / view.s; ctx.stroke(); }
        if (showAll || i === hover || n.r > 9) { ctx.fillStyle = col; ctx.fillText(n.label, n.x, n.y + n.r + 12 / view.s); }
      });
      ctx.restore();
    }
    function tick() {
      raf = 0;
      if (dead || !canvas.isConnected) return;
      const e = forceStep(nodes, edges, { k: 55, alpha: alpha });
      alpha = Math.max(0.02, alpha * 0.985);
      redraw();
      if (alpha > 0.05 || (drag && drag.i >= 0 && e >= 0)) raf = requestAnimationFrame(tick);
    }
    function kick() { alpha = Math.max(alpha, 0.5); if (!raf && !reduce) raf = requestAnimationFrame(tick); else if (reduce) { for (let i = 0; i < 150; i++) forceStep(nodes, edges, { k: 55, alpha: 0.5 }); redraw(); } }
    function toWorld(px, py) {
      const w = canvas.clientWidth, hh = canvas.clientHeight;
      return { x: (px - view.tx - w / 2) / view.s, y: (py - view.ty - hh / 2) / view.s };
    }
    function pick(px, py) {
      const p = toWorld(px, py);
      let best = -1, bd = 1e9;
      nodes.forEach(function (n, i) { const d = Math.hypot(n.x - p.x, n.y - p.y); if (d <= n.r + 3 / view.s && d < bd) { bd = d; best = i; } });
      return best;
    }
    function rel(ev) { const r = canvas.getBoundingClientRect(); return { x: ev.clientX - r.left, y: ev.clientY - r.top }; }
    function select(i) {
      const n = nodes[i];
      if (!n) return;
      if (n.kind === "kisi") return window.SB.openView("person", { name: n.label, path: n.id });
      if (n.kind === "proje") return window.SB.openView("project", { name: n.label, path: n.id });
      preview.replaceChildren(h("strong", { text: n.label }), h("span", { class: "sbv-muted", text: "  " + (n.kind || "not") + " · " + n.id + "  " }),
        link("Obsidian'da aç", obsidianUrl(n.id)), " ", btn("Merkez yap", function () { state.center = n.id; fetchGraph(); }));
    }
    function zoom(f, px, py) {
      const w = canvas.clientWidth, hh = canvas.clientHeight;
      px = px == null ? w / 2 : px; py = py == null ? hh / 2 : py;
      const ns = Math.max(0.15, Math.min(6, view.s * f)), r = ns / view.s;
      view.tx = (px - w / 2) - ((px - w / 2) - view.tx) * r; view.ty = (py - hh / 2) - ((py - hh / 2) - view.ty) * r; view.s = ns;
      redraw();
    }
    canvas.addEventListener("pointerdown", function (ev) {
      const p = rel(ev), i = pick(p.x, p.y);
      drag = { i: i, x: p.x, y: p.y, moved: 0, tx: view.tx, ty: view.ty };
      if (i >= 0) nodes[i].fixed = true;
      canvas.setPointerCapture(ev.pointerId);
    });
    canvas.addEventListener("pointermove", function (ev) {
      const p = rel(ev);
      if (!drag) { const i = pick(p.x, p.y); if (i !== hover) { hover = i; canvas.style.cursor = i >= 0 ? "pointer" : "grab"; redraw(); } return; }
      drag.moved += Math.abs(p.x - drag.x) + Math.abs(p.y - drag.y);
      if (drag.i >= 0) { const w = toWorld(p.x, p.y); nodes[drag.i].x = w.x; nodes[drag.i].y = w.y; kick(); }
      else { view.tx = drag.tx + (p.x - drag.x); view.ty = drag.ty + (p.y - drag.y); redraw(); }
      if (drag.i >= 0) { drag.x = p.x; drag.y = p.y; }
    });
    canvas.addEventListener("pointerup", function () {
      if (!drag) return;
      if (drag.i >= 0) { nodes[drag.i].fixed = false; if (drag.moved < 6) select(drag.i); }
      drag = null;
    });
    canvas.addEventListener("wheel", function (ev) { ev.preventDefault(); const p = rel(ev); zoom(ev.deltaY < 0 ? 1.15 : 1 / 1.15, p.x, p.y); }, { passive: false });
    canvas.addEventListener("keydown", function (ev) {
      const m = { ArrowLeft: [40, 0], ArrowRight: [-40, 0], ArrowUp: [0, 40], ArrowDown: [0, -40] }[ev.key];
      if (m) { view.tx += m[0]; view.ty += m[1]; redraw(); ev.preventDefault(); }
      else if (ev.key === "+" || ev.key === "=") zoom(1.2);
      else if (ev.key === "-") zoom(1 / 1.2);
    });

    function build(data) {
      const idx = {};
      const nn = data.nodes || [];
      nodes = nn.map(function (n, i) {
        idx[n.id] = i;
        const a = i * 2.4, rad = 12 * Math.sqrt(i + 1);
        return { id: n.id, label: n.label || n.id, kind: n.kind, x: Math.cos(a) * rad, y: Math.sin(a) * rad, vx: 0, vy: 0, r: 4 + Math.min(10, Math.sqrt(n.size || 1) * 1.5) };
      });
      edges = [];
      (data.edges || []).forEach(function (e) { if (idx[e.s] != null && idx[e.t] != null) edges.push({ a: idx[e.s], b: idx[e.t], w: e.w || 1 }); });
      view = { s: 1, tx: 0, ty: 0 };
      alpha = 1;
      status.textContent = nodes.length + " düğüm, " + edges.length + " bağ";
      canvas.setAttribute("aria-label", "Bilgi grafı: " + status.textContent + ". Oklarla kaydır, + ve - ile yakınlaştır.");
      if (reduce) { for (let i = 0; i < 250; i++) forceStep(nodes, edges, { k: 55, alpha: Math.max(0.05, 1 - i / 250) }); redraw(); }
      else { cancelAnimationFrame(raf); raf = requestAnimationFrame(tick); }
    }
    async function fetchGraph() {
      if (!hasRoute("GET", "/api/v2/graph")) return emptyState(el, "Graf ucu yok.");
      status.textContent = "Yükleniyor…";
      const r = await call("/api/v2/graph" + qs({ center: state.center, depth: state.depth, kinds: Array.from(state.kinds).join(","), limit: state.limit }));
      if (r.error || !r.nodes || !r.nodes.length) { nodes = []; edges = []; redraw(); status.textContent = r.error ? "Yüklenemedi: " + r.error : "Gösterilecek not yok."; return; }
      build(r);
    }
    const kindBoxes = ["kisi", "proje", "ders", "kavram"].map(function (k) {
      const cb = h("input", { type: "checkbox", checked: true, onchange: function () { cb.checked ? state.kinds.add(k) : state.kinds.delete(k); fetchGraph(); } });
      return h("label", { class: "sbv-kind" }, cb, h("span", { class: "sbv-dot", style: "background:" + kindColor(k) }), k);
    });
    const finder = h("input", { type: "search", placeholder: "Düğüm bul…", "aria-label": "Düğüm ara", onkeydown: function (ev) {
      if (ev.key !== "Enter") return;
      const q = finder.value.toLowerCase(), i = nodes.findIndex(function (n) { return n.label.toLowerCase().indexOf(q) >= 0; });
      if (i >= 0) { view.tx = -nodes[i].x * view.s; view.ty = -nodes[i].y * view.s; hover = i; redraw(); select(i); }
    } });
    const depthSel = h("select", { "aria-label": "Derinlik", onchange: function () { state.depth = depthSel.value; fetchGraph(); } },
      h("option", { value: "1", text: "Derinlik 1" }), h("option", { value: "2", text: "Derinlik 2" }));
    wrap.append(head("Bilgi grafı", status),
      h("div", { class: "sbv-toolbar" }, kindBoxes, depthSel, finder, btn("+", function () { zoom(1.2); }), btn("−", function () { zoom(1 / 1.2); }),
        btn("Yeniden yerleştir", function () { nodes.forEach(function (n) { n.x += Math.random() - 0.5; n.y += Math.random() - 0.5; }); alpha = 1; kick(); }),
        state.center ? btn("Merkezi kaldır", function () { state.center = ""; fetchGraph(); }) : null),
      canvas, preview);
    new Promise(function (r) { setTimeout(r, 0); }).then(fetchGraph);
    if (window.ResizeObserver) { const ro = new ResizeObserver(function () { if (canvas.isConnected) redraw(); else { dead = true; ro.disconnect(); } }); ro.observe(canvas); }
  }

  // ---------- timeline ----------
  function timeline(el, params) {
    params = params || {};
    const wrap = h("div", { class: "sbv" });
    const q = h("input", { type: "search", value: params.q || "", placeholder: "Konu ara…", "aria-label": "Konu" });
    const from = h("input", { type: "date", "aria-label": "Başlangıç" }), to = h("input", { type: "date", "aria-label": "Bitiş" });
    const out = h("div", { class: "sbv-tl" });
    async function run() {
      await load(out, "/api/v2/timeline" + qs({ q: q.value.trim(), from: from.value, to: to.value }), function (rows) {
        if (!Array.isArray(rows)) rows = rows.items || [];
        if (!rows.length) return emptyState(out, "Kayıt yok.");
        const ul = h("ol", { class: "sbv-timeline" });
        rows.forEach(function (r) {
          ul.append(h("li", null, h("time", { text: r.date || "" }), h("span", { class: "sbv-badge", text: r.kind || "" }),
            r.path ? noteLink(r.title, r.path) : h("span", { text: r.title || "" }), r.snippet ? h("p", { class: "sbv-muted", text: r.snippet }) : null));
        });
        out.replaceChildren(ul);
      });
    }
    q.addEventListener("keydown", function (ev) { if (ev.key === "Enter") run(); });
    wrap.append(head("Zaman çizelgesi"), h("div", { class: "sbv-toolbar" }, q, from, to, btn("Ara", run, "sbv-primary")), out);
    el.replaceChildren(wrap);
    run();
  }

  // ---------- kişi / proje ----------
  function entityView(kind, route, titleText) {
    return function (el, params) {
      params = params || {};
      const wrap = h("div", { class: "sbv" });
      const inp = h("input", { type: "search", value: params.name || "", placeholder: "Ad…", "aria-label": titleText + " adı" });
      const out = h("div");
      function go() {
        const name = inp.value.trim();
        if (!name) return emptyState(out, "Bir ad yazın.");
        load(out, route + qs({ name: name }), function (d) { out.replaceChildren(render(d)); });
      }
      function field(label, val) { return val ? h("p", null, h("strong", { text: label + ": " }), val) : null; }
      function render(d) {
        const g = h("div", { class: "sbv-grid" });
        const top = [d.role || d.status, d.company].filter(Boolean).join(" · ");
        const meta = h("div");
        add(meta, [h("h3", { text: d.name || inp.value }), top ? h("p", { text: top }) : null,
          d.path ? h("p", null, noteLink("Notu Obsidian'da aç", d.path)) : null]);
        if (kind === "person") {
          add(meta, [field("Takma adlar", (d.aliases || []).join(", ")), field("Telefon", (d.phones || []).join(", ")),
            field("E-posta", (d.emails || []).join(", ")),
            d.linkedin ? h("p", null, h("strong", { text: "LinkedIn: " }), link(d.linkedin, d.linkedin)) : null, field("Son iletişim", d.last_contact)]);
        } else if (d.summary) add(meta, md(d.summary));
        g.append(section(kind === "person" ? "Kişi" : "Proje", meta));
        const S = function (t, arr, k) { if (arr && arr.length) g.append(section(t, list(arr, function (x) { return itemNode(x, k); }))); };
        if (kind === "person") {
          S("Mailler", d.mail); S("Sohbetler", d.chats); S("Bahseden notlar", d.notes_mentioning); S("Projeler", d.projects, "proje");
          const f = d.facts || {};
          if ((f.declared && f.declared.length) || (f.inferred && f.inferred.length)) {
            g.append(section("Bilinenler", [h("h4", { text: "Beyan" }), list(f.declared, itemNode), h("h4", { text: "Çıkarım" }), list(f.inferred, itemNode)]));
          }
        } else {
          S("Kararlar", d.decisions); S("Açık işler", d.open); S("Kişiler", d.people, "kisi"); S("Dosyalar", d.files);
          S("Zaman çizelgesi", d.timeline); S("Oturumlar", d.sessions);
        }
        return g;
      }
      inp.addEventListener("keydown", function (ev) { if (ev.key === "Enter") go(); });
      wrap.append(head(titleText), h("div", { class: "sbv-toolbar" }, inp, btn("Göster", go, "sbv-primary")), out);
      el.replaceChildren(wrap);
      if (params.name) go(); else emptyState(out, "Bir ad yazıp Enter'a basın.");
    };
  }

  // ---------- kartlar ----------
  function cards(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const body = h("div");
    function showDecks() {
      load(body, "/api/v2/cards/decks", function (decks) {
        if (!Array.isArray(decks)) decks = decks.decks || [];
        const frag = h("div");
        frag.append(decks.length ? h("div", { class: "sbv-grid" }, decks.map(function (d) {
          return section(d.deck || "(deste)", [h("p", { text: d.total + " kart · " + d.due + " tekrar bekliyor" }),
            btn("Çalış", function () { session(d.deck); }, "sbv-primary")]);
        })) : h("p", { class: "sbv-muted", text: "Henüz deste yok." }));
        frag.append(forms());
        body.replaceChildren(frag);
      });
    }
    function forms() {
      const gp = h("input", { placeholder: "Not yolu ya da ders kodu", "aria-label": "Kaynak" });
      const gn = h("input", { type: "number", value: 5, min: 1, max: 30, "aria-label": "Kart sayısı" });
      const gen = section("Kart üret", h("div", { class: "sbv-toolbar" }, gp, gn, btn("Üret", async function () {
        const v = gp.value.trim(); if (!v) return;
        const body_ = { n: +gn.value || 5 }; body_[/[\\/]|\.md$/.test(v) ? "path" : "course"] = v;
        toast("Kartlar üretiliyor…");
        const r = await call("/api/v2/cards/generate", body_);
        if (r.error) toast(r.error, "error"); else { toast("Kartlar üretildi"); showDecks(); }
      }, "sbv-primary")));
      const dk = h("input", { placeholder: "Deste", "aria-label": "Deste" }), fr = h("input", { placeholder: "Ön yüz", "aria-label": "Ön yüz" }), bk = h("input", { placeholder: "Arka yüz", "aria-label": "Arka yüz" });
      const man = section("Elle ekle", h("div", { class: "sbv-toolbar" }, dk, fr, bk, btn("Ekle", async function () {
        if (!fr.value.trim() || !bk.value.trim()) return;
        const r = await call("/api/v2/cards/add", { deck: dk.value.trim() || "Genel", front: fr.value.trim(), back: bk.value.trim() });
        if (r.error) toast(r.error, "error"); else { toast("Eklendi"); fr.value = bk.value = ""; showDecks(); }
      })));
      return h("div", { class: "sbv-grid" }, gen, man);
    }
    async function session(deck) {
      body.replaceChildren(h("p", { class: "sbv-muted", text: "Yükleniyor…" }));
      const r = await call("/api/v2/cards/due" + qs({ deck: deck, limit: 20 }));
      const q = Array.isArray(r) ? r : (r.cards || []);
      if (r.error || !q.length) { body.replaceChildren(h("p", { text: r.error ? r.error : "Bugün tekrar yok." }), btn("Geri", showDecks)); return; }
      let i = 0, flipped = false, done = 0;
      const card = h("div", { class: "sbv-flash", tabindex: "0", role: "group", "aria-live": "polite" });
      const bar = h("div", { class: "sbv-toolbar" });
      function onKey(ev) {
        if (!card.isConnected) return document.removeEventListener("keydown", onKey);
        const t = ev.target && ev.target.tagName;
        if (t === "INPUT" || t === "TEXTAREA" || t === "SELECT") return;
        if (ev.key === " " || ev.key === "Enter") { if (!flipped) { flipped = true; draw(); ev.preventDefault(); } }
        else if (flipped && /^[0-5]$/.test(ev.key)) grade(+ev.key);
      }
      async function grade(g) {
        const c = q[i];
        const rr = await call("/api/v2/cards/review", { id: c.id, grade: g });
        if (rr.error) toast(rr.error, "error");
        done++; i++; flipped = false; draw();
      }
      function draw() {
        if (i >= q.length) { document.removeEventListener("keydown", onKey); body.replaceChildren(h("p", { text: done + " kart tamamlandı." }), btn("Desteler", showDecks, "sbv-primary")); return; }
        const c = q[i];
        card.replaceChildren(h("small", { class: "sbv-muted", text: (i + 1) + " / " + q.length }), h("div", { class: "sbv-front" }, md(c.front)),
          flipped ? h("div", { class: "sbv-back" }, md(c.back)) : null,
          flipped && c.source ? h("small", null, noteLink("Kaynak", c.source)) : null);
        bar.replaceChildren();
        if (!flipped) bar.append(btn("Çevir (Boşluk)", function () { flipped = true; draw(); }, "sbv-primary"));
        else [["Tekrar", 1], ["Zor", 3], ["İyi", 4], ["Kolay", 5]].forEach(function (p) {
          bar.append(btn(p[0] + " (" + p[1] + ")", function () { grade(gradeFor(p[0])); }, p[0] === "İyi" ? "sbv-primary" : ""));
        });
        bar.append(btn("Bitir", showDecks));
      }
      body.replaceChildren(card, bar);
      document.addEventListener("keydown", onKey);
      draw();
    }
    wrap.append(head("Bilgi kartları"), body);
    showDecks();
  }

  // ---------- ayarlar ----------
  function settings(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const S = window.SB.settings || { get: function () { return null; }, set: function () {} };
    function sget(k, d) { try { const v = S.get(k); return v == null ? d : v; } catch (e) { return d; } }
    function sset(k, v) { try { S.set(k, v); } catch (e) {} if (window.SB.bus) window.SB.bus.emit("settings", { key: k, value: v }); }
    function row(label, ctrl) { return h("label", { class: "sbv-row" }, h("span", { text: label }), ctrl); }
    function sel(opts, val, fn, label) {
      const s = h("select", { "aria-label": label, onchange: function () { fn(s.value); } }, opts.map(function (o) { return h("option", { value: o[0], text: o[1], selected: String(o[0]) === String(val) }); }));
      return s;
    }
    function chk(val, fn, label) { const c = h("input", { type: "checkbox", checked: !!val, "aria-label": label, onchange: function () { fn(c.checked); } }); return c; }

    // Görünüm
    const look = section("Görünüm", [
      row("Tema", sel([["system", "Sistem"], ["light", "Açık"], ["dark", "Koyu"]], sget("theme", "system"), function (v) { sset("theme", v); }, "Tema")),
      row("Vurgu rengi", sel([["blue", "Mavi"], ["green", "Yeşil"], ["orange", "Turuncu"], ["purple", "Mor"], ["red", "Kırmızı"]], sget("accent", "blue"), function (v) { sset("accent", v); }, "Vurgu")),
      row("Yazı boyutu", sel([["small", "Küçük"], ["medium", "Orta"], ["large", "Büyük"], ["xlarge", "Çok büyük"]], sget("fontsize", "medium"), function (v) { sset("fontsize", v); }, "Yazı boyutu"))]);

    // Ses
    const voiceSel = h("select", { "aria-label": "Ses" });
    function fillVoices() {
      const vs = (window.speechSynthesis && speechSynthesis.getVoices()) || [], cur = sget("ttsVoice", "");
      voiceSel.replaceChildren(h("option", { value: "", text: "Otomatik (dile göre)" }), vs.map(function (v) { return h("option", { value: v.name, text: v.name + " (" + v.lang + ")", selected: v.name === cur }); }));
    }
    fillVoices();
    if (window.speechSynthesis) speechSynthesis.addEventListener("voiceschanged", fillVoices);
    voiceSel.addEventListener("change", function () { sset("ttsVoice", voiceSel.value); });
    const hasStt = hasRoute("POST", "/api/v2/stt");
    const voice = section("Ses", [
      row("Cevapları sesli oku", chk(sget("tts", false), function (v) { sset("tts", v); if (!v && window.SB.voice) window.SB.voice.cancel(); }, "Sesli okuma")),
      row("Ses", voiceSel),
      btn("Dene", function () { if (window.SB.voice) window.SB.voice.speak("Merhaba, ben senin asistanınım.", "tr"); }),
      row("Uyandırma sözcüğü (yalnız sekme açıkken)", chk(sget("wake", false), function (v) {
        sset("wake", v); const w = window.SB.voice && window.SB.voice.wake; if (w) v ? w.enable() : w.disable();
      }, "Uyandırma")),
      hasStt ? null : h("p", { class: "sbv-muted", text: "Konuşma tanıma ucu bulunamadı." })]);

    // Persona
    const personaBox = h("div");
    const persona = section("Asistan kişiliği", personaBox);
    wrap.append(head("Ayarlar"), h("div", { class: "sbv-grid" }, persona, voice, look));
    if (!hasRoute("GET", "/api/v2/persona")) { personaBox.append(h("p", { class: "sbv-muted", text: "Persona ucu yok." })); return; }
    call("/api/v2/persona").then(function (p) {
      if (p.error) return personaBox.replaceChildren(h("p", { class: "sbv-muted", text: p.error }));
      const f = {
        name: h("input", { value: p.name || "", "aria-label": "Ad" }),
        tone: h("input", { value: p.tone || "", "aria-label": "Ton", placeholder: "samimi, resmi…" }),
        length: sel([["kisa", "Kısa"], ["orta", "Orta"], ["uzun", "Uzun"]], p.length || "orta", function () {}, "Uzunluk"),
        emoji: chk(p.emoji, function () {}, "Emoji"),
        formality: sel([["sen", "Sen"], ["siz", "Siz"]], p.formality || "sen", function () {}, "Hitap")
      };
      personaBox.replaceChildren(row("Ad", f.name), row("Ton", f.tone), row("Cevap uzunluğu", f.length), row("Emoji", f.emoji), row("Hitap", f.formality),
        btn("Kaydet", async function () {
          const body = Object.assign({}, p, { name: f.name.value.trim(), tone: f.tone.value.trim(), length: f.length.value, emoji: f.emoji.checked, formality: f.formality.value });
          if (voiceSel.value) body.voice = voiceSel.value;
          const r = await call("/api/v2/persona", body);
          r.error ? toast(r.error, "error") : toast("Kaydedildi");
        }, "sbv-primary"));
    });
  }

  // ---------- hatalar ----------
  function errors(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const out = h("div");
    wrap.append(head("Hata panosu"), out);
    load(out, "/api/v2/errors", function (rows) {
      if (!Array.isArray(rows)) rows = rows.items || [];
      if (!rows.length) return emptyState(out, "Kayıtlı hata yok.");
      out.replaceChildren(h("div", { class: "sbv-grid" }, rows.map(function (r) {
        return section(r.key || "hata", [h("p", { text: r.error || "" }), r.fix ? h("p", null, h("strong", { text: "Çözüm: " }), r.fix) : null,
          h("p", { class: "sbv-muted", text: [r.count ? r.count + " kez" : "", r.last || "", r.source || ""].filter(Boolean).join(" · ") })]);
      })));
    });
  }

  // ---------- öğrenme yolu ----------
  function learn(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const out = h("div"), topic = h("input", { placeholder: "Konu…", "aria-label": "Konu" });
    function showList() {
      load(out, "/api/v2/learn-paths", function (rows) {
        if (!Array.isArray(rows)) rows = rows.items || [];
        out.replaceChildren(list(rows, function (x) { return typeof x === "string" ? x : itemNode({ title: x.title || x.topic || x.name, path: x.path, date: x.date }); }));
      });
    }
    async function make() {
      const t = topic.value.trim(); if (!t) return;
      toast("Öğrenme yolu hazırlanıyor…");
      const r = await call("/api/v2/learn-path", { topic: t });
      if (r.error) return toast(r.error, "error");
      toast("Hazır" + (r.path ? ": " + r.path : ""));
      showList();
    }
    topic.addEventListener("keydown", function (ev) { if (ev.key === "Enter") make(); });
    wrap.append(head("Öğrenme yolları"), h("div", { class: "sbv-toolbar" }, topic, btn("Oluştur", make, "sbv-primary")), out);
    showList();
  }

  // ---------- ortak günlük ----------
  function journal(el) {
    const wrap = h("div", { class: "sbv" });
    el.replaceChildren(wrap);
    const out = h("div"), ta = h("textarea", { rows: "3", placeholder: "Bugüne bir not düş…", "aria-label": "Günlük notu" });
    function showList() {
      load(out, "/api/v2/journal?days=7", function (r) {
        const rows = Array.isArray(r) ? r : (r.entries || r.days || []);
        if (!rows.length) return emptyState(out, "Son günlerde kayıt yok.");
        out.replaceChildren(h("div", { class: "sbv-grid" }, rows.map(function (x) {
          const t = x.text || x.content || (Array.isArray(x.entries) ? x.entries.map(function (e) { return typeof e === "string" ? e : (e.who ? e.who + ": " : "") + (e.text || ""); }).join("\n") : "");
          return section(x.date || "", md(t));
        })));
      });
    }
    wrap.append(head("Ortak günlük"), ta, h("div", { class: "sbv-toolbar" }, btn("Ekle", async function () {
      const t = ta.value.trim(); if (!t) return;
      const r = await call("/api/v2/journal", { text: t, who: "ayse" });
      if (r.error) return toast(r.error, "error");
      ta.value = ""; showList();
    }, "sbv-primary")), out);
    showList();
  }

  whenSB(function () {
    reg("dashboard", "Pano", "layout-dashboard", dashboard);
    reg("graph", "Bilgi grafı", "share-2", graph);
    reg("timeline", "Zaman çizelgesi", "clock", timeline);
    reg("person", "Kişi", "user", entityView("person", "/api/v2/person", "Kişi"));
    reg("project", "Proje", "folder", entityView("project", "/api/v2/project", "Proje"));
    reg("cards", "Bilgi kartları", "layers", cards);
    reg("settings", "Ayarlar", "settings", settings);
    reg("errors", "Hata panosu", "alert-triangle", errors);
    reg("learn", "Öğrenme yolları", "graduation-cap", learn);
    reg("journal", "Ortak günlük", "book-open", journal);
  });
})();
