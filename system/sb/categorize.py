"""Kural tabanlı mail kategorileme (config/mail_rules.yaml)."""
from __future__ import annotations

import json
import re
from functools import lru_cache

import yaml

from .config import SYSTEM


RULES_FILE = SYSTEM / "config" / "mail_rules.yaml"


@lru_cache(maxsize=1)
def rules() -> tuple[list[dict], str]:
    path = RULES_FILE if RULES_FILE.exists() else SYSTEM / "config" / "mail_rules.example.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    compiled = []
    for c in data["categories"]:
        rule = dict(c)
        for k in ("subject", "any"):
            if k in rule:
                rule[k] = re.compile(rule[k], re.I)
        compiled.append(rule)
    return compiled, data.get("default", "diger")


def _domain_match(addr: str, domains: list[str]) -> bool:
    host = addr.rsplit("@", 1)[-1].lower().strip("> ")
    return any(host == d or host.endswith("." + d) for d in domains)


def categorize(msg: dict) -> str:
    cats, default = rules()
    labels = msg.get("labels") or []
    if isinstance(labels, str):
        labels = json.loads(labels)
    sender = (msg.get("from_addr") or "").lower()
    sender_full = f"{msg.get('from_name') or ''} {sender}".lower()
    recipients = [a.strip() for a in f"{msg.get('to_addrs') or ''},{msg.get('cc_addrs') or ''}".split(",") if a.strip()]
    subject = msg.get("subject") or ""
    is_sms = "SMS" in labels
    sms_sender = re.sub(r"[\s.\-]", "", f"{msg.get('from_name') or ''}{sender}").lower()
    text = f"{subject}\n{(msg.get('body') or '')[:5000]}"
    for c in cats:
        if "not_from_domain" in c and sender and _domain_match(sender, c["not_from_domain"]):
            continue
        if "label" in c and any(l in labels for l in c["label"]):
            return c["name"]
        if "from_domain" in c and sender and _domain_match(sender, c["from_domain"]):
            return c["name"]
        if is_sms and "sms_from" in c and any(re.sub(r"[\s.\-]", "", s.lower()) in sms_sender for s in c["sms_from"]):
            return c["name"]
        if "from" in c and any(s.lower() in sender_full for s in c["from"]):
            return c["name"]
        if "to_domain" in c and any(_domain_match(r, c["to_domain"]) for r in recipients):
            return c["name"]
        if "subject" in c and c["subject"].search(subject):
            return c["name"]
        if "any" in c and c["any"].search(text):
            return c["name"]
    if is_sms and (msg.get("from_name") or "").strip():  # rehberdeki biri → kişisel
        return "kisisel"
    return default
