#!/usr/bin/env python3
"""
热点发现爬虫 - 模拟热门活动数据
通过分析现有数据中的趋势生成热点排行
"""
import json
import random
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✔ {filename} saved ({len(data)} items)")


def analyze_hot_events():
    """分析当前数据生成热点排行"""
    spots = load_json("spots.json")
    events = load_json("events.json")
    promotions = load_json("promotions.json")
    all_places = spots + events

    # 为每个有活动的场所计算热度
    scored = []
    for p in all_places:
        has_events = len(p.get("events", [])) > 0
        has_deals = len(p.get("deals", [])) > 0
        if not has_events and not has_deals:
            continue

        # 基础热度分
        score = p.get("rating", 4.0) * 1000
        if has_deals:
            score += 2000
        if has_events:
            score += 1500
        # 室内场所加分（当前季节适用性）
        if p.get("indoor"):
            score += 500
        # 免费加分
        if p.get("free"):
            score += 800
        # 随机波动模拟真实趋势
        score += random.randint(-500, 500)
        trend = random.choice(["up", "stable", "down"])

        scored.append({
            "rank": 0,
            "title": p["name"],
            "heat": int(score),
            "trend": trend,
            "place_id": p["id"],
            "reason": _generate_reason(p)
        })

    # 按热度排序
    scored.sort(key=lambda x: x["heat"], reverse=True)

    # 取前10名
    top10 = scored[:10]
    for i, item in enumerate(top10):
        item["rank"] = i + 1

    return top10


def _generate_reason(place):
    """生成热度理由"""
    reasons = []
    if place.get("deals"):
        reasons.append(f"限时优惠")
    if place.get("events"):
        reasons.append(f"近期活动")
    if place.get("free"):
        reasons.append(f"免费入场")
    if place.get("indoor"):
        now = datetime.now()
        if now.month in [6, 7, 8]:
            reasons.append(f"室内避暑")
    if "游乐" in place.get("tags", []):
        reasons.append(f"亲子游乐")
    if "水上" in place.get("tags", []):
        reasons.append(f"夏日玩水")

    return " · ".join(reasons[:3]) if reasons else "热门推荐"


def run():
    print(f"\n🔥 热点发现爬虫")
    top10 = analyze_hot_events()
    save_json("hot_events.json", top10)
    print(f"  热度范围: {top10[-1]['heat']} - {top10[0]['heat']}")
    return top10


if __name__ == "__main__":
    run()
