#!/usr/bin/env python3
"""
天气与场景推荐生成脚本
生成天气推荐数据（雨天/晴天/高温/免费）
"""

import json
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

def generate_recommendations():
    """根据 spots 和 events 数据自动生成场景推荐"""
    spots = load_json("spots.json")
    events = load_json("events.json")
    all_places = spots + events

    recommendations = {
        "rainy": {
            "title": "雨天推荐",
            "description": "下雨天也不愁，这些室内场所最适合带娃",
            "place_ids": [p["id"] for p in all_places if p.get("indoor") and p.get("age_min", 0) >= 0]
        },
        "sunny": {
            "title": "晴天推荐",
            "description": "好天气当然要户外，这些户外场所正适合",
            "place_ids": [p["id"] for p in all_places if not p.get("indoor") and p.get("age_min", 0) >= 3]
        },
        "hot": {
            "title": "高温推荐",
            "description": "高温天气，带娃去这些凉爽的室内场所",
            "place_ids": [p["id"] for p in all_places if p.get("indoor")]
        },
        "free": {
            "title": "免费推荐",
            "description": "不花钱也能快乐遛娃，这些免费场所推荐给你",
            "place_ids": [p["id"] for p in all_places if p.get("free")]
        }
    }

    # 按年龄分类推荐
    for age_label, age_min, age_max in [("0-3岁", 0, 3), ("3-6岁", 3, 6), ("6-12岁", 6, 12)]:
        key = f"age_{age_min}_{age_max}".replace("-", "_")
        recommendations[key] = {
            "title": f"{age_label}推荐",
            "description": f"适合{age_label}的亲子场所",
            "place_ids": [p["id"] for p in all_places if p.get("age_min", 0) <= age_min and p.get("age_max", 12) >= age_max]
        }

    save_json("weather_recommendation.json", [recommendations])
    print(f"  ✔ 场景推荐已生成 ({len(recommendations)} 个场景)")

if __name__ == "__main__":
    generate_recommendations()
