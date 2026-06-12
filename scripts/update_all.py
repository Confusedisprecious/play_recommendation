#!/usr/bin/env python3
"""
武汉亲子游玩推荐 - 定时数据更新脚本
根据 开发文档V0.md 要求，每天 02:00/08:00/14:00/20:00 执行
"""

import json
import os
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
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✔ {filename} saved ({len(data)} items)")


def update_last_update():
    """更新 last_update.json 时间戳"""
    now = datetime.now()
    hour = now.hour
    # 对齐到最近的更新批次
    batches = [2, 8, 14, 20]
    current_batch = max(b for b in batches if b <= hour) if hour >= 2 else batches[-1]

    # 计算下次更新时间
    next_idx = (batches.index(current_batch) + 1) % len(batches)
    next_hour = batches[next_idx]
    next_update = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    if next_hour <= current_batch:
        next_update = next_update.replace(day=next_update.day + 1)

    spots = load_json("spots.json")
    events = load_json("events.json")
    promotions = load_json("promotions.json")
    hot_events = load_json("hot_events.json")

    data = {
        "last_update": now.strftime("%Y-%m-%d %H:%M"),
        "next_update": next_update.strftime("%Y-%m-%d %H:%M"),
        "data_version": "1.0",
        "total_places": len(spots),
        "total_events": len(events),
        "total_promotions": len(promotions),
        "total_hot_events": len(hot_events),
        "generated_by": "update_all.py"
    }
    save_json("last_update.json", data)
    return data


def main():
    print("=" * 50)
    print("武汉亲子游玩推荐 - 数据更新")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 验证数据完整性
    spots = load_json("spots.json")
    events = load_json("events.json")
    promotions = load_json("promotions.json")
    hot_events = load_json("hot_events.json")
    weather = load_json("weather_recommendation.json")

    print(f"\n📊 数据统计:")
    print(f"  场所: {len(spots)}")
    print(f"  活动: {len(events)}")
    print(f"  优惠: {len(promotions)}")
    print(f"  热门: {len(hot_events)}")

    # 更新 last_update.json
    info = update_last_update()

    print(f"\n✅ 更新完成")
    print(f"  上次更新: {info['last_update']}")
    print(f"  下次更新: {info['next_update']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
