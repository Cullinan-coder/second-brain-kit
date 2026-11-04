"""Saat dilimi yardımcıları: liste, sistem varsayılanı ve serbest girdiyi ("Gmt+3", "Türkiye", "+03:00") IANA kimliğine çevirme."""
from __future__ import annotations

import re
import time
import unicodedata
from datetime import datetime, timedelta

COMMON = ["Europe/Istanbul", "Europe/London", "Europe/Berlin", "Europe/Paris", "Europe/Moscow", "Asia/Dubai", "Asia/Kolkata", "Asia/Tokyo",
          "Asia/Shanghai", "Australia/Sydney", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
          "America/Sao_Paulo", "Africa/Cairo", "UTC"]
# tzdata yoksa (bazı Windows kurulumları) yedek liste: yaygın kimlikler + Etc/GMT±N
FALLBACK = sorted(set(COMMON) | {f"Etc/GMT{s}{n}" for s in "+-" for n in range(1, 13)} | {"Etc/UTC", "Etc/GMT"})
ALIASES = {  # katlanmış (ascii, küçük harf) ad -> IANA
    "turkiye": "Europe/Istanbul", "turkey": "Europe/Istanbul", "istanbul": "Europe/Istanbul", "ankara": "Europe/Istanbul",
    "izmir": "Europe/Istanbul", "tr": "Europe/Istanbul", "trt": "Europe/Istanbul",
    "almanya": "Europe/Berlin", "germany": "Europe/Berlin", "berlin": "Europe/Berlin",
    "ingiltere": "Europe/London", "birlesik krallik": "Europe/London", "uk": "Europe/London", "england": "Europe/London", "londra": "Europe/London",
    "fransa": "Europe/Paris", "france": "Europe/Paris", "paris": "Europe/Paris",
    "italya": "Europe/Rome", "italy": "Europe/Rome", "roma": "Europe/Rome",
    "ispanya": "Europe/Madrid", "spain": "Europe/Madrid", "madrid": "Europe/Madrid",
    "hollanda": "Europe/Amsterdam", "netherlands": "Europe/Amsterdam",
    "rusya": "Europe/Moscow", "russia": "Europe/Moscow", "moskova": "Europe/Moscow",
    "azerbaycan": "Asia/Baku", "baku": "Asia/Baku", "dubai": "Asia/Dubai", "bae": "Asia/Dubai",
    "japonya": "Asia/Tokyo", "japan": "Asia/Tokyo", "cin": "Asia/Shanghai", "china": "Asia/Shanghai",
    "hindistan": "Asia/Kolkata", "india": "Asia/Kolkata", "avustralya": "Australia/Sydney", "australia": "Australia/Sydney",
    "abd": "America/New_York", "usa": "America/New_York", "us": "America/New_York", "new york": "America/New_York",
    "los angeles": "America/Los_Angeles", "kanada": "America/Toronto", "canada": "America/Toronto",
    "brezilya": "America/Sao_Paulo", "brazil": "America/Sao_Paulo", "misir": "Africa/Cairo", "egypt": "Africa/Cairo",
    "utc": "Etc/UTC", "gmt": "Etc/GMT", "z": "Etc/UTC",
}
HALF = {  # tam saat olmayan ofsetler (dakika)
    330: "Asia/Kolkata", 345: "Asia/Kathmandu", 210: "Asia/Tehran", 270: "Asia/Kabul", 570: "Australia/Darwin", -210: "America/St_Johns",
}
_OFFSET = re.compile(r"^(?:gmt|utc)?\s*([+-])\s*(\d{1,2})(?::?(\d{2}))?$")


def fold(s: str) -> str:
    """Türkçe harfleri ascii'ye indir, küçült, boşlukları sadeleştir."""
    s = str(s or "").replace("İ", "i").replace("I", "i").replace("ı", "i")
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[\s_]+", " ", s).strip()


def available() -> list[str]:
    try:
        from zoneinfo import available_timezones
        z = sorted(x for x in available_timezones() if not x.startswith(("posix/", "right/", "SystemV/")) and x != "localtime")
    except Exception:                                         # noqa: BLE001
        z = []
    return z or list(FALLBACK)


