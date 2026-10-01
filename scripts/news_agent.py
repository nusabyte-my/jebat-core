#!/usr/bin/env python3
"""JEBAT news agent — fetch the latest AI/agent-infrastructure news.

Sources: official engineering blogs + release feeds (Anthropic, OpenAI,
Hugging Face, Simon Willison, LangChain). RSS/Atom only — deterministic,
no scraping fragility, no invented content.

Output: ~/.jebat/news.json (also prints JSON to stdout)
Schema: {"generated_at": iso, "items": [{title, link, source, date, summary}]}

Usage:
    python scripts/news_agent.py               # fetch + write + print
    python scripts/news_agent.py --limit 3     # trim to N items
    python scripts/news_agent.py --refresh-ttl 900
"""
from __future__ import annotations

import argparse
import email.utils
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

FEEDS: List[Dict[str, str]] = [
    {"name": "Anthropic", "url": "https://rsshub.app/anthropic/news"},
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/"},
    {"name": "LangChain", "url": "https://blog.langchain.dev/rss/"},
]

OUT_PATH = Path.home() / ".jebat" / "news.json"
KEYWORDS = re.compile(
    r"\b(agent|agenti[cz]|llm|mcp|model context protocol|inference|rag|"
    r"fine[- ]?tun|embedding|token|transformer|on[- ]?device|local model|"
    r"sdk|tool use|function call|artificial intelligence|\bai\b|gpt|claude|"
    r"gemini|open[- ]?source model|distillation|benchmark|reasoning|"
    r"context window|quantiz|gpu|tpu)\b",
    re.IGNORECASE,
)
TAG = re.compile(r"<[^>]+>")


def _fetch(url: str, timeout: float = 10.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEBAT-NewsAgent/8.3 (+https://jebat.online)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _clean(text: str) -> str:
    text = TAG.sub("", text or "")
    return " ".join(text.split())[:220]


def _parse_ts(raw: str) -> float:
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return email.utils.mktime_tz(email.utils.parsedate_tz(raw)) if "GMT" in raw.upper() or "-" in raw[26:] else time.mktime(time.strptime(raw, fmt))
        except Exception:
            continue
    try:
        return time.mktime(time.strptime(raw.strip(), "%Y-%m-%dT%H:%M:%S%z"))
    except Exception:
        return 0.0


def collect(per_feed: int = 6) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for feed in FEEDS:
        try:
            raw = _fetch(feed["url"])
        except Exception as exc:
            print(f"  ! {feed['name']}: {exc}", file=sys.stderr)
            continue
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            continue
        entries = root.findall(".//item") or root.findall(".//{*}entry")
        for entry in entries[:per_feed]:
            title = (entry.findtext("title") or entry.findtext("{*}title") or "").strip()
            link = (entry.findtext("link") or entry.findtext("{*}link") or "").strip()
            if not link and entry.find("{*}link") is not None:
                link = entry.find("{*}link").get("href", "")
            date_raw = entry.findtext("pubDate") or entry.findtext("{*}updated") or entry.findtext("{*}published") or ""
            summary = _clean(entry.findtext("description") or entry.findtext("{*}summary") or entry.findtext("{*}content") or "")
            if not title or not link:
                continue
            items.append({
                "title": _clean(title),
                "link": link,
                "source": feed["name"],
                "date": date_raw,
                "ts": _parse_ts(date_raw),
                "summary": summary,
                "ai_relevant": bool(KEYWORDS.search(title + " " + summary)),
            })
    # AI/agent-relevant first, then newest
    items.sort(key=lambda x: (not x["ai_relevant"], -x["ts"]))
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch latest AI news into news.json")
    ap.add_argument("--limit", type=int, default=6, help="max items to keep (default 6)")
    ap.add_argument("--refresh-ttl", type=int, default=0, help="seconds; if news.json is fresher, skip fetch")
    ap.add_argument("--out", default=str(OUT_PATH), help="output path")
    args = ap.parse_args()

    out = Path(args.out).expanduser()
    if args.refresh_ttl and out.exists():
        age = time.time() - out.stat().st_mtime
        if age < args.refresh_ttl:
            print(out.read_text(encoding="utf-8"))
            return 0

    items = collect()
    for it in items:
        it.pop("ai_relevant", None)
        it.pop("ts", None)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "count": len(items[:args.limit]),
        "items": items[:args.limit],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
