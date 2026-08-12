#!/usr/bin/env python3
"""Merge reviewed search candidates with official and open-license assets."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPOTS_PATH = ROOT / "data" / "spots.json"
MEDIA_PATH = ROOT / "data" / "media_gallery.json"

OFFICIAL = {
    6: {
        "image": "images/spots/06.jpg",
        "source_url": "https://hwzs.cscec.com/jpgc/syzhl/202311/3735307.html",
        "source_title": "永旺梦乐城武汉经开购物中心",
        "credit": "中建三局二公司华中分公司",
    },
    7: {
        "image": "images/spots/07.jpg",
        "source_url": "https://www.ingkacentres.com/en/where-we-are/china/livat-wuhan/",
        "source_title": "Livat Wuhan",
        "credit": "Ingka Centres",
    },
    12: {
        "image": "images/spots/12.jpg",
        "source_url": "https://www.wuhan.gov.cn/sy/whyw/202405/t20240524_2406800.shtml",
        "source_title": "玩水时刻又来了！武汉玛雅海滩6月8日开园",
        "credit": "武汉市人民政府门户网站 / 长江日报",
    },
    16: {
        "image": "images/spots/16.jpg",
        "source_url": "https://www.wuhan.gov.cn/ztzl/24zt/csrl/202606/t20260625_2803524.shtml",
        "source_title": "武汉人的童年回忆要回来了！中山公园激流勇进6月28日试运行",
        "credit": "武汉市人民政府门户网站",
    },
    31: {
        "image": "images/spots/31.jpg",
        "source_url": "https://www.qingshan.gov.cn/zjqs/qsfc/201703/t20170329_311029.shtml",
        "source_title": "和平公园",
        "credit": "武汉市青山区人民政府",
    },
    37: {
        "image": "images/spots/37.jpg",
        "source_url": "https://www.whkfq.gov.cn/xwzx/yw/kfqyw/qnxw/202304/t20230403_2180433.html",
        "source_title": "四季可赏花 月月能观景 汤湖公园获评武汉首批“精致公园”",
        "credit": "武汉经开区融媒体中心",
    },
    61: {
        "image": "images/spots/61.jpg",
        "source_url": "https://cgw.wuhan.gov.cn/CGYW_13530/SZCG_13564/202603/t20260304_2735051.shtml",
        "source_title": "更新更美好，武昌这两座“湖北最美”口袋公园值得一逛",
        "credit": "武汉市城市管理执法委员会 / 极目新闻",
    },
}

OPEN_LICENSE = {
    15: {
        "image": "images/media/east-lake.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Mount_Mo_and_East_Lake%2C_Wuhan.jpg",
        "source_title": "Mount Mo and East Lake, Wuhan",
        "author": "Zheng Zhou",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
    },
    19: {
        "image": "images/media/wuhan-zoo.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:WUHAN_ZOO.jpg",
        "source_title": "WUHAN ZOO",
        "author": "Wuchernchau",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
    },
    44: {
        "image": "images/media/east-lake.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Mount_Mo_and_East_Lake%2C_Wuhan.jpg",
        "source_title": "Mount Mo and East Lake, Wuhan",
        "author": "Zheng Zhou",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
    },
    48: {
        "image": "images/media/yellow-crane-tower.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:CN_-_Hubei_-_Wuhan_-_Kranichpagode.jpg",
        "source_title": "CN - Hubei - Wuhan - Kranichpagode",
        "author": "MonsieurRoi",
        "license": "CC BY-SA 3.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0",
    },
}


def main() -> None:
    spots = json.loads(SPOTS_PATH.read_text(encoding="utf-8"))
    media = json.loads(MEDIA_PATH.read_text(encoding="utf-8"))

    for spot in spots:
        spot_id = int(spot["id"])
        existing = list(dict.fromkeys(spot.get("gallery", [spot["image"]])))

        if spot_id in OFFICIAL:
            record = OFFICIAL[spot_id]
            spot["image"] = record["image"]
            official_gallery = [
                record["image"],
                f"images/spots/{spot_id:02d}-2.jpg",
                f"images/spots/{spot_id:02d}-3.jpg",
            ] if spot_id in {6, 12, 16, 31, 37, 61} else [record["image"]]
            spot["gallery"] = [*official_gallery, *[path for path in existing if path not in official_gallery]][:5]
            media["items"].insert(0, {
                "place_id": spot_id,
                "name": spot["name"],
                **record,
                "review_status": "官方页面实景图",
            })
        elif spot_id in OPEN_LICENSE:
            record = OPEN_LICENSE[spot_id]
            spot["image"] = record["image"]
            extras = {
                15: ["images/spots/15-2.jpg", "images/spots/15-3.jpg"],
                19: ["images/spots/19-2.jpg", "images/spots/19-3.jpg"],
                44: ["images/spots/44-2.jpg", "images/spots/44-3.jpg"],
                48: ["images/media/yangtze-river-bridge.jpg", "images/spots/48-2.jpg", "images/spots/48-3.jpg"],
            }.get(spot_id, [])
            spot["gallery"] = [record["image"], *extras]
            media["items"].insert(0, {
                "place_id": spot_id,
                "name": spot["name"],
                **record,
                "review_status": "Wikimedia Commons 开放许可图片",
            })
        elif spot_id >= 59:
            spot["gallery"] = [
                spot["image"],
                f"images/spots/{spot_id:02d}-2.jpg",
                f"images/spots/{spot_id:02d}-3.jpg",
            ] if spot_id in {59, 60, 62, 63} else existing
            media["items"].insert(0, {
                "place_id": spot_id,
                "name": spot["name"],
                "image": spot["image"],
                "source_url": spot.get("source_url", ""),
                "source_title": spot.get("source", "已核验报道"),
                "credit": spot.get("image_credit", ""),
                "review_status": "来源页面实景图",
            })

    media["generated_from"] = "Reviewed official, open-license and public web references"
    SPOTS_PATH.write_text(json.dumps(spots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MEDIA_PATH.write_text(json.dumps(media, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Finalized {len(spots)} places and {len(media['items'])} image records")


if __name__ == "__main__":
    main()
