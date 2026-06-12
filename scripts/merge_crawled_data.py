#!/usr/bin/env python3
"""
数据合并脚本 - 将爬虫结果合并到主数据文件
"""
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(filename, data):
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✔ {filename} saved ({len(data)} items)")


def merge_crawled_events():
    """将爬取的活动合并到 events.json"""
    events = load_json("events.json")
    existing_titles = {e["name"] for e in events}
    new_count = 0
    next_id = max([e["id"] for e in events], default=0) + 1

    crawled_files = [
        "crawled_wh_culture.json",
        "crawled_museum.json",
        "crawled_science_museum.json",
        "crawled_happy_valley.json",
        "crawled_polar_ocean.json",
        "crawled_localbao.json",
    ]

    for filename in crawled_files:
        items = load_json(filename)
        for item in items:
            title = item.get("title", "").strip()
            if not title or title in existing_titles:
                continue
            # 从爬取数据创建 events 结构
            event = {
                "id": next_id,
                "name": title,
                "category": "event",
                "district": item.get("district", "武昌区"),
                "seasons": _detect_seasons(title, item.get("description", "")),
                "description": item.get("description", item.get("url", "")),
                "tags": [item.get("category", "亲子活动"), "热门活动"],
                "rating": 4.0,
                "address": item.get("address", "待确认"),
                "hours": item.get("hours", item.get("time", "待确认")),
                "transport": item.get("transport", "待确认"),
                "image": "https://picsum.photos/seed/event-" + str(next_id) + "/400/300",
                "events": [],
                "deals": [],
                "age_min": 3,
                "age_max": 12,
                "price": 0,
                "free": False,
                "indoor": True,
                "parking": "待确认",
                "source": item.get("source", "武汉文旅局"),
            }
            events.append(event)
            existing_titles.add(title)
            next_id += 1
            new_count += 1

    if new_count > 0:
        save_json("events.json", events)
    print(f"  ➕ 新增 {new_count} 条活动")
    return new_count


def merge_crawled_promotions():
    """将爬取的优惠信息合并到 promotions.json"""
    promotions = load_json("promotions.json")
    existing = {p["title"] for p in promotions}
    new_count = 0

    crawled_files = [
        "crawled_happy_valley.json",
        "crawled_wh_culture.json",
    ]

    for filename in crawled_files:
        items = load_json(filename)
        for item in items:
            title = item.get("title", "").strip()
            if not title or title in existing:
                continue
            if "优惠" in title or "折扣" in title or "免费" in title or "票" in title:
                promo = {
                    "id": f"deal_crawled_{len(promotions) + 1}",
                    "title": title,
                    "location": item.get("source", "武汉"),
                    "original_price": 0,
                    "price": 0,
                    "desc": item.get("description", ""),
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-12-31"),
                    "source": item.get("source", "爬虫"),
                    "place_id": 0,
                }
                promotions.append(promo)
                existing.add(title)
                new_count += 1

    if new_count > 0:
        save_json("promotions.json", promotions)
    print(f"  ➕ 新增 {new_count} 条优惠")
    return new_count


def _detect_seasons(title: str, desc: str = "") -> list:
    """根据标题和描述判断季节"""
    text = title + desc
    seasons = []
    if any(k in text for k in ["春", "樱花"]):
        seasons.append("spring")
    if any(k in text for k in ["夏", "暑", "水", "泳"]):
        seasons.append("summer")
    if any(k in text for k in ["秋", "菊", "枫"]):
        seasons.append("autumn")
    if any(k in text for k in ["冬", "雪", "灯", "年"]):
        seasons.append("winter")

    # 全年活动
    if not seasons:
        seasons = ["spring", "summer", "autumn", "winter"]

    return seasons


def merge_all():
    print(f"\n📦 合并爬取数据到主数据文件")
    event_count = merge_crawled_events()
    promo_count = merge_crawled_promotions()
    print(f"  总计新增: {event_count} 活动 + {promo_count} 优惠")
    return event_count + promo_count


if __name__ == "__main__":
    merge_all()
