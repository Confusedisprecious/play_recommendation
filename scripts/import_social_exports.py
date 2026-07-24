#!/usr/bin/env python3
"""Normalize authorized local social exports into the review queue.

The importer accepts common JSON shapes emitted by xiaohongshu-mcp, redbook,
Agent-Reach, and MediaCrawler. Login credentials stay with those local tools;
only public post metadata is written to data/social_candidates.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BASE_DIR / "data" / "social_candidates.json"
LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")
PLATFORM_HOSTS = {
    "xiaohongshu": ("xiaohongshu.com",),
    "douyin": ("douyin.com",),
    "weibo": ("weibo.com",),
    "bilibili": ("bilibili.com", "b23.tv"),
}


def clean_text(value: Any, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit].rstrip()


def nested(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_value(raw: dict, paths: Iterable[tuple[str, ...]]) -> Any:
    for path in paths:
        value = nested(raw, *path)
        if value not in (None, "", [], {}):
            return value
    return None


def decode_embedded_json(payload: Any) -> Any:
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
        return payload
    for block in payload["content"]:
        text = block.get("text") if isinstance(block, dict) else None
        if not isinstance(text, str):
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    return payload


def find_records(payload: Any) -> list[dict]:
    payload = decode_embedded_json(payload)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("items", "feeds", "notes", "results", "list", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            records = find_records(value)
            if records:
                return records
    return [payload] if any(key in payload for key in ("url", "note_id", "id")) else []


def infer_platform(raw: dict, default: str, url: str) -> str:
    explicit = clean_text(
        first_value(raw, (("platform",), ("source_platform",), ("channel",))),
        32,
    ).lower()
    aliases = {
        "xhs": "xiaohongshu",
        "redbook": "xiaohongshu",
        "rednote": "xiaohongshu",
        "小红书": "xiaohongshu",
        "抖音": "douyin",
        "微博": "weibo",
        "哔哩哔哩": "bilibili",
        "b站": "bilibili",
    }
    explicit = aliases.get(explicit, explicit)
    if explicit in PLATFORM_HOSTS:
        return explicit
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    for platform, domains in PLATFORM_HOSTS.items():
        if any(host == domain or host.endswith("." + domain) for domain in domains):
            return platform
    return default


def normalize_timestamp(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)) or str(value).isdigit():
        number = float(value)
        if number > 10_000_000_000:
            number /= 1000
        try:
            return datetime.fromtimestamp(number, timezone.utc).astimezone(
                LOCAL_TIMEZONE
            ).isoformat(timespec="seconds")
        except (OverflowError, OSError, ValueError):
            return ""
    text = clean_text(value, 40)
    try:
        normalized = text.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).astimezone(
            LOCAL_TIMEZONE
        ).isoformat(timespec="seconds")
    except ValueError:
        return text


def extract_url(raw: dict, platform: str) -> str:
    url = clean_text(
        first_value(
            raw,
            (
                ("url",),
                ("note_url",),
                ("share_url",),
                ("web_url",),
                ("link",),
                ("note_card", "url"),
            ),
        ),
        600,
    )
    if url.startswith("http://"):
        url = "https://" + url[7:]
    if url.startswith("https://"):
        return url

    post_id = clean_text(
        first_value(
            raw,
            (
                ("note_id",),
                ("feed_id",),
                ("aweme_id",),
                ("bvid",),
                ("id",),
                ("note_card", "note_id"),
                ("note_card", "id"),
            ),
        ),
        100,
    )
    if not post_id:
        return ""
    if platform == "xiaohongshu":
        url = f"https://www.xiaohongshu.com/explore/{urllib.parse.quote(post_id)}"
        token = clean_text(raw.get("xsec_token"), 500)
        if token:
            url += "?" + urllib.parse.urlencode({"xsec_token": token})
        return url
    if platform == "douyin":
        return f"https://www.douyin.com/video/{urllib.parse.quote(post_id)}"
    if platform == "weibo":
        return f"https://weibo.com/detail/{urllib.parse.quote(post_id)}"
    if platform == "bilibili":
        return f"https://www.bilibili.com/video/{urllib.parse.quote(post_id)}"
    return ""


def extract_image(raw: dict) -> str:
    value = first_value(
        raw,
        (
            ("image",),
            ("cover", "url"),
            ("cover", "url_default"),
            ("cover",),
            ("note_card", "cover", "url"),
            ("note_card", "cover", "url_default"),
            ("video", "cover", "url"),
        ),
    )
    if isinstance(value, str) and value.startswith("http"):
        return clean_text(value, 800)
    image_list = first_value(
        raw,
        (("images",), ("image_list",), ("note_card", "image_list")),
    )
    if isinstance(image_list, list) and image_list:
        first = image_list[0]
        if isinstance(first, str):
            return clean_text(first, 800)
        if isinstance(first, dict):
            return clean_text(first.get("url") or first.get("url_default"), 800)
    return ""


def extract_author(raw: dict) -> str:
    value = first_value(
        raw,
        (
            ("author", "nickname"),
            ("author", "name"),
            ("author",),
            ("user", "nickname"),
            ("user", "name"),
            ("nickname",),
            ("note_card", "user", "nickname"),
        ),
    )
    return clean_text(value, 80)


def valid_public_url(url: str, platform: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    domains = PLATFORM_HOSTS.get(platform, ())
    return parsed.scheme == "https" and any(
        host == domain or host.endswith("." + domain) for domain in domains
    )


def normalize_record(
    raw: dict,
    default_platform: str,
    connector: str,
    review_status: str,
    collected_at: str,
) -> dict | None:
    card = raw.get("note_card") if isinstance(raw.get("note_card"), dict) else raw
    provisional_platform = infer_platform(raw, default_platform, "")
    url = extract_url(raw, provisional_platform)
    platform = infer_platform(raw, provisional_platform, url)
    if not valid_public_url(url, platform):
        return None

    title = clean_text(
        first_value(
            card,
            (
                ("display_title",),
                ("title",),
                ("name",),
                ("desc",),
                ("description",),
            ),
        ),
        120,
    )
    summary = clean_text(
        first_value(
            card,
            (("desc",), ("description",), ("summary",), ("content",), ("text",)),
        ),
        280,
    )
    if not title:
        return None

    published_at = normalize_timestamp(
        first_value(
            raw,
            (
                ("published_at",),
                ("publish_time",),
                ("create_time",),
                ("time",),
                ("note_card", "time"),
            ),
        )
    )
    media_type = clean_text(
        first_value(
            raw,
            (
                ("media_type",),
                ("type",),
                ("note_type",),
                ("note_card", "type"),
            ),
        ),
        24,
    ).lower()
    if any(token in media_type for token in ("video", "视频")):
        media_type = "video"
    elif media_type:
        media_type = "image"

    engagement = {
        "likes": first_value(
            raw,
            (("liked_count",), ("like_count",), ("interact_info", "liked_count")),
        ),
        "comments": first_value(
            raw,
            (("comment_count",), ("comments_count",), ("interact_info", "comment_count")),
        ),
        "collects": first_value(
            raw,
            (("collected_count",), ("collect_count",), ("interact_info", "collected_count")),
        ),
    }
    engagement = {
        key: clean_text(value, 20)
        for key, value in engagement.items()
        if value not in (None, "")
    }
    stable_id = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return {
        "id": stable_id,
        "platform": platform,
        "source_type": "authorized_local_export",
        "connector": connector,
        "title": title,
        "summary": summary,
        "author": extract_author(raw),
        "url": url,
        "published_at": published_at,
        "place_name": clean_text(raw.get("place_name"), 80),
        "district": clean_text(raw.get("district"), 40),
        "tags": [
            clean_text(tag.get("name") if isinstance(tag, dict) else tag, 24)
            for tag in (raw.get("tags") or raw.get("tag_list") or [])[:6]
        ],
        "image": extract_image(raw),
        "media_type": media_type,
        "engagement": engagement,
        "review_status": review_status,
        "collected_at": collected_at,
    }


def import_exports(
    input_paths: list[Path],
    output_path: Path = DEFAULT_OUTPUT,
    platform: str = "xiaohongshu",
    connector: str = "authorized-local-export",
    review_status: str = "pending",
) -> dict:
    now = datetime.now(LOCAL_TIMEZONE).isoformat(timespec="seconds")
    existing = (
        json.loads(output_path.read_text(encoding="utf-8"))
        if output_path.exists()
        else {"items": []}
    )
    imported = []
    for input_path in input_paths:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        for raw in find_records(payload):
            item = normalize_record(raw, platform, connector, review_status, now)
            if item:
                imported.append(item)

    merged = {item.get("url"): item for item in existing.get("items", []) if item.get("url")}
    for item in imported:
        previous = merged.get(item["url"], {})
        if previous.get("review_status") in {"reviewed", "auto_trusted"}:
            item["review_status"] = previous["review_status"]
        merged[item["url"]] = {**previous, **item}

    connectors = dict(existing.get("connectors", {}))
    platform_counts: dict[str, int] = {}
    for item in imported:
        platform_counts[item["platform"]] = platform_counts.get(item["platform"], 0) + 1
    for connector_platform, count in platform_counts.items():
        connectors[connector_platform] = {
            "adapter": connector,
            "status": "connected",
            "last_success_at": now,
            "imported_items": count,
            "publish_requires_review": True,
            "credential_scope": "local_only",
        }

    existing["generated_at"] = now
    existing["publish_requires_review"] = True
    existing["connectors"] = connectors
    existing["items"] = sorted(
        merged.values(),
        key=lambda item: item.get("published_at", ""),
        reverse=True,
    )
    output_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"  imported {len(imported)} social candidates "
        f"({sum(item['review_status'] == 'pending' for item in imported)} pending review)"
    )
    return existing


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import authorized local social-media JSON into the review queue"
    )
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--platform",
        choices=tuple(PLATFORM_HOSTS),
        default="xiaohongshu",
    )
    parser.add_argument(
        "--connector",
        default="authorized-local-export",
        help="Adapter name, for example xiaohongshu-mcp, redbook, or Agent-Reach",
    )
    parser.add_argument(
        "--review-status",
        choices=("pending", "reviewed"),
        default="pending",
        help="Use reviewed only after a human has checked every imported result",
    )
    args = parser.parse_args()
    import_exports(
        args.inputs,
        args.output,
        args.platform,
        args.connector,
        args.review_status,
    )


if __name__ == "__main__":
    main()
