// Second Brain eklentisi: sağ tık "Beyne at". Yalnız yerel sunucuya konuşur.
const BASE = "http://127.0.0.1:8765";
const BLOCKED = /login|signin|checkout|bank/i;

// Sağ tık "Beyne at" araçsız yakalama ucuna gider (denetim D-03): web sayfasından seçilen metin
// sohbet modeline ve araçlarına (komut, kural, hafıza) ASLA verilmez.
function shareBody(info, tab) {
  const sel = (info.selectionText || "").trim();
  const url = info.linkUrl || info.pageUrl || (tab && tab.url) || "";
  if (sel) return {text: sel.slice(0, 3000), url};
  return {text: url}; // yalnız adres -> sunucu yakalar, model çağrılmaz
}

async function share(body) {
  const r = await fetch(BASE + "/api/v2/share", {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-SB": "1"},
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error("HTTP " + r.status);
  const j = await r.json();
  return ((j.results || []).join("\n")).slice(0, 2000) || "Kaydedildi";
}

// Açılır penceredeki soru kutusu: sohbet, ama sunucu bu oturumu güvenilmez sayar (komut/kalıcı yazma hep onaylı).
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
    const reply = await share(shareBody(info, tab));
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
