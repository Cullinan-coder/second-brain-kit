"""Kurulum sihirbazı DENEME KİPİ (SB_SETUP_SANDBOX): tam API akışı uçtan uca.

Deneme kipinde gerçek sisteme dokunulmaz: zamanlanmış görev, kısayol/Başlangıç, claude mcp, ollama, winget, OAuth atlanır;
şifre kasası yerine <deneme>/keyring.json kullanılır. `uv`/`doctor`/içe aktarma yalnız burada taklit edilir (git gerçektir).
conftest'in kapıları (testte gerçek komut/keyring yok) bu testte sandbox katmanının ALTINA (_exec_*) iner: yan etkili komut
oraya hiç ulaşmamalı."""
import http.client
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SYSTEM))

from setup import engine as E  # noqa: E402
from setup import mcp as M  # noqa: E402
from setup import server as S  # noqa: E402
from setup import timez as TZ  # noqa: E402

# conftest kapıları test başında devreye girer; sandbox'ın asıl işlevlerini import anında yakala
_CAP, _STREAM, _KR, _EXEC_STREAM = E._run_capture, E._run_stream, E._keyring, E._exec_stream

SECRET = "sk-DENEMESIR1234567890abcdef"
PW = "parola-gizli-hunter2"
CWDS: list = []                                                # sandbox katmanını geçen komutların çalışma dizinleri
FORBIDDEN = ("schtasks", "scheduledtask", "createshortcut", "mcp add", "mcp remove", "ollama pull", "winget", "install_cli", "--extra",
             "ollamasetup", "launchctl")


