#!/usr/bin/env python3
"""Discover public travel-info candidates through SearXNG and RSSHub.

The output is deliberately review-only. It never modifies social_feed.json.
Configure private/self-hosted instances with SEARXNG_BASE_URL and
RSSHUB_BASE_URL; no public instance is hardcoded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
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
    if not searxng_url and not rsshub_configured and output_path.exists():
        print("  no discovery endpoint configured; existing candidates kept unchanged")
        return load_json(output_path)

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

    unique = {item["url"]: item for item in candidates}
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "publish_requires_review": True,
        "configured": {
            "searxng": bool(searxng_url),
            "rsshub": rsshub_configured,
        },
        "errors": errors,
        "items": list(unique.values()),
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  social_candidates.json saved ({len(unique)} pending items)")
    if not searxng_url and not rsshub_url:
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