def _valid(tz: str) -> bool:
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(tz)
        return True
    except Exception:                                         # noqa: BLE001
        return tz in FALLBACK


def _local_offset_min() -> int:
    t = time.localtime()
    secs = -(time.altzone if t.tm_isdst > 0 and time.daylight else time.timezone)
    return int(secs // 60)


def _etc(minutes: int) -> str:
    h = minutes // 60
    return "Etc/UTC" if h == 0 else f"Etc/GMT{'-' if h > 0 else '+'}{abs(h)}"


def system_default() -> str:
    """Sistemin saat dilimi. Yerel UTC ofseti +3 ise Europe/Istanbul (Windows'ta ad IANA olmadığı için)."""
    off = _local_offset_min()
    try:
        from tzlocal import get_localzone_name             # varsa en doğrusu
        n = get_localzone_name()
        if n and _valid(n) and "/" in n:
            return n
    except Exception:                                         # noqa: BLE001
        pass
    if off == 180:
        return "Europe/Istanbul"
    try:
        key = getattr(datetime.now().astimezone().tzinfo, "key", "")
        if key and _valid(key):
            return key
    except Exception:                                         # noqa: BLE001
        pass
    if off in HALF:
        return HALF[off]
    return _etc(off) if off % 60 == 0 else "Europe/Istanbul"


def _utc_label(tz: str) -> str:
    try:
        from zoneinfo import ZoneInfo
        off = datetime.now(ZoneInfo(tz)).utcoffset() or timedelta(0)
    except Exception:                                         # noqa: BLE001
        return tz
    m = int(off.total_seconds() // 60)
    sign = "+" if m >= 0 else "-"
    return f"{tz} (UTC{sign}{abs(m) // 60:02d}:{abs(m) % 60:02d})"


def prefer_istanbul() -> bool:
    """Türkiye yerel ayarı (ya da sistem saat dilimi Europe/Istanbul) ise UTC+3 girdileri Etc/GMT-3 yerine Europe/Istanbul olur (aynı ofset)."""
    try:
        import locale
        lang = (locale.getlocale()[0] or "").lower()
        if lang.startswith(("tr", "turkish")):
            return True
    except Exception:                                         # noqa: BLE001
        pass
    return system_default() == "Europe/Istanbul"


def listing() -> dict:
    ids = available()
    default = system_default()
    if default not in ids:
        ids.append(default)
    first = [x for x in COMMON if x in ids]
    rest = [x for x in ids if x not in first]
    return {"default": default, "list": [{"id": x, "label": _utc_label(x)} for x in first + rest]}


def normalize(raw, default: str | None = None) -> str:
    """Girdiyi geçerli IANA kimliğine çevirir; boşsa varsayılan; anlaşılamazsa ValueError."""
    s = str(raw or "").strip()
    if not s or fold(s) in ("varsayilan", "default", "otomatik", "auto"):
        return default or system_default()
    ids = available()
    if s in ids and _valid(s):
        return s
    low = {x.lower(): x for x in ids}
    if s.lower() in low:
        return low[s.lower()]
    f = fold(s)
    m = _OFFSET.match(f.replace(" ", "")) or _OFFSET.match(f)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        hh, mm = int(m.group(2)), int(m.group(3) or 0)
        if hh > 14 or mm > 59:
            raise ValueError(f"geçersiz saat dilimi: {s}")
        total = sign * (hh * 60 + mm)
        if total == 180 and prefer_istanbul():
            return "Europe/Istanbul"
        if mm == 0:
            out = _etc(total)
            if _valid(out):
                return out
        elif total in HALF and _valid(HALF[total]):
            return HALF[total]
        raise ValueError(f"bu UTC ofseti için kimlik bulunamadı: {s} (listeden seç)")
    if f in ALIASES and _valid(ALIASES[f]):
        return ALIASES[f]
    if f in ("gmt", "utc"):
        return "Etc/UTC"
    hits = [x for x in ids if fold(x.rsplit("/", 1)[-1]) == f or fold(x) == f]
    if len(hits) == 1:
        return hits[0]
    raise ValueError(f"geçersiz saat dilimi: {s} (örnek: Europe/Istanbul, GMT+3, Türkiye)")
