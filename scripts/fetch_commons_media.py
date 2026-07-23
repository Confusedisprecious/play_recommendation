#!/usr/bin/env python3
"""Download curated, openly licensed Wuhan photos from Wikimedia Commons."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "images" / "media"
OUTPUT_PATH = BASE_DIR / "data" / "media_gallery.json"
API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "WuhanFamilyGuide/1.0 "
    "(https://github.com/confusedisprecious/play_recommendation)"
)

CURATED_MEDIA = [
    {
        "slug": "yellow-crane-tower",
        "title": "File:CN - Hubei - Wuhan - Kranichpagode.jpg",
        "name": "黄鹤楼",
        "place_id": 48,
        "district": "武昌区",
        "kind": "photo",
        "caption": "登楼看长江与武汉三镇，适合安排半日经典线路。",
    },
    {
        "slug": "east-lake",
        "title": "File:Mount Mo and East Lake, Wuhan.jpg",
        "name": "东湖",
        "place_id": 44,
        "district": "武昌区",
        "kind": "photo",
        "caption": "湖岸、绿道与磨山串成适合亲子骑行的一日路线。",
    },
    {
        "slug": "wuhan-zoo",
        "title": "File:WUHAN ZOO.jpg",
        "name": "武汉动物园",
        "place_id": 19,
        "district": "汉阳区",
        "kind": "photo",
        "caption": "动物观察与步行游园结合，低龄家庭也容易安排。",
    },
    {
        "slug": "wuhan-botanical-garden",
        "title": "File:Wuhan Botanical Garden.jpg",
        "name": "武汉植物园",
        "place_id": 44,
        "district": "武昌区",
        "kind": "photo",
        "caption": "季节花卉和自然科普兼具，适合研学型亲子出行。",
    },
    {
        "slug": "hubei-museum",
        "title": "File:Hubei Provincial Museum.JPG",
        "name": "湖北省博物馆",
        "place_id": 43,
        "district": "武昌区",
        "kind": "photo",
        "caption": "编钟与楚文化是武汉经典室内文化体验。",
    },
    {
        "slug": "yangtze-river-bridge",
        "title": "File:Wuhan Yangtze River Bridge in 2020.jpg",
        "name": "武汉长江大桥",
        "place_id": 48,
        "district": "武昌区",
        "kind": "photo",
        "caption": "可与黄鹤楼、户部巷组合成城市地标路线。",
    },
    {
        "slug": "wuhan-skyline",
        "title": "File:Wuhan Skyline 01,黄鹤楼南路.jpg",
        "name": "江城天际线",
        "place_id": 23,
        "district": "江岸区",
        "kind": "photo",
        "caption": "江滩散步时可直观看到武汉两江四岸的城市景观。",
    },
    {
        "slug": "happy-valley",
        "title": "File:Happy Valley Wuhan 2.jpg",
        "name": "武汉欢乐谷",
        "place_id": 9,
        "district": "洪山区",
        "kind": "photo",
        "caption": "大型游乐设施集中，适合学龄儿童与青少年家庭。",
    },
]


def clean_markup(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def commons_page_url(title: str) -> str:
    name = title.removeprefix("File:").replace(" ", "_")
    return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(name)


def fetch_metadata(title: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": 1600,
            "format": "json",
            "formatversion": 2,
            "origin": "*",
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    pages = payload.get("query", {}).get("pages", [])
    if not pages or not pages[0].get("imageinfo"):
        raise RuntimeError(f"Commons file not found: {title}")
    return pages[0]["imageinfo"][0]


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def build_gallery() -> dict:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for entry in CURATED_MEDIA:
        info = fetch_metadata(entry["title"])
        metadata = info.get("extmetadata", {})
        image_url = info.get("thumburl") or info["url"]
        destination = MEDIA_DIR / f"{entry['slug']}.jpg"
        download(image_url, destination)
        item = {
            **entry,
            "image": destination.relative_to(BASE_DIR).as_posix(),
            "source_url": commons_page_url(entry["title"]),
            "author": clean_markup(metadata.get("Artist", {}).get("value", "")),
            "license": clean_markup(
                metadata.get("LicenseShortName", {}).get("value", "")
            ),
            "license_url": clean_markup(
                metadata.get("LicenseUrl", {}).get("value", "")
            ),
        }
        items.append(item)
        print(f"  saved {destination.name}")

    gallery = {
        "generated_from": "Wikimedia Commons",
        "usage_notice": "照片按各自开放许可使用，作者与许可见每张媒体记录。",
        "items": items,
    }
    OUTPUT_PATH.write_text(
        json.dumps(gallery, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  media_gallery.json saved ({len(items)} items)")
    return gallery


if __name__ == "__main__":
    build_gallery()