@pytest.fixture
def sbx(tmp_path, monkeypatch):
    box = tmp_path / "deneme"
    monkeypatch.setenv("SB_SETUP_SANDBOX", str(box))
    monkeypatch.delenv("SB_DATA", raising=False)
    monkeypatch.setattr(E, "_run_capture", _CAP)
    monkeypatch.setattr(E, "_run_stream", _STREAM)
    monkeypatch.setattr(E, "_keyring", _KR)
    monkeypatch.setattr(E, "kit_dir", lambda: None)
    monkeypatch.setattr(E, "_trash", lambda: None)
    monkeypatch.setattr(E, "_http", lambda *a, **k: (200, "{}"))
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("testte gerçek ağ yok")))
    E.SANDBOX_SKIPPED.clear()
    CWDS.clear()
    real: list[list[str]] = []                                 # sandbox katmanını GEÇİP gerçek yürütmeye ulaşan komutlar

    def cap(cmd, timeout=15, cwd=None):
        real.append([str(x) for x in cmd])
        CWDS.append(str(cwd or ""))
        j = " ".join(map(str, cmd))
        if "doctor" in j:
            return 0, "  ✓ kasa → tamam\n  ! yerel model → ollama yok\nSürüm 1.0"
        if "import" in j and "--dry-run" in j:
            return 0, "okunan 3 mesaj"
        return 127, "yok"

    def stream(cmd, log, cwd=None):
        real.append([str(x) for x in cmd])
        CWDS.append(str(cwd or ""))
        if str(cmd[0]) == "git":                               # git gerçekten çalışır (deneme kasasında)
            return _EXEC_STREAM(cmd, log, cwd)
        log("$ " + " ".join(map(str, cmd)))
        if "sync" in cmd:                                      # uv sync taklit: sanal ortam <proje>/.venv (proje = --directory ya da cwd)
            proj = Path(cmd[cmd.index("--directory") + 1]) if "--directory" in cmd else Path(cwd)
            (proj / ".venv").mkdir(exist_ok=True)
        return 0
    monkeypatch.setattr(E, "_exec_capture", cap)
    monkeypatch.setattr(E, "_exec_stream", stream)
    monkeypatch.setattr(E, "_imap_login", lambda host, user, pw, port=993: (False, "IMAP girişi başarısız: gaierror"))
    s = S.make_server().start()
    port, tok = s.server_address[1], s.token

    def call(method, path, body=None, raw=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        h = {"X-Setup-Token": tok, **(headers or {})}
        data = raw
        if body is not None:
            data, h["Content-Type"] = json.dumps(body).encode(), "application/json"
        c.request(method, path, body=data, headers=h)
        r = c.getresponse()
        txt = r.read().decode("utf-8")
        c.close()
        return r.status, json.loads(txt) if txt else {}

    def wait(timeout=120):
        end = time.time() + timeout
        while time.time() < end:
            _, p = call("GET", "/api/progress")
            if not p["running"]:
                return p
            time.sleep(0.1)
        raise AssertionError("iş bitmedi")
    yield call, wait, box, real, s.engine
    s.stop()


# ------------------------------------------------------------------ saat dilimi ve varsayılanlar
@pytest.mark.parametrize("raw,want", [("Gmt+3", "Etc/GMT-3"), ("GMT+3", "Etc/GMT-3"), ("UTC+3", "Etc/GMT-3"), ("+3", "Etc/GMT-3"),
                                      ("+03:00", "Etc/GMT-3"), ("-5", "Etc/GMT+5"), ("Türkiye", "Europe/Istanbul"), ("İstanbul", "Europe/Istanbul"),
                                      ("istanbul", "Europe/Istanbul"), ("Europe/Istanbul", "Europe/Istanbul"), ("europe/london", "Europe/London"),
                                      ("+5:30", "Asia/Kolkata"), ("UTC", "UTC"), ("gmt", "GMT"), ("Berlin", "Europe/Berlin"), ("Almanya", "Europe/Berlin")])
def test_saat_dilimi_normallestirme(raw, want, monkeypatch):
    monkeypatch.setattr(TZ, "prefer_istanbul", lambda: False)      # Türkiye yerel ayarı bağımsız (madde 17 ayrı testte)
    assert TZ.normalize(raw) == want


@pytest.mark.parametrize("raw", ["Gmt+3", "GMT+3", "UTC+3", "+3", "+03:00"])
def test_saat_dilimi_turkiyede_istanbul_tercih_edilir(raw, monkeypatch):
    monkeypatch.setattr(TZ, "prefer_istanbul", lambda: True)
    assert TZ.normalize(raw) == "Europe/Istanbul"
    assert TZ.normalize("-5") == "Etc/GMT+5" and TZ.normalize("+5:30") == "Asia/Kolkata"       # başka ofsetler değişmez


def test_prefer_istanbul_yerel_ayara_gore(monkeypatch):
    import locale
    monkeypatch.setattr(locale, "getlocale", lambda *a, **k: ("tr_TR", "UTF-8"))
    assert TZ.prefer_istanbul() is True
    monkeypatch.setattr(locale, "getlocale", lambda *a, **k: ("en_US", "UTF-8"))
    monkeypatch.setattr(TZ, "system_default", lambda: "Europe/London")
    assert TZ.prefer_istanbul() is False


def test_saat_dilimi_bos_varsayilan_ve_gecersiz():
    assert TZ.normalize("") == TZ.system_default() == TZ.normalize("varsayılan")
    for bad in ("Mars/Olympus", "GMT+99", "xyz123"):
        with pytest.raises(ValueError):
            TZ.normalize(bad)


def test_saat_dilimi_listesi_ve_istanbul_onerisi(monkeypatch):
    monkeypatch.setattr(TZ, "_local_offset_min", lambda: 180)
    monkeypatch.setitem(sys.modules, "tzlocal", None)
    assert TZ.system_default() == "Europe/Istanbul"
    lst = TZ.listing()
    assert lst["default"] == "Europe/Istanbul" and lst["list"][0]["id"] == "Europe/Istanbul" and "UTC+03:00" in lst["list"][0]["label"]
    assert any(x["id"] == "Etc/GMT-3" for x in lst["list"])


# ------------------------------------------------------------------ tam akış
def test_deneme_kipi_tam_akis(sbx, tmp_path, monkeypatch):
    monkeypatch.setattr(TZ, "prefer_istanbul", lambda: False)
    call, wait, box, real, eng = sbx
    vault = box / "SecondBrain"

    # varsayılanlar ve saat dilimi uçları
    st, d = call("GET", "/api/defaults")
    assert st == 200 and d["vault"] == str(vault) and d["sandbox"] == str(box)
    st, z = call("GET", "/api/timezones")
    assert st == 200 and z["default"] and z["list"] and {"id", "label"} <= set(z["list"][0])

    # katalog → hazır seçim → birleştir → gereksinimler
    st, cat = call("GET", "/api/catalog")
    assert st == 200 and cat["modules"]
    st, pr = call("GET", "/api/presets")
    assert st == 200 and "yazilimci" in [x["id"] for x in pr["axes"]["meslek"]]
    st, comb = call("POST", "/api/combine", {"meslek": "yazilimci", "donanim": "zayif_bulut", "gizlilik": "karma", "yogunluk": "gunluk"})
    assert st == 200 and comb["modules"]
    st, rq = call("POST", "/api/requirements", {"modules": {m: True for m in comb["modules"]}, "items": {}})
    assert st == 200 and rq["accounts"]

    # kişisel bilgiler: boş kasa + "Gmt+3"
    st, r = call("POST", "/api/profile/basic", {"name": "Ayşe", "vault": "", "timezone": "Gmt+3"})
    assert st == 200 and r["fields"]["vault"] == str(vault) and r["fields"]["timezone"] == "Etc/GMT-3"
    for v in ("varsayılan", "default"):
        st, r = call("POST", "/api/profile/basic", {"name": "Ayşe", "vault": v, "timezone": ""})
        assert st == 200 and r["fields"]["vault"] == str(vault) and r["fields"]["timezone"] == TZ.system_default()
    assert call("POST", "/api/profile/basic", {"name": "Ayşe", "vault": "", "timezone": "Mars/X"})[0] == 400
    assert call("POST", "/api/profile/basic", {"name": "", "vault": ""})[0] == 400

    # sır → keyring.json (gerçek keyring değil)
    st, r = call("POST", "/api/secret", {"key": "api-openai", "value": SECRET})
    assert st == 200 and r["set"]
    assert call("POST", "/api/secret", {"key": "svc-spotify-client-id", "value": "abc"})[0] == 200
    assert call("POST", "/api/secret", {"key": "spotify_client_id", "value": "abc"})[0] == 400
    kr = json.loads((box / "keyring.json").read_text(encoding="utf-8"))
    assert kr["second-brain/api-openai"] == SECRET

    # IMAP doğrulama hatası (gerçek test taklit: başarısız) ve sonra başarı
    st, r = call("POST", "/api/account/imap", {"alias": "posta", "preset": "gmail", "user": "a@gmail.com", "password": PW})
    assert st == 200 and r["ok"] is False and "başarısız" in r["message"] and PW not in json.dumps(r)
    monkeypatch.setattr(E, "_imap_login", lambda host, user, pw, port=993: (True, "IMAP girişi başarılı"))
    st, r = call("POST", "/api/account/imap", {"alias": "posta", "preset": "gmail", "user": "a@gmail.com", "password": PW})
    assert st == 200 and r["ok"] is True
    assert json.loads((box / "keyring.json").read_text(encoding="utf-8"))["second-brain/imap-posta"] == PW

    # Google: önce client_secret yok → hata; yükleme doğrulaması; e-posta zorunlu; sonra "deneme: bağlandı"
    st, acc = call("GET", "/api/accounts")
    assert st == 200 and acc["client_secret"] is False and [x["alias"] for x in acc["imap"]] == ["posta"]
    st, r = call("POST", "/api/account/google", {"alias": "ana", "email": "a@gmail.com", "scopes": ["gmail"]})
    assert st == 200 and r["ok"] is False and "client_secret" in r["message"]
    assert call("POST", "/api/upload/client-secret", raw=b"degil json", headers={"Content-Type": "application/json"})[0] == 400
    assert call("POST", "/api/upload/client-secret", raw=b'{"foo": 1}', headers={"Content-Type": "application/json"})[0] == 400
    st, r = call("POST", "/api/upload/client-secret", raw=json.dumps({"installed": {"client_id": "x.apps", "client_secret": "y"}}).encode(),
                 headers={"Content-Type": "application/json"})
    assert st == 200 and r["ok"] and (box / "data" / "secrets" / "client_secret.json").is_file()
    assert call("GET", "/api/accounts")[1]["client_secret"] is True
    assert call("POST", "/api/account/google", {"alias": "ana", "scopes": ["gmail"]})[0] == 400          # e-posta yok
    assert call("POST", "/api/account/google", {"alias": "ana", "email": "yanlis", "scopes": ["gmail"]})[0] == 400
    st, r = call("POST", "/api/account/google", {"alias": "ana", "email": "a@gmail.com", "scopes": ["gmail", "calendar"]})
    assert st == 200 and r["ok"] is True and r["sandbox"] is True and "deneme" in r["message"]
    assert call("GET", "/api/accounts")[1]["google"][0]["authorized"] is True

    # MCP: claude mcp add atlanır, kayıt yalnız deneme klasöründeki Claude Desktop kopyasına
    assert M.desktop_config_path() == box / "claude_desktop_config.json"
    st, r = call("POST", "/api/mcp/install", {"id": "second-brain"})
    assert st == 200 and r["ok"] is True
    cfg = json.loads((box / "claude_desktop_config.json").read_text(encoding="utf-8"))
    assert "second-brain" in cfg["mcpServers"]
    st, ov = call("GET", "/api/mcp")
    assert st == 200 and any(i["name"] == "second-brain" for i in ov["installed"])

    # veri yükleme: küçük uydurma WhatsApp dosyası → önizleme → içe aktarma
    chat = "12.03.2024 10:15 - Ali: merhaba\n12.03.2024 10:16 - Ayşe: selam\n12.03.2024 10:17 - Ali: nasılsın\n".encode("utf-8")
    st, r = call("POST", "/api/import/upload?source=whatsapp&name=sohbet.txt", raw=chat, headers={"Content-Type": "application/octet-stream"})
    assert st == 200 and r["size"] == len(chat) and (box / "data" / "import_staging" / "whatsapp" / "sohbet.txt").is_file()
    st, r = call("POST", "/api/import/preview", {"source": "whatsapp", "file": "sohbet.txt"})
    assert st == 200 and r["ok"] and r["read"] == 3
    st, r = call("POST", "/api/import/run", {"source": "whatsapp", "file": "sohbet.txt"})
    assert st == 202
    assert not wait()["error"]
    assert call("GET", "/api/imports")[1]["imports"][0]["ok"] is True

    # otomatik başlatma: yalnız deneme klasörüne
    st, r = call("POST", "/api/autostart", {"on": True, "minimized": True})
    assert st == 200 and r["ok"] and r["on"] is True
    assert any(d.exists() and any(d.iterdir()) for d in (box / "Startup", box / "LaunchAgents"))      # Windows: Startup, macOS: LaunchAgents

    # apply (UI'nın gönderdiği biçim): selection + meslek kimliği E.PRESETS'te yok → "tam"
    sel = {"modules": comb["modules"], "items": comb["items"]}
    st, r = call("POST", "/api/apply", {"selection": {"axes": {"meslek": "yazilimci"}, **sel}, "preset": "yazilimci", **sel, "fields": {}})
    assert st == 202, r
    p = wait()
    assert not p["error"], p["error"]
    assert all(s["status"] in ("done", "skipped") for s in p["steps"]), p["steps"]
    assert (vault / "_system" / "config" / "profile.yaml").is_file()
    prof = (vault / "_system" / "config" / "profile.yaml").read_text(encoding="utf-8")
    assert "Ayşe" in prof and "timezone:" in prof            # profil adımı alanları apply'da kaybolmadı (CI saat dilimi UTC olabilir)
    assert (vault / "_system" / "config" / "features.yaml").is_file()
    assert (vault / "_system" / "sb").is_dir() and (vault / "_system" / ".venv").is_dir()      # kod kopyalandı + uv sync (taklit)
    if shutil.which("git"):
        assert (vault / ".git").is_dir()
    assert (box / "keyring.json").is_file()

    # gerçek sisteme dokunulmadı
    flat = [" ".join(c).lower() for c in real]
    assert not [c for c in flat if any(f in c for f in FORBIDDEN)], flat
    skipped = " ".join(E.SANDBOX_SKIPPED).lower()
    assert "[deneme] atlandı" in " ".join(E.SANDBOX_SKIPPED) and "mcp add" in skipped
    if sys.platform == "win32":
        assert "createshortcut" in skipped and "schedule" in skipped
    # günlükte sır yok (ne API anahtarı ne IMAP şifresi); sihirbaz/durum dosyalarında da
    log = "\n".join(p["log"])
    assert "[deneme] atlandı" in log and SECRET not in log and PW not in log
    for f in (box / "data").glob("*.json"):
        assert SECRET not in f.read_text(encoding="utf-8") and PW not in f.read_text(encoding="utf-8")
    accy = (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")
    assert PW not in accy and SECRET not in accy and "a@gmail.com" in accy
    # her şey deneme klasörünün altında
    assert vault.is_relative_to(box) and eng.data.is_relative_to(box)


def test_mcp_komut_gunlukte_sir_maskelenir(sbx):
    call, wait, box, real, eng = sbx
    assert E._run_stream(["claude", "mcp", "add", "x", "-e", f"KEY={SECRET}", "--", "npx"], eng.log) == 0
    assert SECRET not in "\n".join(eng.progress()["log"]) and "[deneme] atlandı" in "\n".join(eng.progress()["log"])
    assert not real


def test_deneme_disinda_filtre_yok(monkeypatch, tmp_path):
    monkeypatch.delenv("SB_SETUP_SANDBOX", raising=False)
    assert E.sandbox_dir() is None and not E._sandbox_skip(["schtasks", "/create"])
    assert E.default_vault() == Path.home() / "SecondBrain"


# ------------------------------------------------------------------ canlı deneme bulguları (2026-11-04)
def _norm(s) -> str:
    return str(s).replace("\\", "/").lower()


def _real_system() -> str:
    return _norm(SYSTEM)


def _assert_no_real_system(cmds, cwds, box):
    """Hiçbir komutta (argüman ya da çalışma dizini) çalışan kurulumun `_system` yolu geçmez; --directory/cwd deneme klasörünün altında."""
    rs = _real_system()
    for c in cmds:
        for a in c:
            assert rs not in _norm(a) or _norm(box) in _norm(a), (c, a)
        if "--directory" in c:
            d = c[c.index("--directory") + 1]
            assert Path(d).resolve().is_relative_to(box.resolve()), c
    for w in cwds:
        if w:
            assert Path(w).resolve().is_relative_to(box.resolve()), w


def test_madde1_deneme_kipi_hicbir_komutta_gercek_system_yok(sbx):
    """Madde 1: içe aktarma / MCP / ses / apply — üretilen BÜTÜN komutlar (atlananlar dahil) deneme klasörünün altında."""
    call, wait, box, real, eng = sbx
    chat = "12.03.2024 10:15 - Ali: merhaba\n".encode("utf-8")
    assert call("POST", "/api/import/upload?source=whatsapp&name=s.txt", raw=chat, headers={"Content-Type": "application/octet-stream"})[0] == 200
    assert call("POST", "/api/import/preview", {"source": "whatsapp", "file": "s.txt"})[0] == 200      # kurulumdan ÖNCE: kod deneme kasasına hazırlanır
    assert call("POST", "/api/import/run", {"source": "whatsapp", "file": "s.txt"})[0] == 202
    assert not wait()["error"]
    assert call("POST", "/api/mcp/install", {"id": "second-brain"})[0] == 200
    assert call("POST", "/api/voice/setup", {"gpu": True})[0] == 202
    assert not wait()["error"]
    assert call("POST", "/api/apply", {"selection": {"modules": {}, "items": {}}, "preset": "minimal", "fields": {"name": "A"}})[0] == 202
    assert not wait()["error"]
    assert real and E.SANDBOX_SKIPPED
    _assert_no_real_system(real, CWDS, box)
    skipped = [s.removeprefix("[deneme] atlandı: ").split(" ") for s in E.SANDBOX_SKIPPED]
    _assert_no_real_system(skipped, [], box)
    voice = [s for s in E.SANDBOX_SKIPPED if "--extra" in s]
    assert voice and all(_norm(box) in _norm(s) for s in voice)
    assert eng.code_root() == (box / "SecondBrain" / "_system")


def test_madde1_code_root_kasa_secilmeden_de_denemede(sbx):
    call, wait, box, real, eng = sbx
    assert eng.vault is None
    assert eng.code_root() == box / "SecondBrain" / "_system"
    assert (box / "SecondBrain" / "_system" / "sb").is_dir()                  # kod hedefe kopyalandı
    assert eng.health()["ok"] in (True, False)                                  # doctor da HEDEF _system'de
    assert all(_real_system() not in _norm(" ".join(c)) or _norm(box) in _norm(" ".join(c)) for c in real)


def test_madde1_ayni_klasore_kopyalama_reddedilir(tmp_path):
    with pytest.raises(RuntimeError):
        E.sync_code(SYSTEM, SYSTEM)
    with pytest.raises(RuntimeError):
        E.sync_code(tmp_path, tmp_path)


def test_madde2_sync_code_yalniz_kod_ve_ornek_config(tmp_path):
    src = tmp_path / "src"
    for rel, txt in {"sb/__init__.py": "", "sb/__pycache__/x.pyc": "x", "config/profile.yaml": "bio: gizli", "config/profile.example.yaml": "bio: ornek",
                     "config/accounts.yaml": "a: 1", "data/obs.yaml": "gizli", ".venv/Scripts/python.exe": "x", "docs/kullanici.md": "k",
                     "docs/v1-plan.md": "p", "docs/faz2-sartname.md": "s", "docs/kurulum-canli-deneme-bulgulari.md": "b", "pyproject.toml": "[project]",
                     "VERSION": "1.0"}.items():
        f = src / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(txt, encoding="utf-8")
    dst = tmp_path / "dst"
    (dst / "config").mkdir(parents=True)
    (dst / "config" / "profile.yaml").write_text("bio: hedefin kendi ayari", encoding="utf-8")     # var olan kişisel dosyaya dokunulmaz
    E.sync_code(src, dst)
    assert sorted(p.name for p in (dst / "config").glob("*.yaml")) == ["profile.example.yaml", "profile.yaml"]
    assert (dst / "config" / "profile.yaml").read_text(encoding="utf-8") == "bio: hedefin kendi ayari"
    assert not (dst / "data").exists() and not (dst / ".venv").exists() and not list(dst.rglob("__pycache__"))
    assert sorted(p.name for p in (dst / "docs").iterdir()) == ["kullanici.md"]
    assert (dst / "pyproject.toml").is_file() and (dst / "VERSION").is_file()


def test_madde2_gercek_agacta_kisisel_ayar_kopyalanmaz(tmp_path):
    dst = tmp_path / "kopya" / "_system"
    E.sync_code(SYSTEM, dst)
    extra = [p.name for p in (dst / "config").glob("*.yaml") if not p.name.endswith(".example.yaml")]
    assert extra == [], extra
    assert not (dst / "data").exists() and not (dst / ".venv").exists() and not list(dst.rglob("__pycache__"))
    assert not [p.name for p in (dst / "docs").glob("*.md") if E.internal_doc(p.name)]
    assert (dst / "sb").is_dir() and (dst / "docs" / "mcp-second-brain.md").is_file()


def test_madde2_deneme_kasasinda_profil_kisisel_degil(sbx):
    call, wait, box, real, eng = sbx
    import yaml
    src = yaml.safe_load((SYSTEM / "config" / "profile.yaml").read_text(encoding="utf-8")) or {}
    ex = SYSTEM / "config" / "profile.example.yaml"
    example = (yaml.safe_load(ex.read_text(encoding="utf-8")) or {}) if ex.exists() else {}
    # yalnız örnek dosyadan FARKLI (kişisel) değerler sızmamalı; kurulu bir kopyada profil zaten örnektir
    secret_vals = [str(v) for k, v in src.items() if k in ("bio", "github_user", "workspace") and v and example.get(k) != v]
    assert call("POST", "/api/apply", {"selection": {"modules": {}, "items": {}}, "preset": "minimal", "fields": {"name": "Ayşe"}})[0] == 202
    assert not wait()["error"]
    prof = (box / "SecondBrain" / "_system" / "config" / "profile.yaml").read_text(encoding="utf-8")
    got = yaml.safe_load(prof) or {}                       # alt metin değil değer karşılaştırması ('ci' gibi kısa değerler her yerde geçer)
    assert got.get("name") == "Ayşe" and not [k for k in ("bio", "github_user", "workspace") if str(got.get(k) or "") in secret_vals]
    for name in ("mail_rules.yaml", "course_files.yaml", "local_files.yaml", "session_map.yaml", "topic_map.yaml", "sohbet_eslesme.yaml"):
        a, b = SYSTEM / "config" / name, box / "SecondBrain" / "_system" / "config" / name
        if a.exists() and not (SYSTEM / "config" / name.replace(".yaml", ".example.yaml")).exists():
            assert not b.exists(), name                                          # örneği olmayan kişisel dosya kopyalanmadı


def test_madde3_venv_kasa_sistem_altinda(sbx, monkeypatch):
    call, wait, box, real, eng = sbx
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(box))        # dışarıdan sızan ortam kasa köküne venv kurdurmasın
    assert call("POST", "/api/apply", {"selection": {"modules": {}, "items": {}}, "preset": "minimal", "fields": {"name": "A"}})[0] == 202
    assert not wait()["error"]
    vault = box / "SecondBrain"
    assert (vault / "_system" / ".venv").is_dir()
    assert not (vault / ".venv").exists() and not (vault / "Lib").exists() and not (vault / "Scripts").exists() and not (vault / "CACHEDIR.TAG").exists()
    sync = [c for c in real if "sync" in c and "--extra" not in c]
    assert sync and all(c[c.index("--directory") + 1] == str(vault / "_system") for c in sync)
    assert all(Path(w).resolve() == (vault / "_system").resolve() for c, w in zip(real, CWDS) if "sync" in c and "--extra" not in c)


def test_madde3_proc_env_uv_sanal_ortami_proje_altinda(tmp_path, monkeypatch):
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "/baska/yer")
    monkeypatch.setenv("VIRTUAL_ENV", "/gercek/.venv")
    sysd = tmp_path / "_system"
    e = E.proc_env(["uv", "sync", "--directory", str(sysd)], tmp_path)
    assert e["UV_PROJECT_ENVIRONMENT"] == str(sysd / ".venv") and "VIRTUAL_ENV" not in e
    e = E.proc_env([r"C:\bin\uv.exe", "sync"], sysd)
    assert e["UV_PROJECT_ENVIRONMENT"] == str(sysd / ".venv")
    e = E.proc_env(["git", "status"], sysd)                         # uv olmayan komutlara dokunulmaz
    assert e["UV_PROJECT_ENVIRONMENT"] == "/baska/yer"


