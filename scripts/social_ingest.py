#!/usr/bin/env python3
"""Build a reviewed social-content feed from approved public URLs.

This importer intentionally does not log in, reuse cookies, solve CAPTCHAs, or
call undocumented endpoints. Metadata refresh is limited to configured public
URLs and only runs when robots.txt permits this user agent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_INPUT = DATA_DIR / "social_sources.json"
DEFAULT_OUTPUT = DATA_DIR / "social_feed.json"
DEFAULT_CANDIDATES = DATA_DIR / "social_candidates.json"
USER_AGENT = "WuhanFamilyGuide/1.0 (+public-metadata-only)"
LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")
ALLOWED_HOSTS = {
    "xiaohongshu.com",
    "www.xiaohongshu.com",
    "douyin.com",
    "www.douyin.com",
    "jingxuan.douyin.com",
    "weibo.com",
    "www.weibo.com",
    "bilibili.com",
    "www.bilibili.com",
    "b23.tv",
    "news.cjn.cn",
    "news.hbtv.com.cn",
    "www.cnhubei.com",
    "cnhubei.com",
    "wuhan.gov.cn",
    "www.wuhan.gov.cn",
    "wlj.wuhan.gov.cn",
}


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.metadata: dict[str, str] = {}
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag != "meta":
            return
        key = values.get("property") or values.get("name")
        content = values.get("content")
        if key and content:
            self.metadata[key.lower()] = content

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join(self._title_parts).strip()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clean_text(value: object, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit].rstrip()


def allowed_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(
        hostname == allowed or hostname.endswith("." + allowed)
        for allowed in ALLOWED_HOSTS
    )


def robots_allows(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser(robots_url)
    try:
        parser.read()
    except Exception:
        return False
    return parser.can_fetch(USER_AGENT, url)


def fetch_metadata(url: str, timeout: int = 12) -> dict[str, str]:
    if not allowed_url(url) or not robots_allows(url):
        return {}
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return {}
        html = response.read(512_000).decode("utf-8", errors="replace")
    parser = MetadataParser()
    parser.feed(html)
    meta = parser.metadata
    return {
        "title": meta.get("og:title") or meta.get("twitter:title") or parser.title,
        "summary": meta.get("og:description") or meta.get("description") or "",
        "image": meta.get("og:image") or "",
    }


def normalize_item(raw: dict, refreshed: dict[str, str], now: str) -> dict:
    url = clean_text(raw.get("url"), 500)
    stable_id = raw.get("id") or hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    title = raw.get("title") or refreshed.get("title")
    summary = raw.get("summary") or refreshed.get("summary")
    item = {
        "id": clean_text(stable_id, 80),
        "platform": clean_text(raw.get("platform"), 32).lower(),
        "source_type": clean_text(raw.get("source_type", "public_page"), 40),
        "title": clean_text(title, 90),
        "summary": clean_text(summary, 150),
        "author": clean_text(raw.get("author"), 60),
        "url": url,
        "published_at": clean_text(raw.get("published_at"), 32),
        "place_name": clean_text(raw.get("place_name"), 80),
        "district": clean_text(raw.get("district"), 40),
        "tags": [clean_text(tag, 24) for tag in raw.get("tags", [])[:6]],
        "image": clean_text(raw.get("image") or refreshed.get("image"), 500),
        "review_status": clean_text(raw.get("review_status", "reviewed"), 24),
        "collected_at": clean_text(raw.get("collected_at") or now, 32),
    }
    for key, limit in (
        ("media_type", 24),
        ("connector", 60),
        ("discovery_query", 120),
        ("image_source", 40),
        ("verified_at", 32),
    ):
        value = clean_text(raw.get(key), limit)
        if value:
            item[key] = value
    if isinstance(raw.get("engagement"), dict):
        item["engagement"] = {
            clean_text(key, 24): clean_text(value, 24)
            for key, value in raw["engagement"].items()
            if value not in (None, "")
        }
    return item


def build_feed(
    input_path: Path = DEFAULT_INPUT,
    output_path: Path = DEFAULT_OUTPUT,
    refresh_metadata: bool = False,
    candidates_path: Path = DEFAULT_CANDIDATES,
) -> dict:
    config = load_json(input_path)
    now = datetime.now(LOCAL_TIMEZONE).isoformat(timespec="seconds")
    seen_urls: set[str] = set()
    items: list[dict] = []
    candidates: dict = {}

    for raw in config.get("items", []):
        url = clean_text(raw.get("url"), 500)
        if not allowed_url(url) or url in seen_urls:
            continue
        seen_urls.add(url)
        refreshed: dict[str, str] = {}
        if refresh_metadata:
            try:
                refreshed = fetch_metadata(url)
            except Exception as error:
                print(f"  metadata skipped: {url} ({error})")
            time.sleep(1.2)
        item = normalize_item(raw, refreshed, now)
        if item["title"] and item["summary"]:
            items.append(item)

    if candidates_path.exists():
        candidates = load_json(candidates_path)
        for raw in candidates.get("items", []):
            if raw.get("review_status") not in {"reviewed", "auto_trusted"}:
                continue
            url = clean_text(raw.get("url"), 500)
            if not allowed_url(url) or url in seen_urls:
                continue
            seen_urls.add(url)
            item = normalize_item(raw, {}, now)
            if item["title"] and item["summary"]:
                items.append(item)

    items.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    latest_published_at = items[0].get("published_at", "") if items else ""
    platforms = list(config.get("platforms", []))
    if any(item.get("platform") == "local_news" for item in items):
        platforms.insert(
            0,
            {
                "id": "local_news",
                "label": "实时资讯",
                "mode": "trusted_public_news_rss",
                "status": "auto_refreshing",
            },
        )
    platforms = list({platform["id"]: platform for platform in platforms}.values())
    pending_count = sum(
        item.get("review_status") == "pending"
        for item in candidates.get("items", [])
    )
    source_health = {
        "status": "degraded" if candidates.get("errors") else "healthy",
        "last_discovery_at": candidates.get("generated_at", ""),
        "automatic_sources": candidates.get("source_status", {}),
        "connectors": candidates.get("connectors", {}),
        "pending_review": pending_count,
        "errors": candidates.get("errors", []),
    }
    feed = {
        "generated_at": now,
        "latest_published_at": latest_published_at,
        "freshness": {
            "live_window_days": 7,
            "current_window_days": 30,
            "stale_after_days": 30,
        },
        "source_health": source_health,
        "policy": config.get("policy", {}),
        "platforms": platforms,
        "items": items,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(feed, handle, ensure_ascii=False, indent=2)
    print(f"  social_feed.json saved ({len(items)} reviewed items)")
    return feed


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the reviewed social-content feed")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument(
        "--refresh-metadata",
        action="store_true",
        help="Refresh OpenGraph metadata only when robots.txt allows it",
    )
    args = parser.parse_args()
    build_feed(args.input, args.output, args.refresh_metadata, args.candidates)


if __name__ == "__main__":
    main()
