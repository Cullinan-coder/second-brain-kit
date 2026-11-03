"""Güvenlik incelemesi (orta/düşük bulgular) regresyon testleri."""
import json
import sys
import zipfile
from pathlib import Path

import pytest

from sb import agents, capture, config, content, llm, router, vault_ops
from sb import privacy as pv


# ---- 1 router / llm
@pytest.mark.parametrize("text", [
    "anahtar sk-ant-api03-abcdefghijklmnopqrstuvwx",
    "SMTP_PASSWORD=hunter2hunter2",
    "doğrulama kodu 482913 geldi",
    "kart 4111 1111 1111 1111 bitti",
])
def test_sensitive_uses_redact(text):
    assert router.sensitive(text)
    assert router.chain({"tasks": {"x": "claude"}}, "x", text) == ["ollama"]


def test_sensitive_clean_text():
    assert not router.sensitive("bugün hava güzel, toplantı 14:00")


def test_cloud_safe_messages():
    clean = [{"role": "user", "content": "merhaba"}]
    assert router.cloud_safe_messages(clean) == (clean, False)
    dirty = clean + [{"role": "user", "content": "OPENAI_API_KEY=abcd1234efgh5678"}]
    assert router.cloud_safe_messages(dirty)[1] is True
    parts = [{"role": "user", "content": [{"type": "text", "text": "kod: sk-proj-abcdefghijklmnopqrstu"}]}]
    assert router.cloud_safe_messages(parts)[1] is True


def test_long_complete_sensitivity_whole_text(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "config", lambda: {"ollama": {"max_chars": 6000}})
    monkeypatch.setattr(llm, "complete", lambda task, prompt, **kw: (seen.append(kw.get("private")) or "ok", "yerel x"))
    text = ("temiz paragraf. " * 400 + "\n\n") * 3 + "SMTP_PASSWORD=hunter2hunter2\n\n" + "temiz. " * 100
    llm.long_complete("t", "özetle", text, chunk_chars=4000)
    assert len(seen) > 2 and all(seen)


# ---- 2 SSRF
@pytest.mark.parametrize("url", ["http://127.0.0.1/x", "http://169.254.169.254/latest", "http://100.64.1.2/", "http://10.0.0.5/",
                                 "http://[::1]/", "file:///etc/passwd", "ftp://example.com/", "http://localhost:8080/"])
def test_check_public_url_blocks(url):
    with pytest.raises(capture.UnsafeUrl):
        capture.check_public_url(url)


def test_check_public_url_allows_public_and_blocks_dns_to_private(monkeypatch):
    import socket
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 80))])
    assert capture.check_public_url("http://example.com/") == "http://example.com/"
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 80)), (2, 1, 6, "", ("192.168.1.1", 80))])
    with pytest.raises(capture.UnsafeUrl):
        capture.check_public_url("http://rebind.example/")


def test_redirect_to_private_blocked(monkeypatch):
    import socket
    import urllib.request
    real = socket.getaddrinfo
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, *a, **k: [(2, 1, 6, "", ("93.184.216.34", 80))] if host == "example.com" else real(host, *a, **k))
    h = capture._SafeRedirect()
    req = urllib.request.Request("http://example.com/")
    with pytest.raises(capture.UnsafeUrl):
        h.redirect_request(req, None, 302, "Found", {}, "http://127.0.0.1:8765/api")


def test_get_rejects_private():
    with pytest.raises(capture.UnsafeUrl):
        capture._get("http://127.0.0.1:1/")


def test_transcribe_url_private_and_local_only():
    from sb import voice
    from sb.webroutes import ROUTES, ApiError, load
    with pytest.raises(ApiError):
        voice.transcribe_url("http://169.254.169.254/latest/meta-data")
    load()
    assert ROUTES[("POST", "/api/v2/transcribe-url")].local_only is True


# ---- 3 vault key / restore
class _KR:
    def __init__(self, store=None):
        self.store = store or {}

    def get_password(self, svc, name):
        return self.store.get(name)

    def set_password(self, svc, name, v):
        self.store[name] = v