def test_madde4_uzun_yol_ve_onedrive_uyarisi(sbx, monkeypatch):
    call, wait, box, real, eng = sbx
    monkeypatch.setattr(E, "WIN", True)
    short = "C:\\Users\\ali\\SecondBrain"
    assert E.path_warnings(short) == []
    long = "C:\\Users\\ali\\Documents\\" + "cok-uzun-klasor-adi\\" * 6 + "SecondBrain"
    w = E.path_warnings(long)
    assert [x["code"] for x in w] == ["long_path"] and "260" in w[0]["message"] and w[0]["suggest"].endswith("SecondBrain")
    ow = E.path_warnings("C:\\Users\\ali\\OneDrive\\Belgeler\\SecondBrain")
    assert [x["code"] for x in ow] == ["onedrive"]
    # API: kişisel bilgiler adımı ve ayrı denetim ucu uyarı döner
    st, r = call("POST", "/api/profile/basic", {"name": "Ali", "vault": str(box / ("x" * 200)), "timezone": "UTC"})
    assert st == 200 and any(x["code"] == "long_path" for x in r["warnings"])
    st, r = call("POST", "/api/path/check", {"vault": long})
    assert st == 200 and r["warnings"][0]["code"] == "long_path"
    st, r = call("POST", "/api/path/check", {"vault": short})
    assert r["warnings"] == []
    # apply öncesi aynı denetim günlüğe UYARI yazar
    call("POST", "/api/profile/basic", {"name": "Ali", "vault": str(box / ("y" * 200)), "timezone": "UTC"})
    assert call("POST", "/api/apply", {"selection": {"modules": {}, "items": {}}, "preset": "minimal", "fields": {"name": "Ali"}})[0] == 202
    p = wait()
    assert any("UYARI" in ln and "260" in ln for ln in p["log"])


