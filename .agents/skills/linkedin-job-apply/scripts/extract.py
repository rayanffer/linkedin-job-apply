#!/usr/bin/env python3
"""Pull the recruiter address and the apply URL out of a LinkedIn post.

The skill used to make the model read the post and decide this. That is one slow reasoning
pass, and it is the one place a model invents an address. This does it in milliseconds, the
same way every time.

Input — stdin, either:

  * raw text (the post as pasted, or document.body.innerText), or
  * JSON: {"text": "...", "hrefs": ["https://...", "mailto:..."]}

Output — JSON on stdout:

  {"emails": ["..."], "apply_urls": ["..."], "rejected": {"emails": [...], "urls": [...]}}

    cat post.txt | python3 scripts/extract.py
    python3 scripts/extract.py < dump.json
"""
from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"')\]]+", re.I)
BARE_DOMAIN_RE = re.compile(r"\b((?:[a-z0-9\-]+\.)+[a-z]{2,}(?:/[^\s<>\"')\]]*)?)", re.I)

EMAIL_NOISE_RE = re.compile(
    r"(noreply|no-reply|donotreply|do-not-reply|example\.(com|org|net)|@linkedin\.com|"
    r"\.(png|jpe?g|gif|webp|svg)$)",
    re.I,
)

NOISE_HOST_RE = re.compile(
    r"(^|\.)(twitter|x|youtube|youtu\.be|instagram|facebook|medium|tiktok|threads|google|"
    r"bit\.ly|t\.co|wa\.me|whatsapp|telegram|discord|spotify|apple)\.",
    re.I,
)

ATS_RE = re.compile(
    r"(greenhouse|lever\.co|workday|myworkdayjobs|ashbyhq|smartrecruiters|recruitee|teamtailor|"
    r"bamboohr|jobvite|icims|taleo|workable|rippling|wellfound|instahyre|cutshort|darwinbox|"
    r"zohorecruit|keka|forms\.gle|docs\.google\.com/forms|typeform|jotform|airtable|notion\.site)",
    re.I,
)

APPLY_PATH_RE = re.compile(
    r"(apply|application|careers?|jobs?|hiring|vacanc|opening|form|register)", re.I
)

RANK = {"ats": 0, "apply": 1, "linkedin-job": 2, "shortlink": 3}


def clean_email(raw: str) -> str | None:
    email = str(raw).strip()
    email = re.sub(r"^mailto:", "", email, flags=re.I)
    email = re.split(r"[?;]", email)[0].strip().strip(".,;:")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email):
        return None
    if EMAIL_NOISE_RE.search(email):
        return None
    return email.lower()


def classify(url: str) -> tuple[str, str] | None:
    """Return (kind, url) for a link worth offering, else None."""
    candidate = url.strip().strip(".,;:)]}")
    if candidate.lower().startswith("mailto:"):
        return None
    if not re.match(r"^https?://", candidate, re.I):
        if candidate.lower().startswith("www.") or BARE_DOMAIN_RE.fullmatch(candidate):
            candidate = "https://" + candidate
        else:
            return None

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    path = (parsed.path or "").lower()
    full = candidate.lower()

    if host == "lnkd.in":
        return "shortlink", candidate
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        return ("linkedin-job", candidate) if path.startswith("/jobs/") else None
    if NOISE_HOST_RE.search(host + "."):
        return None
    if ATS_RE.search(host) or ATS_RE.search(full):
        return "ats", candidate
    if APPLY_PATH_RE.search(path) or APPLY_PATH_RE.search(parsed.query or ""):
        return "apply", candidate
    return None


def extract(text: str, hrefs: list[str]) -> dict:
    emails: list[str] = []
    rejected_emails: list[str] = []
    seen: set[str] = set()

    for match in EMAIL_RE.finditer(text or ""):
        email = clean_email(match.group(0))
        if email is None:
            rejected_emails.append(match.group(0))
        elif email not in seen:
            seen.add(email)
            emails.append(email)

    for href in hrefs or []:
        if not href.lower().startswith("mailto:"):
            continue
        email = clean_email(href)
        if email is None:
            rejected_emails.append(href)
        elif email not in seen:
            seen.add(email)
            emails.append(email)

    found: dict[str, tuple[str, str]] = {}
    rejected_urls: list[str] = []
    for raw in list(hrefs or []) + URL_RE.findall(text or "") + BARE_DOMAIN_RE.findall(text or ""):
        hit = classify(raw)
        if hit is None:
            continue
        kind, url = hit
        previous = found.get(url)
        if previous is None or RANK[kind] < RANK[previous[0]]:
            found[url] = (kind, url)

    ordered = sorted(found.values(), key=lambda item: RANK[item[0]])
    return {
        "emails": emails[:8],
        "apply_urls": [url for _kind, url in ordered][:3],
        "rejected": {"emails": rejected_emails[:8], "urls": rejected_urls},
    }


def main() -> int:
    raw = sys.stdin.read()

    payload: dict = {}
    stripped = raw.strip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = {}

    text = payload.get("text") or (raw if not payload else "")
    hrefs = payload.get("hrefs") or []

    if not text and not hrefs:
        print(json.dumps({"error": "no input on stdin"}, ensure_ascii=False))
        return 2

    print(json.dumps(extract(text, hrefs), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
