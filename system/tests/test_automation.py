"""Paket A: otomasyon motoru (taklitli; gerçek takvim/model/WhatsApp/keyring yok)."""
import json
import sys
import types
from datetime import datetime

import pytest

from sb import api_auto, automation as au, chat, convstore, webroutes  # noqa: F401  (uçları kaydeder)
from sb.webroutes import Ctx

NOW = datetime(2026, 11, 2, 9, 30)   # pazartesi


def call(method, path, data=None, calendar=None):
    r = webroutes.find(method, path)
    assert r is not None, path
    ctx = Ctx(method, path, data or {}, {}, b"", "", "s1", False, chat.Session(), None, calendar)
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


class FakeCal:
    def __init__(self):
        self.added = []

    def add(self, ev, dry_run=True):
        self.added.append((ev, dry_run))
        return "created", {}


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(au, "DATA", tmp_path / "data")
    monkeypatch.setattr(au, "RULES_FILE", tmp_path / "otomasyon.yaml")
    sent = []
    monkeypatch.setattr(convstore, "notify", lambda *a, **k: sent.append(a) or {})
    fake = types.SimpleNamespace(find_contacts=lambda q, v: [("Ali", "+905550001122")],
                                 whatsapp_send=lambda p, t: sent.append(("WA", p, t)) or "gönderildi")
    monkeypatch.setitem(sys.modules, "sb.actions", fake)
    monkeypatch.setattr("sb.actions", fake, raising=False)
    from sb import vault_ops
    monkeypatch.setattr(vault_ops, "log", lambda *a, **k: {})
    return sent


def rule(**kw):
    base = {"ad": "Haftalık", "tetik": {"tur": "zaman", "saat": "09:00", "gun": "pazartesi"}, "eylem": {"tur": "bildirim", "baslik": "Selam"}}
    base.update(kw)
    return au.add_rule(base)


def test_bos_kural_listesi_ve_dogrulama():
    assert au.load_rules() == []
    code, out = call("POST", "/api/v2/automations", {"ad": "x", "tetik": {"tur": "yok"}, "eylem": {"tur": "bildirim"}})
    assert code == 400
    code, out = call("POST", "/api/v2/automations", {"ad": "x", "tetik": {"tur": "zaman", "saat": "9"}, "eylem": {"tur": "bildirim"}})
    assert code == 400


def test_zaman_tetik_bir_kez_calisir_ve_ac_kapa(env):
    r = rule()
    assert [x["sonuc"] for x in au.tick(NOW)] == ["bildirim"]
    assert au.tick(NOW) == []                                  # aynı slot tekrar çalışmaz
    assert au.tick(datetime(2026, 11, 3, 9, 30)) == []         # salı: gün tutmaz
    code, out = call("POST", "/api/v2/automations", {"id": r["id"], "acik": False})
    assert code == 200 and out["rule"]["acik"] is False
    assert au.tick(datetime(2026, 11, 9, 9, 30)) == []         # kapalı


def test_ozet_yerel_modelle(monkeypatch):
    seen = {}
    monkeypatch.setattr("sb.llm.complete", lambda task, prompt, **kw: seen.update(kw=kw) or ("özet metni", "x"))
    monkeypatch.setattr("sb.inbox.add", lambda text, source="": seen.update(note=text) or "ok")
    rule(eylem={"tur": "ozet", "istem": "haftalık rapor"})
    au.tick(NOW)
    assert seen["kw"]["private"] is True and "özet metni" in seen["note"]


def test_dis_etkili_eylem_onaysiz_yurutulmez(env):
    cal = FakeCal()
    rule(ad="Takvim", eylem={"tur": "takvim_oner", "baslik": "Toplantı", "gun": "2026-11-05", "saat": "10:00"})
    rule(ad="WA", eylem={"tur": "whatsapp_taslak", "kisi": "Ali", "metin": "selam"})
    res = au.tick(NOW)
    assert len(res) == 2 and all("onay bekliyor" in r["sonuc"] for r in res)
    assert not [e for e in env if e and e[0] == "WA"]          # WhatsApp gönderilmedi
    pend = au.approvals()
    assert len(pend) == 2 and all(p["durum"] == "bekliyor" for p in pend)
    code, out = call("GET", "/api/v2/approvals")
    assert code == 200 and len(out["approvals"]) == 2
    # reddet: hiçbir şey yürümez
    code, out = call("POST", "/api/v2/approvals/decide", {"id": pend[0]["id"], "ok": False}, cal)
    assert out["durum"] == "reddedildi" and cal.added == [] and not [e for e in env if e and e[0] == "WA"]
    # onayla
    tid = next(p for p in pend if p["tur"] == "takvim_oner")["id"]
    wid = next(p for p in pend if p["tur"] == "whatsapp_taslak")["id"]
    for i in (tid, wid):
        if i != pend[0]["id"]:
            call("POST", "/api/v2/approvals/decide", {"id": i, "ok": True}, cal)
    assert len(au.approvals()) == 0
    code, _ = call("POST", "/api/v2/approvals/decide", {"id": pend[1]["id"], "ok": True}, cal)
    assert code == 403                                         # çift yürütme yok