def test_madde21_hata_karti_ve_yeniden_dene(sbx, monkeypatch):
    call, wait, box, real, eng = sbx
    orig = E._exec_stream

    def failing(cmd, log, cwd=None):
        if "sync" in cmd and "--extra" not in cmd:
            log("error: Failed to persist temporary file: os error 3")
            return 2
        return orig(cmd, log, cwd)
    monkeypatch.setattr(E, "_exec_stream", failing)
    body = {"selection": {"modules": {}, "items": {}}, "preset": "minimal", "fields": {"name": "A"}}
    assert call("POST", "/api/apply", body)[0] == 202
    p = wait()
    ei = p["error_info"]
    assert p["error"] and ei["step"] == "deps" and ei["retry"] is True
    assert "os error 3" in ei["message"] and "260" in ei["hint"] and "Yeniden dene" in ei["hint"]
    st = {s["id"]: s["status"] for s in p["steps"]}
    assert st["deps"] == "error" and st["vault"] == "done" and st["claude"] == "pending"
    assert any("NE YAPMALI" in ln for ln in p["log"])
    # düzelt → sürdür: biten adımlar tekrarlanmaz, hata kartı temizlenir
    monkeypatch.setattr(E, "_exec_stream", orig)
    n_before = len([ln for ln in eng.progress()["log"] if "== Kasa ve kod ==" in ln])
    assert call("POST", "/api/apply", {**body, "resume": True})[0] == 202
    p2 = wait()
    assert not p2["error"] and p2["error_info"] is None
    assert all(s["status"] in ("done", "skipped") for s in p2["steps"])
    assert len([ln for ln in p2["log"] if "== Kasa ve kod ==" in ln]) <= n_before          # biten adım yeniden çalışmadı
    assert any("== Python ortamı ==" in ln for ln in p2["log"])


