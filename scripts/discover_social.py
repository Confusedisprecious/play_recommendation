#!/usr/bin/env python3
"""Discover public travel-info candidates through SearXNG and RSSHub.

The output is deliberately review-only. It never modifies social_feed.json.
Configure private/self-hosted instances with SEARXNG_BASE_URL and
RSSHUB_BASE_URL; no public instance is hardcoded.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = BASE_DIR / "data" / "source_registry.json"
OUTPUT_PATH = BASE_DIR / "data" / "social_candidates.json"
USER_AGENT = "WuhanFamilyGuide/1.0 (+review-only-public-discovery)"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def fetch_xml(url: str) -> ET.Element:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml,application/atom+xml"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return ET.fromstring(response.read())


def allowed_host(url: str, allowed_domains: list[str]) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(host == domain or host.endswith("." + domain) for domain in allowed_domains)


def platform_for(url: str) -> str:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    for platform in ("xiaohongshu", "douyin", "weibo", "bilibili"):
        if platform in host:
            return platform
    return "web"


def candidate_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def discover_searxng(config: dict, base_url: str) -> list[dict]:
    allowed_domains = config.get("allowed_domains", [])
    candidates = []
    for query in config.get("queries", []):
        params = urllib.parse.urlencode(
            {"q": query, "format": "json", "language": "zh-CN", "safesearch": 1}
        )
        payload = fetch_json(base_url.rstrip("/") + "/search?" + params)
        for result in payload.get("results", [])[:12]:
            url = str(result.get("url", "")).strip()
            if not url.startswith("https://") or not allowed_host(url, allowed_domains):
                continue
            candidates.append(
                {
                    "id": candidate_id(url),
                    "platform": platform_for(url),
                    "source_type": "searxng_public_result",
                    "title": str(result.get("title", "")).strip()[:120],
                    "summary": str(result.get("content", "")).strip()[:240],
                    "url": url,
                    "discovery_query": query,
                    "review_status": "pending",
                }
            )
    return candidates


def child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in node.iter():
        local_name = child.tag.rsplit("}", 1)[-1]
        if local_name in names and child.text:
            return child.text.strip()
    return ""


def clean_text(value: str, limit: int = 240) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:limit].rstrip()


def unwrap_news_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname in {"bing.com", "www.bing.com"}:
        target = urllib.parse.parse_qs(parsed.query).get("url", [""])[0]
        if target:
            url = urllib.parse.unquote(target)
            parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")
        url = urllib.parse.urlunparse(parsed)
    return url


def infer_district(text: str) -> str:
    districts = (
        "武昌区", "江岸区", "江汉区", "硚口区", "汉阳区", "洪山区",
        "青山区", "东西湖区", "蔡甸区", "江夏区", "黄陂区", "新洲区",
    )
    return next((district for district in districts if district in text), "")


def discover_news_rss(config: dict) -> list[dict]:
    if not config.get("enabled", False):
        return []
    endpoint = config.get("endpoint", "https://www.bing.com/news/search")
    trusted_domains = config.get("auto_publish_domains", [])
    max_age_days = int(config.get("max_age_days", 45))
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    candidates = []

    for query in config.get("queries", []):
        params = urllib.parse.urlencode(
            {"q": query, "format": "rss", "setlang": "zh-cn"}
        )
        root = fetch_xml(endpoint + "?" + params)
        for item in list(root.iter("item"))[:20]:
            url = unwrap_news_url(child_text(item, ("link",)))
            if not url.startswith("https://") or not allowed_host(url, trusted_domains):
                continue
            published_raw = child_text(item, ("pubDate", "published", "updated"))
            try:
                published = parsedate_to_datetime(published_raw)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
            if published < cutoff:
                continue
            title = clean_text(child_text(item, ("title",)), 120)
            summary = clean_text(child_text(item, ("description", "summary")), 240)
            source = clean_text(child_text(item, ("Source", "source", "author")), 60)
            if not title or not summary:
                continue
            candidates.append(
                {
                    "id": candidate_id(url),
                    "platform": "local_news",
                    "source_type": "public_news_rss",
                    "title": title,
                    "summary": summary,
                    "author": source or (urllib.parse.urlparse(url).hostname or "公开新闻源"),
                    "url": url,
                    "published_at": published.astimezone(timezone.utc).date().isoformat(),
                    "place_name": "",
                    "district": infer_district(title + " " + summary),
                    "tags": ["实时资讯", "武汉文旅"],
                    "discovery_query": query,
                    "review_status": "auto_trusted",
                }
            )

    unique = {item["url"]: item for item in candidates}
    items = sorted(
        unique.values(),
        key=lambda item: item.get("published_at", ""),
        reverse=True,
    )
    return items[: int(config.get("max_items", 24))]


def discover_rsshub(config: dict, base_url: str) -> list[dict]:
    candidates = []
    for route in config.get("routes", []):
        root = fetch_xml(base_url.rstrip("/") + "/" + route.lstrip("/"))
        for item in list(root.iter("item"))[:20]:
            url = child_text(item, ("link",))
            if not url:
                continue
            candidates.append(
                {
                    "id": candidate_id(url),
                    "platform": platform_for(url),
                    "source_type": "rsshub_feed",
                    "title": child_text(item, ("title",))[:120],
                    "summary": child_text(item, ("description", "summary"))[:240],
                    "url": url,
                    "discovery_query": route,
                    "review_status": "pending",
                }
            )
    return candidates


def discover(registry_path: Path = REGISTRY_PATH, output_path: Path = OUTPUT_PATH) -> dict:
    registry = load_json(registry_path)
    candidates = []
    errors = []

    searxng_url = os.environ.get(registry["search"]["base_url_env"], "").strip()
    rsshub_url = os.environ.get(registry["feeds"]["base_url_env"], "").strip()
    rsshub_configured = bool(rsshub_url and registry["feeds"].get("routes"))
    news_configured = bool(registry.get("news_rss", {}).get("enabled"))
    if not searxng_url and not rsshub_configured and not news_configured and output_path.exists():
        print("  no discovery endpoint configured; existing candidates kept unchanged")
        return load_json(output_path)

    if news_configured:
        try:
            candidates.extend(discover_news_rss(registry["news_rss"]))
        except Exception as error:
            errors.append(f"News RSS: {error}")

    if searxng_url:
        try:
            candidates.extend(discover_searxng(registry["search"], searxng_url))
        except Exception as error:
            errors.append(f"SearXNG: {error}")

    if rsshub_configured:
        try:
            candidates.extend(discover_rsshub(registry["feeds"], rsshub_url))
        except Exception as error:
            errors.append(f"RSSHub: {error}")

    if output_path.exists():
        existing = load_json(output_path)
        max_age_days = int(registry.get("news_rss", {}).get("max_age_days", 45))
        cutoff_date = (
            datetime.now(timezone.utc) - timedelta(days=max_age_days)
        ).date().isoformat()
        candidates.extend(
            item
            for item in existing.get("items", [])
            if item.get("review_status") == "auto_trusted"
            and item.get("published_at", "") >= cutoff_date
        )

    unique = {item["url"]: item for item in candidates}
    ordered_items = sorted(
        unique.values(),
        key=lambda item: item.get("published_at", ""),
        reverse=True,
    )
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "publish_requires_review": True,
        "configured": {
            "searxng": bool(searxng_url),
            "rsshub": rsshub_configured,
            "news_rss": news_configured,
        },
        "errors": errors,
        "items": ordered_items,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    auto_trusted = sum(
        item.get("review_status") == "auto_trusted" for item in unique.values()
    )
    print(
        "  social_candidates.json saved "
        f"({auto_trusted} trusted, {len(unique) - auto_trusted} pending)"
    )
    if not searxng_url and not rsshub_url and not news_configured:
        print("  no discovery endpoint configured; set SEARXNG_BASE_URL or RSSHUB_BASE_URL")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover review-only social candidates")
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    discover(args.registry, args.output)


if __name__ == "__main__":
    main()
