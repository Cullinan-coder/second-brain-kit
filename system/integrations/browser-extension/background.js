// Second Brain eklentisi: sağ tık "Beyne at". Yalnız yerel sunucuya konuşur.
const BASE = "http://127.0.0.1:8765";
const BLOCKED = /login|signin|checkout|bank/i;

function chatText(info, tab) {
  const sel = (info.selectionText || "").trim();
  const url = info.linkUrl || info.pageUrl || (tab && tab.url) || "";
  if (sel) return "Not al: " + sel.slice(0, 3000) + "\nKaynak: " + url;
  return url; // yalnız adres -> sunucu brain_capture çalıştırır
}

async function send(text) {
  const r = await fetch(BASE + "/api/v2/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-SB": "1"},
    body: JSON.stringify({sid: "eklenti", text})
  });
  if (!r.ok) throw new Error("HTTP " + r.status);
  const j = await r.json();
  return (j.reply && j.reply.text) || "";
}

async function setBadge(ok) {
  await chrome.action.setBadgeText({text: ok ? "OK" : "!"});
  setTimeout(() => chrome.action.setBadgeText({text: ""}), 3000);
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({id: "beyne-at", title: "Beyne at", contexts: ["page", "selection", "link"]});
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "beyne-at") return;
  const url = info.linkUrl || info.pageUrl || (tab && tab.url) || "";
  if (BLOCKED.test(url)) { await setBadge(false); return; }
  try {
    const reply = await send(chatText(info, tab));
    await chrome.storage.local.set({last: reply.slice(0, 2000)});
    await setBadge(true);
  } catch (e) {
    await chrome.storage.local.set({last: "Hata: " + e.message + " (sunucu çalışıyor mu?)"});
    await setBadge(false);
  }
});

chrome.runtime.onMessage.addListener((msg, _s, reply) => {
  if (msg && msg.type === "ask") {
    send(String(msg.text || "").slice(0, 4000)).then(
      t => reply({ok: true, text: t}),
      e => reply({ok: false, text: "Hata: " + e.message}));
    return true;
  }
});
