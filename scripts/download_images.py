#!/usr/bin/env python3
"""
Download real images from Bing/Baidu for all spots and events.
Saves to images/{id}.jpg (spots) and images/e{id}.jpg (events).
"""
import json, os, re, time, random, sys
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {filename}")


def search_bing_images(query, max_retries=2):
    """Search Bing Images and return list of image thumbnail URLs."""
    url = "https://cn.bing.com/images/search?q=" + requests.utils.quote(query) + "&FORM=IRFLTR"
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.encoding = "utf-8"
            html = resp.text
            # Extract tseX-mm.cn.bing.net thumbnail URLs (real photos)
            urls = re.findall(r'https?://tse\d-mm\.cn\.bing\.net/th/id/OIP-[^\"?\\<>]+', html)
            # De-duplicate while preserving order
            seen = set()
            unique = []
            for u in urls:
                if u not in seen:
                    seen.add(u)
                    unique.append(u)
            if unique:
                return unique[:5]
        except Exception as e:
            print(f"    Bing search error: {e}", file=sys.stderr)
            time.sleep(2)
    return []


def download_image(url, filepath, referer="https://cn.bing.com/"):
    """Download an image from URL to filepath. Returns True on success."""
    headers = HEADERS.copy()
    headers["Referer"] = referer
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type:
            print(f"    Not an image: {content_type}", file=sys.stderr)
            return False
        if len(resp.content) < 1000:
            print(f"    Too small: {len(resp.content)} bytes", file=sys.stderr)
            return False
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        print(f"    Download failed: {e}", file=sys.stderr)
        return False


def process_items(items, prefix="", name_fn=None):
    """Process a list of items (spots or events), downloading images.

    Args:
        items: List of dicts with 'id', 'name', 'image', etc.
        prefix: Filename prefix ('' for spots, 'e' for events)
        name_fn: Optional function to generate search query from item

    Returns:
        (downloaded_count, skipped_count)
    """
    downloaded = 0
    skipped = 0

    for idx, item in enumerate(items):
        item_id = item["id"]
        filename = f"{prefix}{item_id}.jpg"
        filepath = IMAGES_DIR / filename

        # Already downloaded
        if filepath.exists():
            print(f"  [{prefix}{item_id}] {item['name']}: exists, skipping")
            item["image"] = f"images/{filename}"
            skipped += 1
            continue

        print(f"  [{prefix}{item_id}/{len(items)}] {item['name']}...", end=" ", flush=True)

        image_url = item.get("image", "")
        ok = False

        # Priority 1: If it already has a Baidu CDN URL, download directly
        if "baidu.com" in image_url:
            print("baidu CDN...", end=" ", flush=True)
            ok = download_image(image_url, filepath, referer="https://image.baidu.com/")

        # Priority 2: Search Bing for this place
        if not ok:
            if name_fn:
                query = name_fn(item)
            else:
                district = item.get("district", "")
                query = f"武汉{item['name']}" if not district else f"武汉{district}{item['name']}"
            print(f"bing...", end=" ", flush=True)
            urls = search_bing_images(query)
            if urls:
                ok = download_image(urls[0], filepath, referer="https://cn.bing.com/")

        if ok:
            item["image"] = f"images/{filename}"
            downloaded += 1
            print(f"OK ({os.path.getsize(filepath)//1024}KB)")
        else:
            skipped += 1
            print("FAILED")

        # Rate limiting: 1-2s delay between requests
        if idx < len(items) - 1:
            time.sleep(random.uniform(1.0, 2.0))

    return downloaded, skipped


def event_name_fn(event):
    """Generate search query for an event."""
    name = event["name"]
    category = event.get("category", "")
    if "演出" in name or "音乐" in name or "节" in name:
        return f"武汉{name}"
    return f"武汉{name}活动"


def main():
    IMAGES_DIR.mkdir(exist_ok=True)
    print(f"Images will be saved to: {IMAGES_DIR}")

    spots = load_json("spots.json")
    events = load_json("events.json")

    total_downloaded = 0
    total_skipped = 0

    # Process spots (47 items)
    print(f"\n=== Spots ({len(spots)} items) ===")
    d, s = process_items(spots)
    total_downloaded += d
    total_skipped += s

    # Process events (59 items)
    print(f"\n=== Events ({len(events)} items) ===")
    d, s = process_items(events, prefix="e", name_fn=event_name_fn)
    total_downloaded += d
    total_skipped += s

    # Save updated data files
    print(f"\n=== Summary ===")
    print(f"Downloaded: {total_downloaded}, Skipped/Failed: {total_skipped}")

    save_json("spots.json", spots)
    save_json("events.json", events)

    # Count files in images directory
    image_files = list(IMAGES_DIR.glob("*.jpg"))
    print(f"Total images in directory: {len(image_files)}")


if __name__ == "__main__":
    main()
