"""Normalize public social URLs into mobile-friendly direct links."""

from __future__ import annotations

import re
import urllib.parse


XIAOHONGSHU_NOTE_PATH = re.compile(
    r"^/(?:search_result|explore|discovery/item)/([^/?#]+)"
)


def normalize_public_url(value: object) -> str:
    url = str(value or "").strip()
    if url.startswith("http://"):
        url = "https://" + url[7:]
    if not url.startswith("https://"):
        return ""

    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host not in {"xiaohongshu.com", "www.xiaohongshu.com"}:
        return url

    match = XIAOHONGSHU_NOTE_PATH.match(parsed.path)
    if not match:
        return url
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    token = query.get("xsec_token", "").strip()
    if not token:
        return ""

    note_id = urllib.parse.quote(urllib.parse.unquote(match.group(1)), safe="")
    direct_query = urllib.parse.urlencode(
        {
            "xsec_token": token,
            "xsec_source": query.get("xsec_source") or "pc_search",
        }
    )
    return urllib.parse.urlunsplit(
        (
            "https",
            "www.xiaohongshu.com",
            f"/discovery/item/{note_id}",
            direct_query,
            "",
        )
    )


def is_direct_social_url(url: str, platform: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/")
    platform = str(platform or "").lower()

    if platform == "xiaohongshu":
        query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
        return (
            host in {"xiaohongshu.com", "www.xiaohongshu.com"}
            and path.startswith("/discovery/item/")
            and bool(query.get("xsec_token"))
        )
    if platform == "douyin":
        return host in {"douyin.com", "www.douyin.com"} and path.startswith(
            "/video/"
        )
    return True