def test_takvim_onayi_calendar_yoluyla():
    cal = FakeCal()
    rule(eylem={"tur": "takvim_oner", "baslik": "Toplantı", "gun": "2026-11-05", "saat": "10:00"})
    au.tick(NOW)
    pid = au.approvals()[0]["id"]
    assert cal.added == []
    call("POST", "/api/v2/approvals/decide", {"id": pid, "ok": True}, cal)
    assert len(cal.added) == 1 and cal.added[0][1] is False and cal.added[0][0].title == "Toplantı"


def test_webhook_token(monkeypatch):
    import keyring
    monkeypatch.setattr(keyring, "get_password", lambda svc, name: "gizli" if name == "hook-n8n" else None)
    rule(ad="Hook", tetik={"tur": "webhook", "ad": "n8n"}, eylem={"tur": "bildirim", "baslik": "Geldi {konu}"})
    assert webroutes.find("POST", "/api/v2/hook").local_only is False
    code, _ = call("POST", "/api/v2/hook", {"name": "n8n", "token": "yanlis", "data": {}})
    assert code == 403
    code, _ = call("POST", "/api/v2/hook", {"name": "n8n", "token": "", "data": {}})
    assert code == 403
    code, _ = call("POST", "/api/v2/hook", {"name": "yok", "token": "gizli"})
    assert code == 403                                         # secret tanımsız
    code, out = call("POST", "/api/v2/hook", {"name": "n8n", "token": "gizli", "data": {"konu": "x"}})
    assert code == 200 and out["ran"] == 1


def test_webhook_ile_dis_eylem_de_onay_bekler(monkeypatch):
    import keyring
    monkeypatch.setattr(keyring, "get_password", lambda svc, name: "t")
    rule(ad="H", tetik={"tur": "webhook", "ad": "z"}, eylem={"tur": "whatsapp_taslak", "kisi": "Ali", "metin": "{konu}"})
    call("POST", "/api/v2/hook", {"name": "z", "token": "t", "data": {"konu": "merhaba"}})
    assert au.approvals()[0]["payload"]["metin"] == "merhaba"


def test_yeni_mail_ilk_calismada_susar_sonra_kosulla_tetikler(monkeypatch):
    mails = [{"konu": "Fatura geldi", "gonderen": "a", "ozet": "", "_ms": 5}, {"konu": "Selam", "gonderen": "b", "ozet": "", "_ms": 6}]
    monkeypatch.setattr(au, "_mail_events", lambda since: [m for m in mails if m["_ms"] > since])
    rule(ad="Mail", tetik={"tur": "yeni_mail"}, kosul={"alan": "konu", "iceren": "fatura"}, eylem={"tur": "bildirim", "baslik": "{konu}"})
    assert au.tick(NOW) == []                                  # ilk çalışma: yalnız işaret
    mails.append({"konu": "FATURA 2", "gonderen": "c", "ozet": "", "_ms": 10 ** 15})
    assert len(au.tick(datetime(2026, 11, 2, 10, 0))) == 1


def test_kuru_calistirma_yurutmez(env):
    r = rule(eylem={"tur": "whatsapp_taslak", "kisi": "Ali", "metin": "selam"})
    code, out = call("POST", "/api/v2/automations/test", {"id": r["id"]})
    assert code == 200 and out["onay_gerekir"] is True and "ONAY" in out["yapardi"]
    assert au.approvals() == []
    assert call("POST", "/api/v2/automations/test", {"id": "yok"})[0] == 404
