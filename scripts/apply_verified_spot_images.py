#!/usr/bin/env python3
"""Install reviewed spot photos and record their source metadata.

This script expects a manually reviewed Baidu Image candidate export in
``CAND_DIR``. It is intentionally not part of the scheduled crawler: image
relevance must be checked by a person before replacing public-site assets.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_DIR = Path(os.environ["CAND_DIR"])
SPOTS_PATH = ROOT / "data" / "spots.json"
MEDIA_PATH = ROOT / "data" / "media_gallery.json"
OUTPUT_DIR = ROOT / "images" / "spots"

# Candidate numbers selected after reviewing the full contact sheet.
SELECTION = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 8: 1, 9: 1, 10: 1,
    11: 1, 13: 1, 14: 1, 17: 1, 18: 1, 20: 1, 21: 1, 22: 1,
    23: 1, 24: 1, 25: 1, 26: 1, 27: 1, 28: 1, 29: 1, 30: 1,
    32: 1, 33: 1, 34: 2, 35: 1, 36: 1, 38: 1, 39: 2, 40: 2,
    41: 1, 42: 3, 43: 1, 45: 1, 46: 1, 47: 1, 49: 1, 50: 1,
    51: 1, 52: 3, 53: 1, 54: 1, 55: 1, 56: 1, 57: 3, 58: 1,
}

# Better primary/official images are prepared outside this script and copied
# in separately. Existing open-license or already verified images are kept.
KEEP_EXISTING = {6, 7, 12, 15, 16, 19, 31, 37, 44, 48, 59, 60, 61, 62, 63}

# Secondary frames are also manually selected. A shorter gallery is preferred
# when search results are ambiguous (for example, parks with duplicated names
# in other cities).
GALLERY_SELECTION = {
    1: [2, 3], 2: [2, 3], 3: [2, 3], 4: [2, 3], 5: [2, 3],
    8: [2, 3], 9: [2, 3], 10: [2, 3], 11: [2, 3], 13: [2, 3],
    14: [2, 3], 17: [2, 3], 18: [2, 3], 20: [2, 3], 21: [2, 3],
    22: [2, 3], 23: [2, 3], 24: [2, 3], 25: [2, 3], 26: [2, 3],
    27: [3], 28: [2, 3], 29: [2, 3], 30: [2, 3], 32: [2, 3],
    33: [2, 3], 34: [3], 35: [2, 3], 36: [2, 3], 38: [2, 3],
    39: [3], 40: [3], 41: [2, 3], 42: [1, 2], 43: [2, 3],
    45: [2, 3], 46: [2, 3], 47: [2, 3], 49: [2, 3], 50: [2, 3],
    51: [2, 3], 52: [1, 2], 53: [2], 54: [2, 3], 55: [2, 3],
    56: [2, 3], 57: [1], 58: [2, 3],
}


def normalized_jpeg(source: Path, target: Path) -> None:
    """Write a web-friendly, EXIF-rotated RGB JPEG."""
    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw).convert("RGB")
        if max(image.size) > 1800:
            image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        image.save(target, "JPEG", quality=86, optimize=True, progressive=True)


def main() -> None:
    spots = json.loads(SPOTS_PATH.read_text(encoding="utf-8"))
    index = json.loads((CANDIDATE_DIR / "index.json").read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    media = {
        "generated_from": "Reviewed public web references",
        "usage_notice": "地点主图已逐项人工核对。图片用于地点识别与导览，来源页面见每条记录；开放许可图片另行标注作者与许可。",
        "items": [],
    }

    for spot in spots:
        spot_id = int(spot["id"])
        if spot_id in KEEP_EXISTING:
            continue

        candidate_number = SELECTION[spot_id]
        source_file = next(CANDIDATE_DIR.glob(f"{spot_id:02d}-{candidate_number}.*"))
        image_numbers = [candidate_number, *GALLERY_SELECTION.get(spot_id, [])]
        gallery = []
        for gallery_index, image_number in enumerate(image_numbers):
            source_file = next(CANDIDATE_DIR.glob(f"{spot_id:02d}-{image_number}.*"))
            suffix = "" if gallery_index == 0 else f"-{gallery_index + 1}"
            target = OUTPUT_DIR / f"{spot_id:02d}{suffix}.jpg"
            normalized_jpeg(source_file, target)
            candidate = index[str(spot_id)]["candidates"][image_number - 1]
            relative = target.relative_to(ROOT).as_posix()
            gallery.append(relative)
            media["items"].append({
                "place_id": spot_id,
                "name": spot["name"],
                "image": relative,
                "source_url": candidate.get("source_url", ""),
                "source_title": candidate.get("title", ""),
                "asset_note": "本地展示副本来自图片搜索缩略图，原页面版权归其权利人；如权利人要求将立即替换。",
                "review_status": "人工核对地点名称与画面",
            })
        spot["image"] = gallery[0]
        spot["gallery"] = gallery

    # Existing open-license/verified records are merged by the caller after
    # official assets have been installed.
    SPOTS_PATH.write_text(json.dumps(spots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MEDIA_PATH.write_text(json.dumps(media, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Installed {len(media['items'])} reviewed spot images")


if __name__ == "__main__":
    main()