def test_step_hint_ipuclari():
    assert "260" in E.step_hint("deps", "uv sync başarısız: Failed to persist temporary file (os error 3)")
    assert "İnternet" in E.step_hint("deps", "connection timed out")
    for sid, _ in E.STEPS:
        h = E.step_hint(sid, "bilinmeyen")
        assert "Yeniden dene" in h or "günlüğ" in h.lower()


def test_madde20_sihirbazda_kaydedilen_sirlar_sayilir(sbx):
    call, wait, box, real, eng = sbx
    assert call("POST", "/api/secret", {"key": "api-openai", "value": SECRET})[0] == 200
    assert call("POST", "/api/secret", {"key": "svc-github-pat", "value": "ghp_denemedeger"})[0] == 200
    assert call("POST", "/api/apply", {"selection": {"modules": {}, "items": {}}, "preset": "minimal", "fields": {"name": "A"}})[0] == 202
    p = wait()
    sec = next(s for s in p["steps"] if s["id"] == "secrets")
    assert sec["status"] == "done"                                   # "atlandı: girilecek sır yok" değil
    line = next(ln for ln in p["log"] if "sır şifre kasasında" in ln)
    assert "2 sır" in line and "api-openai" in line and "svc-github-pat" in line
    assert SECRET not in "\n".join(p["log"]) and "ghp_denemedeger" not in "\n".join(p["log"])


