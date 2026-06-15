#!/usr/bin/env python3
"""
第二步数据丰富 - 添加新场所、修复图片种子
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_json(filename):
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✔ {filename} saved ({len(data)} items)")

def add_spots():
    """添加8个新场所"""
    spots = load_json("spots.json")
    existing_ids = {s["id"] for s in spots}
    next_id = max(existing_ids) + 1

    new_spots = [
        {
            "id": next_id, "name": "洪山江滩", "category": "park",
            "district": "洪山区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "杨泗港长江大桥下的生态江滩公园，2022年新开放，有儿童乐园、篮球场、滑板公园和超长滨江步道，樱花季绝美。",
            "tags": ["江滩公园", "儿童乐园", "滑板公园", "滨江步道", "樱花"],
            "rating": 4.5, "address": "洪山区白沙洲大道与江国路交汇处（杨泗港大桥下）",
            "hours": "全天开放", "transport": "地铁5号线烽胜路站换乘公交",
            "image": "https://picsum.photos/seed/wuhan-hongshan-river/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "江滩停车场"
        },
        {
            "id": next_id + 1, "name": "武昌江滩", "category": "park",
            "district": "武昌区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "武昌段滨江长廊，从大堤口到月亮湾，有观景平台、儿童沙池和骑行绿道，对望汉口江滩和长江大桥，夜景超美。",
            "tags": ["江滩公园", "观景平台", "儿童沙池", "骑行", "夜景"],
            "rating": 4.3, "address": "武昌区临江大道（大堤口至月亮湾）",
            "hours": "全天开放", "transport": "地铁5号线三层楼站/积玉桥站",
            "image": "https://picsum.photos/seed/wuhan-wuchang-river/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "月亮湾停车场"
        },
        {
            "id": next_id + 2, "name": "汉阳江滩", "category": "park",
            "district": "汉阳区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "汉阳沿江生态江滩，从晴川阁到杨泗港，有大禹神话园、儿童乐园和体育设施，鹦鹉洲长江大桥下很适合拍照。",
            "tags": ["江滩公园", "大禹神话园", "儿童乐园", "体育设施", "桥梁景观"],
            "rating": 4.2, "address": "汉阳区晴川大道（晴川阁至杨泗港）",
            "hours": "全天开放", "transport": "地铁4号线拦江路站",
            "image": "https://picsum.photos/seed/wuhan-hanyang-river/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
        {
            "id": next_id + 3, "name": "武汉科学技术馆", "category": "playground",
            "district": "江岸区",
            "seasons": ["spring", "summer", "autumn", "winter"],
            "description": "武汉科技馆新馆，紧邻汉口江滩，常设宇宙、生命、水、光、信息、交通等八大展厅，大量互动体验项目，孩子可以玩一整天。",
            "tags": ["科技馆", "互动体验", "科普教育", "室内场馆", "地铁直达"],
            "rating": 4.7, "address": "江岸区沿江大道68号（汉口江滩旁）",
            "hours": "09:00-16:30（周一周二闭馆）", "transport": "地铁1号线/8号线黄浦路站",
            "image": "https://picsum.photos/seed/wuhan-sci-museum/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": True, "parking": "武汉科技馆停车场"
        },
        {
            "id": next_id + 4, "name": "东湖磨山", "category": "park",
            "district": "武昌区",
            "seasons": ["spring", "autumn"],
            "description": "东湖风景区核心景点，有楚天台、索道、滑道、儿童乐园、樱花园（东湖樱花节主场地），登山观湖视野极佳，可玩半天到一天。",
            "tags": ["东湖", "索道", "滑道", "樱花园", "登山观湖"],
            "rating": 4.6, "address": "武昌区东湖风景区磨山景区",
            "hours": "08:00-17:00", "transport": "地铁8号线梨园站转乘东湖观光车",
            "image": "https://picsum.photos/seed/wuhan-moshan/400/300",
            "events": [{"text": "东湖樱花节", "schedule": "3月-4月"}],
            "deals": [],
            "age_min": 3, "age_max": 12, "price": 60, "free": False,
            "indoor": False, "parking": "磨山停车场"
        },
        {
            "id": next_id + 5, "name": "花博汇", "category": "park",
            "district": "蔡甸区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "武汉大型花卉主题景区，四季花海、萌宠乐园、亲子农场、帐篷露营、焰火秀和游乐嘉年华，适合全家出游一整天的好去处。",
            "tags": ["花海", "萌宠乐园", "亲子农场", "露营", "焰火秀"],
            "rating": 4.5, "address": "蔡甸区大集街知音湖大道天星村1号",
            "hours": "08:30-17:30（周末延至21:00）", "transport": "建议自驾，地铁3号线/4号线转公交",
            "image": "https://picsum.photos/seed/wuhan-huabohui/400/300",
            "events": [{"text": "花博汇焰火秀", "schedule": "周末及节假日 20:00"}],
            "deals": [{"text": "亲子年票 198元（不限次）", "validUntil": "2026-12-31"}],
            "age_min": 0, "age_max": 12, "price": 60, "free": False,
            "indoor": False, "parking": "大型免费停车场"
        },
        {
            "id": next_id + 6, "name": "盘龙城遗址博物院", "category": "playground",
            "district": "黄陂区",
            "seasons": ["spring", "summer", "autumn", "winter"],
            "description": "武汉新晋文化地标，3500年前商代遗址，博物院建筑获国际设计大奖，有儿童考古体验区和大量珍贵文物展出，兼具教育性和趣味性。",
            "tags": ["博物院", "考古体验", "商代遗址", "建筑地标", "文化教育"],
            "rating": 4.6, "address": "黄陂区盘龙城经济开发区盘龙大道1号",
            "hours": "09:00-17:00（周一闭馆）", "transport": "地铁2号线盘龙城站",
            "image": "https://picsum.photos/seed/wuhan-panlong/400/300",
            "events": [{"text": "小小考古家体验营", "schedule": "每月第二个周末"}],
            "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": True, "parking": "免费停车场"
        },
        {
            "id": next_id + 7, "name": "奇趣蛋壳公园", "category": "park",
            "district": "硚口区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "2023年新开的网红无动力儿童公园，以巨型蛋壳滑梯为标志，有超长滑梯、攀爬网、沙池、蹦床、秋千等，全部免费，孩子能玩到不想走。",
            "tags": ["无动力乐园", "蛋壳滑梯", "攀爬", "沙池", "免费"],
            "rating": 4.6, "address": "硚口区解放大道与汉西一路交汇处",
            "hours": "全天开放", "transport": "地铁1号线汉西一路站",
            "image": "https://picsum.photos/seed/wuhan-egg-park/400/300",
            "events": [], "deals": [],
            "age_min": 1, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "停车位较少，建议公共交通"
        },
    ]

    spots.extend(new_spots)
    save_json("spots.json", spots)
    print(f"  ➕ 新增 {len(new_spots)} 个场所")
    return spots

def fix_event_images():
    """修复events.json中数字种子改为描述性种子"""
    events = load_json("events.json")
    image_map = {
        31: "wuhan-tourism-fest",
        32: "wuhan-city-orienteering",
        33: "wuhan-river-film",
        34: "wuhan-intangible-heritage",
        35: "wuhan-children-play",
        36: "wuhan-chu-cultural",
        37: "wuhan-archaeology-kid",
        38: "wuhan-bianzhong",
        46: "wuhan-summer-music-old",
        47: "wuhan-museum-night",
        48: "wuhan-physics-class",
        49: "wuhan-science-camp",
        50: "wuhan-ai-expo",
        51: "wuhan-scientist-class",
    }
    changed = 0
    for e in events:
        eid = e["id"]
        if eid in image_map:
            new_seed = image_map[eid]
            old_img = e.get("image", "")
            if f"event-{eid}" in old_img:
                e["image"] = f"https://picsum.photos/seed/{new_seed}/400/300"
                changed += 1
    save_json("events.json", events)
    print(f"  🖼️ 修复 {changed} 个活动图片种子")
    return events

if __name__ == "__main__":
    print("🏗️ 添加新场所...")
    add_spots()
    print("\n🖼️ 修复活动图片种子...")
    fix_event_images()
    print("\n✅ 数据更新完成")
