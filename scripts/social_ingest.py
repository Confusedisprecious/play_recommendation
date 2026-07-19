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


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_INPUT = DATA_DIR / "social_sources.json"
DEFAULT_OUTPUT = DATA_DIR / "social_feed.json"
USER_AGENT = "WuhanFamilyGuide/1.0 (+public-metadata-only)"
ALLOWED_HOSTS = {
    "xiaohongshu.com",
    "www.xiaohongshu.com",
    "douyin.com",
    "www.douyin.com",
    "jingxuan.douyin.com",
    "weibo.com",
    "www.weibo.com",
    "news.cjn.cn",
    "news.hbtv.com.cn",
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
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


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
    return {
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


def build_feed(
    input_path: Path = DEFAULT_INPUT,
    output_path: Path = DEFAULT_OUTPUT,
    refresh_metadata: bool = False,
) -> dict:
    config = load_json(input_path)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    seen_urls: set[str] = set()
    items: list[dict] = []

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

    items.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    feed = {
        "generated_at": now,
        "policy": config.get("policy", {}),
        "platforms": config.get("platforms", []),
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
    parser.add_argument(
        "--refresh-metadata",
        action="store_true",
        help="Refresh OpenGraph metadata only when robots.txt allows it",
    )
    args = parser.parse_args()
    build_feed(args.input, args.output, args.refresh_metadata)


if __name__ == "__main__":
    main()