def test_madde16_ozet_ucu_sirlari_adla_verir(sbx):
    call, wait, box, real, eng = sbx
    call("POST", "/api/profile/basic", {"name": "Ayşe", "vault": "", "timezone": "UTC"})
    call("POST", "/api/secret", {"key": "api-openai", "value": SECRET})
    st, sm = call("GET", "/api/summary")
    assert st == 200 and sm["vault"] == str(box / "SecondBrain") and sm["sandbox"] == str(box) and sm["timezone"] == "UTC"
    assert sm["secrets"] == ["api-openai"] and SECRET not in json.dumps(sm)
    assert set(sm) >= {"accounts", "mcps", "imports", "models"}
    # okul: adres + kullanıcı hesaplara, şifre keyring'e
    st, r = call("POST", "/api/account/school", {"url": "obs.okul.edu.tr", "user": "2021001"})
    assert st == 200 and r["ok"] and r["has_password"] is False
    assert call("POST", "/api/secret", {"key": "svc-school-password", "value": PW})[0] == 200
    acc = call("GET", "/api/accounts")[1]
    assert acc["school"] == {"url": "obs.okul.edu.tr", "user": "2021001", "has_password": True}
    assert PW not in json.dumps(acc) and PW not in (box / "SecondBrain" / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")
    assert call("POST", "/api/account/school", {"url": "http://!!", "user": "x"})[0] == 400
    assert call("GET", "/api/summary")[1]["accounts"]["school"]["user"] == "2021001"
    assert call("POST", "/api/account/school", {"url": "", "user": ""})[1]["ok"]
    assert call("GET", "/api/accounts")[1]["school"] is None


def test_madde7_ice_aktarma_sayisi_gecmise_yazilir(sbx):
    call, wait, box, real, eng = sbx
    from setup import imports as IM
    assert IM.parse_count(["$ sb import whatsapp x", "  3 mesaj içe aktarıldı"]) == 3
    assert IM.parse_count(["yazılan: 12", "okunan 5"]) == 5
    assert IM.parse_count(["hiçbir sayı yok"]) is None
    IM._record(eng, "whatsapp", "s.txt", True, "ok", 3)
    assert call("GET", "/api/imports")[1]["imports"][-1]["count"] == 3


# ------------------------------------------------------------------ hazır uygulamalar (ClipBoardLine, Nashi)
def test_apps_sandbox_listing_install_autostart(sbx, monkeypatch):
    call, wait, box, real, eng = sbx
    from sb import apps
    monkeypatch.setattr(apps, "_proc_running", lambda name: False)
    for fn in ("_reg_set", "_reg_del", "_reg_get", "_spawn", "_open", "_run"):
        monkeypatch.setattr(apps, fn, lambda *a, **k: (_ for _ in ()).throw(AssertionError("deneme kipinde gerçek sistem/ağ çağrısı")))
    code, d = call("GET", "/api/apps?lang=tr")
    assert code == 200 and d["sandbox"] is True and [a["id"] for a in d["apps"]] == ["clipboardline", "nashi"]
    nashi = d["apps"][1]
    assert nashi["autostart"] == "login" and nashi["title"].startswith("Nashi") and nashi["about"] and nashi["license"] == "MIT"
    code, r = call("POST", "/api/apps/autostart", {"id": "nashi", "mode": "startup"})
    assert code == 200 and r["skipped"] and r["mode"] == "startup" and "[deneme] atlandı" in r["message"]
    assert call("GET", "/api/apps")[1]["apps"][1]["autostart"] == "startup"
    assert (box / "data" / "apps.json").exists()
    code, _ = call("POST", "/api/apps/autostart", {"id": "nashi", "mode": "bazen"})
    assert code == 400 and call("POST", "/api/apps/install", {"id": "yok"})[0] == 400
    code, _ = call("POST", "/api/apps/install", {"id": "clipboardline"})
    assert code == 202
    p = wait()
    assert not p["error"] and any("[deneme] atlandı: ClipBoardLine" in ln for ln in p["log"])
    code, r = call("POST", "/api/apps/start", {"id": "nashi"})
    assert code == 200 and r["skipped"]
    assert not [c for c in real if "apps" in " ".join(c)]