@pytest.fixture
def pvenv(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "40-Kaynaklar").mkdir(parents=True)
    (vault / "40-Kaynaklar" / "a.md").write_text("merhaba", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    for mod in (pv, vault_ops):
        monkeypatch.setattr(mod, "VAULT", vault)
    monkeypatch.setattr(pv, "BACKUPS", data / "backups")
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(config, "DATA", data)
    return vault


def _fake_keyring(monkeypatch, kr):
    import types
    monkeypatch.setitem(sys.modules, "keyring", types.SimpleNamespace(get_password=kr.get_password, set_password=kr.set_password))


def test_key_not_regenerated_when_marker_exists(pvenv, monkeypatch):
    kr = _KR()
    _fake_keyring(monkeypatch, kr)
    enc, dec = pv._real_cipher()                       # ilk üretim: anahtar + işaret dosyası
    assert kr.store["vault-key"] and (config.DATA / "vault_key_created").exists()
    assert dec(enc(b"x")) == b"x"
    kr.store.clear()                                   # keyring okunamıyor/silindi
    with pytest.raises(pv.KeyLost):
        pv._real_cipher()
    assert not kr.store                                # yeni anahtar üretilmedi


def test_key_not_regenerated_when_encrypted_files_exist(pvenv, monkeypatch):
    _fake_keyring(monkeypatch, _KR())
    (pvenv / "40-Kaynaklar" / "b.md.enc").write_bytes(b"x")
    with pytest.raises(pv.KeyLost):
        pv._real_cipher()
    monkeypatch.setattr(pv, "_cipher", pv._real_cipher)
    assert pv.encrypt_folder("40-Kaynaklar", confirm=True)["ok"] is False


def test_export_key_and_cli(pvenv, monkeypatch, tmp_path):
    _fake_keyring(monkeypatch, _KR({"vault-key": "ABC="}))
    out = pv.export_key(tmp_path / "k" / "key.txt")
    assert out.read_text().strip() == "ABC="
    assert pv.vault_key_cli(["--export", str(tmp_path / "k2.txt")]) == 0
    assert pv.vault_key_cli([]) == 1


def test_encrypt_writes_encrypted_backup_copy(pvenv, monkeypatch):
    monkeypatch.setattr(pv, "_cipher", lambda: ((lambda b: b"ENC" + b[::-1]), (lambda t: t[3:][::-1])))
    r = pv.encrypt_folder("40-Kaynaklar", confirm=True)
    assert (pv.BACKUPS / r["backup_encrypted"]).exists() and "Geri Dönüşüm" in r["advice"]


@pytest.mark.parametrize("bad", ["C:foo.md", "C:/x.md", "/abs.md", "\\\\srv\\share\\x.md", "../x.md", "a/../../x.md", "a:stream"])
def test_restore_rejects_unsafe_members(pvenv, bad):
    pv.BACKUPS.mkdir(parents=True, exist_ok=True)
    z = pv.BACKUPS / "vault-x.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr(bad, "kötü")
        zf.writestr("iyi.md", "ok")
    r = pv.restore(z.name, confirm=True)
    assert r["restored"] == 1 and (pvenv / "iyi.md").exists()


def test_restore_rejects_non_vault_zip(pvenv):
    pv.BACKUPS.mkdir(parents=True, exist_ok=True)
    z = pv.BACKUPS / "system-1.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("sb/evil_regression_marker.py", "x")
    r = pv.restore(z.name, confirm=True)
    assert r["ok"] is False and not (pv.SYSTEM / "sb" / "evil_regression_marker.py").exists()


# ---- 4 uninstall secrets
def test_uninstall_plan_lists_secrets_not_vault_key(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from setup import engine as E

    class KR(_KR):
        def delete_password(self, svc, name):
            self.store.pop(name)
    kr = KR({"api-openai": "k", "telegram-bot": "t", "vault-key": "VK"})
    monkeypatch.setattr(E, "_keyring", lambda: kr)
    monkeypatch.setattr(E, "_trash", lambda: None)
    ran = []
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (ran.append(cmd), (0, ""))[1])   # gerçek schtasks YOK
    monkeypatch.setattr(E, "_run_stream", lambda cmd, log, cwd=None: (ran.append(cmd), 0)[1])
    eng = E.Engine()
    plan = eng.uninstall_plan()
    sec = next(a for a in plan if a["id"] == "secrets")
    assert "api-openai" in sec["names"] and "vault-key" not in sec["names"]
    assert any(a["id"] == "vault_key" and "vault-key" in a["desc"] for a in plan)
    eng.uninstall(False)
    assert "api-openai" in kr.store                              # onaysız silinmez
    eng.uninstall(True)
    assert "api-openai" not in kr.store and "telegram-bot" not in kr.store and kr.store["vault-key"] == "VK"


# ---- 5 agents sandbox
@pytest.fixture
def avault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    (v / "10-Dersler").mkdir(parents=True)
    (v / "10-Dersler" / "ok.md").write_text("---\ntype: ders\n---\nmerhaba", encoding="utf-8")
    (v / "10-Dersler" / "late.md").write_text("---\ntype: ders\nvisibility: private\nx: 1\n---\ngizli", encoding="utf-8")
    (v / "10-Dersler" / "late2.md").write_text("---\n" + "a: b\n" * 200 + "visibility: private\n---\ngizli", encoding="utf-8")
    (v / "30-Kariyer").mkdir()
    (v / "30-Kariyer" / "x.md").write_text("özel", encoding="utf-8")
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    return v


def test_sandbox_private_whole_frontmatter(avault):
    sb = agents.Sandbox(agents.get("ders"), "r1")
    assert "merhaba" in sb.call("read_note", path="10-Dersler/ok.md")
    assert sb.call("read_note", path="10-Dersler/late2.md") == ""
    assert sb.call("read_note", path="10-Dersler/late.md") == ""


def test_sandbox_symlink_escape(avault):
    link = avault / "10-Dersler" / "link"
    try:
        link.symlink_to(avault / "30-Kariyer", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("sembolik bağ oluşturulamadı")
    with pytest.raises(PermissionError):
        agents.Sandbox(agents.get("ders"), "r2").call("read_note", path="10-Dersler/link/x.md")


def test_sandbox_research_filtered(avault, monkeypatch):
    from sb import brain, search
    hits = [{"doc_id": i, "kind": "note", "title": t, "ref": r, "date": "", "text": "metin"} for i, (t, r) in enumerate([
        ("ok", "10-Dersler/ok.md"), ("priv", "10-Dersler/late.md"), ("kariyer", "30-Kariyer/x.md"), ("mail", "msg-123")])]
    monkeypatch.setattr(brain, "find", lambda *a, **k: hits)
    monkeypatch.setattr(search, "_plan", lambda q: ["alt"])
    monkeypatch.setattr(search, "_log_question", lambda q: None)
    monkeypatch.setattr(llm, "complete", lambda *a, **k: ("rapor [1]", "yerel"))
    ag = dict(agents.get("ders"), araclar=["research"])
    r = agents.Sandbox(ag, "r3").call("research", question="q")
    assert [s["label"].split(" · ")[1] for s in r["sources"]] == ["ok"]


# ---- 6 deep / 7 career / 8 mcp
def test_deep_disallowed_tools(monkeypatch, tmp_path):
    from sb import deep
    got = {}

    class P:
        returncode, stderr = 0, ""
        stdout = json.dumps({"result": "ok", "is_error": False})

    def fake(cmd, **k):
        got["cmd"] = cmd
        return P()
    monkeypatch.setattr(deep.subprocess, "run", fake)
    try:
        deep.run_claude(tmp_path, "x")
    except Exception:
        pass
    deny = got["cmd"][got["cmd"].index("--disallowedTools") + 1]
    for pat in ("*.pfx", "*.p12", "*.kdbx", ".npmrc", ".aws/**", "*.pem", "*.key", "id_rsa*", ".git-credentials", "*cookies*", "Login Data"):
        assert pat in deny, pat


def test_career_inside_prefix_trick(tmp_path, monkeypatch):
    from sb import career
    v = tmp_path / "vault"
    (v / "a").mkdir(parents=True)
    (v / "a" / "n.md").write_text("x", encoding="utf-8")
    evil = tmp_path / "vault-evil"
    evil.mkdir()
    (evil / "s.md").write_text("sır", encoding="utf-8")
    monkeypatch.setattr(career, "_vault", lambda: v)
    assert career._inside("a/n.md").name == "n.md"
    with pytest.raises(ValueError):
        career._inside("../vault-evil/s.md")


def test_brain_note_system_and_private(tmp_path, monkeypatch):
    from sb import mcp_server as ms
    v = tmp_path / "vault"
    (v / "_system" / "config").mkdir(parents=True)
    (v / "_system" / "config" / "s.md").write_text("SIR", encoding="utf-8")
    (v / "60").mkdir()
    (v / "60" / "Gizli.md").write_text("---\nvisibility: private\n---\nGIZLI-ICERIK", encoding="utf-8")
    (v / "60" / "Acik.md").write_text("açık içerik", encoding="utf-8")
    monkeypatch.setattr(ms, "VAULT", v)
    assert "SIR" not in ms.brain_note("_system/config/s.md")
    r = ms.brain_note("60/Gizli.md")
    assert "GIZLI-ICERIK" not in r and "Gizli" in r
    assert "açık içerik" in ms.brain_note("60/Acik.md")


# ---- 9 zip bombası
def _zip(path, n=1, size=10):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(n):
            zf.writestr(f"f{i}.xml", b"a" * size)
    return path


def test_guard_zip(tmp_path, monkeypatch):
    content.guard_zip(_zip(tmp_path / "ok.zip"))
    monkeypatch.setattr(content, "MAX_UNZIPPED", 1000)
    with pytest.raises(ValueError):
        content.guard_zip(_zip(tmp_path / "big.zip", 1, 5000))
    monkeypatch.setattr(content, "MAX_UNZIPPED", 10**9)
    monkeypatch.setattr(content, "MAX_ZIP_FILES", 3)
    many = _zip(tmp_path / "many.zip", 10, 1)
    with pytest.raises(ValueError):
        content.guard_zip(many)
    for fn in (content._docx, content._pptx, content._xlsx):
        with pytest.raises(ValueError):
            fn(many)


# ---- 10 update
def test_update_previews_and_asks_before_pull(tmp_path, monkeypatch, capsys):
    from sb import update
    calls = []

    class R:
        def __init__(self, out="", rc=0):
            self.stdout, self.returncode, self.stderr = out, rc, ""

    def fake_run(cmd, **k):
        calls.append(cmd)
        sub = [c for c in cmd if c in ("fetch", "rev-list", "show", "log", "diff", "pull", "merge", "tag")]
        out = {"rev-list": "2", "show": "9.9.9", "log": "abc123 yeni özellik\ndef456 düzeltme",
               "diff": "a.py\nb.py\nc.py", "tag": "v9.9.9\nv9.9.0"}.get(sub[0] if sub else "", "")
        return R(out)
    kit = tmp_path / "kit"
    (kit / ".git").mkdir(parents=True)
    monkeypatch.setattr(update, "_kit", lambda: (kit, tmp_path))
    monkeypatch.setattr(update, "backup", lambda: tmp_path / "b.zip")
    monkeypatch.setattr(update, "_install", lambda *a: 0)
    monkeypatch.setattr(update.subprocess, "run", fake_run)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert update.run() == 1                                      # onay yok → pull yok
    out = capsys.readouterr().out
    assert "abc123" in out and "Değişen dosya: 3" in out
    assert not any("pull" in c for c in calls)
    assert update.run(yes=True) == 0
    assert any("pull" in c for c in calls)
    calls.clear()
    assert update.run(yes=True, tags_only=True) == 0
    assert any("merge" in c and "v9.9.9" in c for c in calls) and not any("pull" in c for c in calls)
