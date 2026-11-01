const out = document.getElementById("out");
const BLOCKED = /login|signin|checkout|bank/i;
function ask(text) {
  out.textContent = "...";
  chrome.runtime.sendMessage({type: "ask", text}, r => { out.textContent = (r && r.text) || "Cevap yok"; });
}
document.getElementById("go").onclick = () => {
  const t = document.getElementById("q").value.trim();
  if (t) ask(t);
};
const cap = document.getElementById("cap");
chrome.tabs.query({active: true, currentWindow: true}, tabs => {
  const url = (tabs[0] && tabs[0].url) || "";
  if (!/^https?:/.test(url) || BLOCKED.test(url)) { cap.disabled = true; cap.title = "Bu sayfada devre dışı"; }
  cap.onclick = () => ask(url);
});
chrome.storage.local.get("last", d => { if (d.last) out.textContent = d.last; });
