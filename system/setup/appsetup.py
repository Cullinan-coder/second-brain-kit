"""Kurulum paneli: hazır uygulamalar (ClipBoardLine, Nashi) uçlarının mantığı. Asıl iş `sb/apps.py`dedir (indirme, SHA-256, kurulum, başlangıç).

Deneme kipinde (`SB_SETUP_SANDBOX`) indirme/kurulum/başlangıç yazımı "[deneme] atlandı" olur; kayıt defterine ve gerçek klasörlere dokunulmaz.
"""
from __future__ import annotations

import sys

try:
    from . import engine as E
except ImportError:                                           # pragma: no cover
    import engine as E  # type: ignore


def sb_apps():
    cd = E.code_dir()
    if cd and str(cd) not in sys.path:
        sys.path.insert(0, str(cd))
    from sb import apps
    return apps


def _loc(v, lang: str) -> str:
    return E._t(v, E._lang(lang))


def listing(lang: str | None = "tr") -> dict:
    A = sb_apps()
    out = []
    for c in A.catalog():
        st = A.status(c["id"])
        out.append({**st, "title": _loc(c["name"], lang or "tr"), "desc": _loc(c["desc"], lang or "tr"),
                    "about": _loc(c["app"].get("about"), lang or "tr"), "homepage": c["app"].get("homepage"),
                    "license": c["app"].get("license"), "repo": c["app"].get("repo")})
    return {"apps": out, "sandbox": bool(E.sandbox_dir()), "modes": list(A.MODES), "default_mode": A.DEFAULT_MODE}


def _check(app_id: str):
    A = sb_apps()
    if str(app_id) not in A.ids():
        raise ValueError("bilinmeyen uygulama")
    return A


def install(eng, app_id: str, wait: bool = False) -> bool:
    A = _check(app_id)
    title = A.get(app_id)["app"].get("name", app_id)

    def work(pct):
        def prog(p, msg):
            pct(p)
            if msg:
                eng.log(f"{title}: {msg}")
        try:
            r = A.install(app_id, prog)
        except A.AppsError as e:
            raise RuntimeError(str(e)) from None
        eng.log(r["message"])
        if not r.get("ok") and not r.get("skipped"):
            raise RuntimeError(r["message"])
    return eng.run_job("apps_install:" + app_id, f"{title} kurulumu", work, wait)


def set_autostart(app_id: str, mode: str) -> dict:
    A = _check(app_id)
    try:
        return A.set_autostart(app_id, str(mode))
    except A.AppsError as e:
        raise ValueError(str(e)) from None


def start(app_id: str) -> dict:
    A = _check(app_id)
    try:
        return A.start(app_id)
    except A.AppsError as e:
        raise ValueError(str(e)) from None
