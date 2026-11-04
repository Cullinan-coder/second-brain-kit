/* Faz 2 Paket E — ses ön yüzü: bas-konuş, sesli okuma, konuşma kesme, uyandırma, görsel/ses komutları */
(function () {
  "use strict";

  // ---------- saf mantık ----------
  // Enerji tabanlı VAD: her karede rms verilir; konuşma başlangıcı/bitişi döner.
  function makeVad(o) {
    o = o || {};
    const st = {
      thresh: o.thresh || 0.04, onFrames: o.onFrames || 3, offFrames: o.offFrames || 14,
      noise: o.noise || 0.01, hi: 0, lo: 0, speaking: false
    };
    st.step = function (rms) {
      const limit = Math.max(st.thresh, st.noise * 3);
      if (rms > limit) { st.hi++; st.lo = 0; } else {
        st.lo++; st.hi = 0;
        if (!st.speaking) st.noise = st.noise * 0.95 + rms * 0.05; // gürültü tabanı
      }
      if (!st.speaking && st.hi >= st.onFrames) { st.speaking = true; return "start"; }
      if (st.speaking && st.lo >= st.offFrames) { st.speaking = false; return "end"; }
      return "";
    };
    return st;
  }
  function rmsOf(buf) {
    let s = 0;
    for (let i = 0; i < buf.length; i++) { const v = (buf[i] - 128) / 128; s += v * v; }
    return Math.sqrt(s / (buf.length || 1));
  }
  // Konuşmak için markdown/kod/bağlantı sadeleştirme
  function stripForSpeech(t) {
    return String(t || "")
      .replace(/```[\s\S]*?```/g, " (kod bloğu) ")
      .replace(/`([^`]*)`/g, "$1")
      .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
      .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
      .replace(/https?:\/\/\S+/g, " bağlantı ")
      .replace(/^\s{0,3}#{1,6}\s*/gm, "")
      .replace(/^\s*[-*+]\s+/gm, "")
      .replace(/[*_~>|]/g, "")
      .replace(/\s+/g, " ").trim();
  }
  function guessLang(t) {
    t = String(t || "").toLowerCase();
    if (/[çğıöşü]/.test(t)) return "tr";
    const tr = (t.match(/\b(ve|bir|bu|için|ile|ne|var|yok|değil|çok|daha|gibi|ama)\b/g) || []).length;
    const en = (t.match(/\b(the|and|is|are|to|of|that|with|for|this|you)\b/g) || []).length;
    return tr > en ? "tr" : (en > 0 ? "en" : "tr");
  }
  function pickMime(isSupported) {
    const c = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
    for (let i = 0; i < c.length; i++) if (isSupported(c[i])) return c[i];
    return "";
  }
  const pure = { makeVad, rmsOf, stripForSpeech, guessLang, pickMime };
  if (typeof module !== "undefined") module.exports = pure;
  if (typeof window === "undefined") return;

  // ---------- DOM ----------
  function h(tag, props) {
    const e = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (k) {
      const v = props[k];
      if (v == null || v === false) return;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k.slice(0, 2) === "on" && typeof v === "function") e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? "" : v);
    });
    for (let i = 2; i < arguments.length; i++) { const c = arguments[i]; if (c != null) e.appendChild(c.nodeType ? c : document.createTextNode(String(c))); }
    return e;
  }
  function toast(m, k) { if (window.SB && window.SB.toast) window.SB.toast(m, k); }
  function SBget(k, d) { try { const v = window.SB.settings.get(k); return v == null ? d : v; } catch (e) { return d; } }
  function emit(n, p) { try { window.SB.bus.emit(n, p); } catch (e) {} }

  const secure = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder && window.isSecureContext !== false);
  const canTTS = !!window.speechSynthesis;

  // Ham ses yükleme (SB.api JSON gönderdiği için kendi fetch'imiz)
  async function upload(path, params, blob) {
    const p = new URLSearchParams();
    p.set("sid", (window.SB && window.SB.sid) || "");
    Object.keys(params || {}).forEach(function (k) { if (params[k] !== "" && params[k] != null) p.set(k, params[k]); });
    try {
      const r = await fetch(path + "?" + p.toString(), {
        method: "POST", headers: { "X-SB": "1", "Content-Type": (blob.type || "application/octet-stream").split(";")[0] }, body: blob, credentials: "same-origin"
      });
      const j = await r.json().catch(function () { return {}; });
      if (!r.ok && !j.error) j.error = "HTTP " + r.status;
      return j;
    } catch (e) { return { error: String(e.message || e) }; }
  }

  // ---------- kayıt ----------
  let rec = null; // {stream, mr, chunks, mime, ctx, vadTimer}
  const state = { listening: false, speaking: false, busy: false };

  function micStream() {
    return navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
  }
  function recordFrom(stream) {
    const mime = pickMime(function (m) { return MediaRecorder.isTypeSupported(m); });
    const mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
    const chunks = [];
    mr.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
    const done = new Promise(function (res) { mr.onstop = function () { res(new Blob(chunks, { type: mr.mimeType || mime || "audio/webm" })); }; });
    mr.start();
    return { mr: mr, done: done };
  }

  async function transcribeAndSend(blob) {
    if (!blob || blob.size < 800) { toast("Ses çok kısa."); return; }
    state.busy = true; emit("voice:processing", {});
    const lang = SBget("sttLang", "");
    const r = await upload("/api/v2/stt", { lang: lang }, blob);
    state.busy = false;
    if (r.available === false) { toast(r.hint || "Konuşma tanıma kurulu değil.", "error"); return; }
    if (r.error) { toast("Ses tanınamadı: " + r.error, "error"); return; }
    const text = (r.text || "").trim();
    if (!text) { toast("Ses anlaşılamadı."); return; }
    emit("voice:transcript", { text: text, language: r.language });
    if (window.SB.sendMessage) window.SB.sendMessage(text, { voice: true });
  }

  async function start() {
    if (state.listening) return;
    cancel();
    if (!secure) { filePick("audio/*", true).then(function (f) { if (f) voiceNote(f); }); return; }
    pauseWake();
    try {
      const stream = await micStream();
      const r = recordFrom(stream);
      rec = { stream: stream, mr: r.mr, done: r.done };
      state.listening = true; emit("voice:start", {});
      document.body.classList.add("sbv-listening");
    } catch (e) {
      toast("Mikrofon açılamadı: " + (e.message || e), "error"); resumeWake();
    }
  }
  async function stop() {
    if (!rec) return;
    const cur = rec; rec = null; state.listening = false;
    document.body.classList.remove("sbv-listening");
    emit("voice:stop", {});
    try { cur.mr.state !== "inactive" && cur.mr.stop(); } catch (e) {}
    const blob = await cur.done;
    cur.stream.getTracks().forEach(function (t) { t.stop(); });
    resumeWake();
    await transcribeAndSend(blob);
  }

  // Sessizlikte kendiliğinden biten tek seferlik dinleme (uyandırma sonrası)
  async function listenAuto(maxMs) {
    if (!secure || state.listening) return;
    await start();
    if (!rec) return;
    const cur = rec, ac = new (window.AudioContext || window.webkitAudioContext)();
    const an = ac.createAnalyser(); an.fftSize = 1024;
    ac.createMediaStreamSource(cur.stream).connect(an);
    const buf = new Uint8Array(an.fftSize), vad = makeVad({ offFrames: 18 });
    let heard = false;
    const t0 = Date.now();
    const iv = setInterval(function () {
      an.getByteTimeDomainData(buf);
      const ev = vad.step(rmsOf(buf));
      if (ev === "start") heard = true;
      if ((ev === "end" && heard) || Date.now() - t0 > (maxMs || 15000) || (!heard && Date.now() - t0 > 6000) || rec !== cur) {
        clearInterval(iv); ac.close().catch(function () {}); if (rec === cur) stop();
      }
    }, 50);
  }

  // ---------- sesli okuma ----------
  let audioEl = null, bargeStop = null;
  function chooseVoice(lang) {
    const vs = canTTS ? speechSynthesis.getVoices() : [];
    const want = SBget("ttsVoice", "");
    let v = vs.find(function (x) { return x.name === want && x.lang.slice(0, 2) === lang; });
    if (!v) v = vs.find(function (x) { return x.lang.toLowerCase().indexOf(lang) === 0; });
    return v || null;
  }
  async function speak(text, lang) {
    text = stripForSpeech(text);
    if (!text) return;
    lang = lang || guessLang(text);
    cancel();
    state.speaking = true; emit("voice:speak", { text: text });
    const voice = canTTS ? chooseVoice(lang) : null;
    const finish = function () { state.speaking = false; if (bargeStop) { bargeStop(); bargeStop = null; } emit("voice:speak-end", {}); };
    if (voice) {
      const parts = text.match(/[^.!?\n]+[.!?]?/g) || [text];
      let n = 0;
      parts.forEach(function (p) {
        if (!p.trim()) return;
        const u = new SpeechSynthesisUtterance(p.trim());
        u.voice = voice; u.lang = voice.lang; n++;
        u.onend = u.onerror = function () { if (--n <= 0) finish(); };
        speechSynthesis.speak(u);
      });
      if (!n) return finish();
      armBargeIn();
      return;
    }
    // Yedek: sunucu wav
    try {
      const r = await fetch("/api/v2/tts", { method: "POST", headers: { "X-SB": "1", "Content-Type": "application/json" }, body: JSON.stringify({ text: text.slice(0, 1500), voice: SBget("ttsVoice", "") || undefined }), credentials: "same-origin" });
      if (!r.ok || !(r.headers.get("content-type") || "").includes("audio")) { finish(); return; }
      const url = URL.createObjectURL(await r.blob());
      audioEl = new Audio(url);
      audioEl.onended = audioEl.onerror = function () { URL.revokeObjectURL(url); finish(); };
      await audioEl.play();
      armBargeIn();
    } catch (e) { finish(); }
  }
  function cancel() {
    if (canTTS) speechSynthesis.cancel();
    if (audioEl) { try { audioEl.pause(); } catch (e) {} audioEl = null; }
    if (state.speaking) { state.speaking = false; if (bargeStop) { bargeStop(); bargeStop = null; } emit("voice:speak-end", {}); }
  }

  // Konuşma kesme (50): okurken kullanıcı sesi algılanırsa kes ve dinle
  async function armBargeIn() {
    if (!secure || !SBget("bargeIn", true) || bargeStop) return;
    let stream, ac, iv;
    try { stream = await micStream(); } catch (e) { return; }
    if (!state.speaking) { stream.getTracks().forEach(function (t) { t.stop(); }); return; }
    ac = new (window.AudioContext || window.webkitAudioContext)();
    const an = ac.createAnalyser(); an.fftSize = 1024;
    ac.createMediaStreamSource(stream).connect(an);
    const buf = new Uint8Array(an.fftSize), vad = makeVad({ thresh: 0.08, onFrames: 6, noise: 0.03 });
    const t0 = Date.now();
    bargeStop = function () { clearInterval(iv); stream.getTracks().forEach(function (t) { t.stop(); }); ac.close().catch(function () {}); };
    iv = setInterval(function () {
      an.getByteTimeDomainData(buf);
      if (Date.now() - t0 > 600 && vad.step(rmsOf(buf)) === "start") {
        const b = bargeStop; bargeStop = null; b();
        cancel(); emit("voice:barge-in", {});
        start();
      }
    }, 50);
  }

  // ---------- uyandırma (40) ----------
  const wakeSt = { on: false, paused: false, stream: null, ac: null, iv: 0, mr: null };
  let phrase = "";
  async function getPhrase() {
    if (phrase) return phrase;
    try { const p = await window.SB.api("/api/v2/persona"); phrase = "hey " + ((p && p.name) || "asistan"); } catch (e) { phrase = "hey asistan"; }
    return phrase;
  }
  async function wakeEnable() {
    if (wakeSt.on || !secure) { if (!secure) toast("Uyandırma için güvenli bağlam (https/localhost) gerekir.", "error"); return; }
    try { wakeSt.stream = await micStream(); } catch (e) { toast("Mikrofon açılamadı.", "error"); return; }
    wakeSt.on = true;
    const ac = wakeSt.ac = new (window.AudioContext || window.webkitAudioContext)();
    const an = ac.createAnalyser(); an.fftSize = 1024;
    ac.createMediaStreamSource(wakeSt.stream).connect(an);
    const buf = new Uint8Array(an.fftSize), vad = makeVad({ offFrames: 12 });
    let seg = null, t0 = 0;
    wakeSt.iv = setInterval(async function () {
      if (wakeSt.paused || state.speaking || state.listening || state.busy) { if (seg) { try { seg.mr.stop(); } catch (e) {} seg = null; } return; }
      an.getByteTimeDomainData(buf);
      const ev = vad.step(rmsOf(buf));
      if (ev === "start" && !seg) { seg = recordFrom(wakeSt.stream); t0 = Date.now(); }
      else if (seg && (ev === "end" || Date.now() - t0 > 4000)) {
        const cur = seg; seg = null; cur.mr.stop();
        const blob = await cur.done;
        if (blob.size < 1500 || !wakeSt.on) return;
        const r = await upload("/api/v2/wake", { phrase: await getPhrase() }, blob);
        if (r && r.wake) { toast("Dinliyorum…"); emit("voice:wake", r); listenAuto(15000); }
      }
    }, 50);
    emit("voice:wake-on", {});
  }
  function wakeDisable() {
    wakeSt.on = false; clearInterval(wakeSt.iv);
    if (wakeSt.stream) wakeSt.stream.getTracks().forEach(function (t) { t.stop(); });
    if (wakeSt.ac) wakeSt.ac.close().catch(function () {});
    wakeSt.stream = wakeSt.ac = null;
    emit("voice:wake-off", {});
  }
  function pauseWake() { wakeSt.paused = true; }
  function resumeWake() { wakeSt.paused = false; }

  // ---------- dosya yedekleri ----------
  function filePick(accept, capture) {
    return new Promise(function (resolve) {
      const i = h("input", { type: "file", accept: accept, style: "display:none" });
      if (capture) i.setAttribute("capture", "");
      i.addEventListener("change", function () { resolve(i.files && i.files[0] || null); i.remove(); });
      i.addEventListener("cancel", function () { resolve(null); i.remove(); });
      document.body.appendChild(i); i.click();
    });
  }
  async function voiceNote(file) {
    toast("Sesli not kaydediliyor…");
    const r = await upload("/api/v2/voice-note", { title: "" }, file);
    if (r.error) return toast(r.error, "error");
    if (r.available === false) return toast(r.hint || "Konuşma tanıma kurulu değil.", "error");
    toast("Sesli not kaydedildi" + (r.path ? ": " + r.path : ""));
    showResult("Sesli not", r.text || r.path || "");
  }

  // Sonuç penceresi (metin güvenli: textContent / SB.md)
  function showResult(title, text, extra) {
    const old = document.getElementById("sbv-result"); if (old) old.remove();
    const body = h("div", { class: "sbv-modal-body" });
    if (window.SB.md) body.appendChild(window.SB.md(String(text || ""))); else body.textContent = String(text || "");
    if (extra) body.appendChild(extra);
    const close = function () { box.remove(); };
    const box = h("div", { id: "sbv-result", class: "sbv-modal", role: "dialog", "aria-modal": "true", "aria-label": title, onkeydown: function (e) { if (e.key === "Escape") close(); } },
      h("div", { class: "sbv-modal-card" }, h("h3", { text: title }), body,
        h("div", { class: "sbv-actions" },
          h("button", { type: "button", class: "btn", text: "Sohbete gönder", onclick: function () { if (window.SB.sendMessage) window.SB.sendMessage(title + ":\n" + String(text || "")); close(); } }),
          h("button", { type: "button", class: "btn primary", text: "Kapat", onclick: close }))));
    document.body.appendChild(box);
    box.querySelector(".primary").focus();
  }

  // Kayıt penceresi: Başlat/Durdur -> Blob
  function recordDialog(title) {
    return new Promise(function (resolve) {
      if (!secure) { filePick("audio/*", true).then(resolve); return; }
      let r = null, stream = null;
      const status = h("p", { text: "Hazır." });
      const go = h("button", { type: "button", class: "btn primary", text: "Kaydı başlat" });
      const cancelB = h("button", { type: "button", class: "btn", text: "Vazgeç" });
      const box = h("div", { class: "sbv-modal", role: "dialog", "aria-modal": "true", "aria-label": title },
        h("div", { class: "sbv-modal-card" }, h("h3", { text: title }), status, h("div", { class: "sbv-actions" }, go, cancelB)));
      function end(v) { if (stream) stream.getTracks().forEach(function (t) { t.stop(); }); box.remove(); resolve(v); }
      go.addEventListener("click", async function () {
        if (!r) {
          try { stream = await micStream(); } catch (e) { toast("Mikrofon açılamadı.", "error"); return end(null); }
          r = recordFrom(stream); go.textContent = "Durdur"; status.textContent = "Kaydediliyor…";
        } else { r.mr.stop(); end(await r.done); }
      });
      cancelB.addEventListener("click", function () { if (r) { try { r.mr.stop(); } catch (e) {} } end(null); });
      document.body.appendChild(box); go.focus();
    });
  }

  function registerCommands() {
    const SB = window.SB;
    if (!SB.registerCommand) return;
    SB.registerCommand({ cmd: "/foto", desc: "Fotoğraf seç ve hakkında soru sor", run: async function (args) {
      const f = await filePick("image/*", false); if (!f) return;
      toast("Görsel inceleniyor…");
      const r = await upload("/api/v2/vision/ask", { q: String(args || "Bu görselde ne var?") }, f);
      if (r.error) return toast(r.error, "error");
      if (r.available === false) return toast(r.hint || "Görsel modeli yok.", "error");
      showResult("Görsel cevabı", r.answer || r.text || "");
    } });
    SB.registerCommand({ cmd: "/tara", desc: "El yazısı / tahta fotoğrafını metne çevir ve kaydet", run: async function (args) {
      const f = await filePick("image/*", false); if (!f) return;
      toast("Taranıyor…");
      const r = await upload("/api/v2/vision/ocr", { save: 1, title: String(args || "") }, f);
      if (r.error) return toast(r.error, "error");
      if (r.available === false) return toast(r.hint || "Görsel modeli yok.", "error");
      showResult("Taranan metin", r.text || "");
    } });
    SB.registerCommand({ cmd: "/toplanti", desc: "Toplantı/ders ses kaydını özetle", run: async function (args) {
      const f = await filePick("audio/*", false); if (!f) return;
      toast("Toplantı işleniyor, bu biraz sürebilir…");
      const r = await upload("/api/v2/meeting", { title: String(args || "") }, f);
      if (r.error) return toast(r.error, "error");
      if (r.available === false) return toast(r.hint || "Konuşma tanıma kurulu değil.", "error");
      const lines = [r.summary || ""];
      if (r.decisions && r.decisions.length) lines.push("\n**Kararlar**\n" + r.decisions.map(function (d) { return "- " + d; }).join("\n"));
      if (r.tasks && r.tasks.length) lines.push("\n**Görevler**\n" + r.tasks.map(function (d) { return "- " + (d.text || d); }).join("\n"));
      if (r.path) lines.push("\nNot: " + r.path);
      showResult("Toplantı özeti", lines.join("\n"));
    } });
    SB.registerCommand({ cmd: "/dokum", desc: "Video/podcast bağlantısını dök: /dokum <url>", run: async function (args) {
      const url = String(args || "").trim();
      if (!/^https?:\/\//i.test(url)) return toast("Kullanım: /dokum https://…", "error");
      toast("Döküm alınıyor…");
      const r = await SB.api("/api/v2/transcribe-url", { url: url });
      if (r.error) return toast(r.error, "error");
      if (r.available === false) return toast(r.hint || "yt-dlp kurulu değil.", "error");
      showResult("Döküm", (r.path ? "Not: " + r.path + "\n\n" : "") + (r.text || r.summary || "Kaydedildi."));
    } });
    SB.registerCommand({ cmd: "/telaffuz", desc: "Telaffuz koçu: /telaffuz <hedef cümle>", run: async function (args) {
      const target = String(args || "").trim();
      if (!target) return toast("Kullanım: /telaffuz <hedef cümle>", "error");
      const blob = await recordDialog("Şunu söyle: " + target); if (!blob) return;
      const r = await upload("/api/v2/pronounce", { target: target, lang: guessLang(target) === "tr" ? "tr" : "en" }, blob);
      if (r.error) return toast(r.error, "error");
      if (r.available === false) return toast(r.hint || "Konuşma tanıma kurulu değil.", "error");
      const words = h("p", null);
      (r.words || []).forEach(function (w) {
        words.appendChild(h("span", { class: w.ok ? "sbv-w-ok" : "sbv-w-bad", title: w.ok ? "" : "Duyulan: " + (w.heard || "—"), text: w.word + " " }));
      });
      showResult("Telaffuz puanı: " + (r.score != null ? r.score : "?") + "/100", (r.tips || []).map(function (t) { return "- " + t; }).join("\n"), words);
    } });
  }

  // ---------- genel API ----------
  const voice = {
    start: start, stop: stop, speak: speak, cancel: cancel,
    wake: { enable: wakeEnable, disable: wakeDisable },
    get available() { return secure; },
    get listening() { return state.listening; },
    get speaking() { return state.speaking; }
  };

  // Mikrofon düğmeleri (D'nin düğmesi: [data-voice-mic], #mic-btn, .mic-btn) için bas-konuş
  function micTarget(t) { return t && t.closest && t.closest("[data-voice-mic], #mic-btn, .mic-btn"); }
  function bindUI() {
    document.addEventListener("pointerdown", function (e) { if (micTarget(e.target) && e.button === 0) { e.preventDefault(); holdPointer = true; start(); } });
    // Düğmeden dışarı bırakılsa da bitir
    document.addEventListener("pointerup", function () { if (holdPointer) { holdPointer = false; if (state.listening) stop(); } });
    document.addEventListener("pointercancel", function () { holdPointer = false; if (state.listening) stop(); });
    document.addEventListener("keydown", function (e) {
      if (e.ctrlKey && e.code === "Space" && !e.repeat) { e.preventDefault(); holdKey = true; start(); }
      else if (e.code === "Escape" && state.speaking) cancel();
    });
    document.addEventListener("keyup", function (e) {
      if (holdKey && (e.code === "Space" || e.key === "Control")) { holdKey = false; if (state.listening) stop(); }
    });
    // Klavyeyle mikrofon düğmesi: Enter/Boşluk ile aç-kapa
    document.addEventListener("keydown", function (e) {
      if ((e.key === "Enter" || e.key === " ") && !e.ctrlKey && micTarget(e.target)) { e.preventDefault(); if (!e.repeat) (state.listening ? stop() : start()); }
    });
  }
  let holdKey = false, holdPointer = false;

  function init() {
    const SB = window.SB;
    SB.voice = voice;
    registerCommands();
    bindUI();
    if (SB.bus && SB.bus.on) {
      SB.bus.on("message", function (m) {
        m = m || {};
        const msg = m.message || m;
        if (msg.role !== "assistant" || !msg.text) return;
        if ([true, "1", "true"].indexOf(SBget("tts", false)) < 0) return;
        speak(msg.text);
      });
      SB.bus.on("settings", function (s) {
        if (s && s.key === "wake") (s.value ? wakeEnable() : wakeDisable());
      });
    }
    if (canTTS) speechSynthesis.getVoices();
    if ([true, "1", "true"].indexOf(SBget("wake", false)) >= 0 && secure) wakeEnable();
    document.body.classList.toggle("sbv-no-mic", !secure);
    emit("voice:ready", { available: secure });
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
