#!/usr/bin/env python3
"""
Update index.html inline DATA and highlights from spots.json and events.json
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INDEX_HTML = BASE_DIR / "index.html"

def load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def esc(s):
    """Escape string for JS single-quoted string"""
    if not s:
        return ""
    return s.replace("\\", "\\\\").replace("'", "\\'")

def fmt_val(v, indent=8):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return "'" + esc(v) + "'"
    if isinstance(v, list):
        if not v:
            return "[]"
        if all(isinstance(x, str) for x in v):
            return "[" + ", ".join(fmt_val(x) for x in v) + "]"
        items = ",\n" + " " * (indent + 2)
        items = items.join(fmt_val(item, indent + 2) for item in v)
        return "[\n" + " " * (indent + 2) + items + "\n" + " " * indent + "]"
    if isinstance(v, dict):
        if not v:
            return "{}"
        inner = " " * (indent + 2)
        pairs = ",\n" + inner
        pairs = pairs.join(f"{k}: {fmt_val(val, indent + 2)}" for k, val in v.items())
        return "{\n" + inner + pairs + "\n" + " " * indent + "}"
    return str(v)

def fmt_place(p, indent=6):
    ii = " " * (indent + 2)
    fields = []
    fields.append("id: " + str(p["id"]))
    fields.append("name: " + fmt_val(p["name"]))
    fields.append("category: " + fmt_val(p["category"]))
    fields.append("district: " + fmt_val(p["district"]))
    fields.append("seasons: " + fmt_val(p["seasons"], indent + 2))
    fields.append("description: " + fmt_val(p.get("description", "")))
    fields.append("tags: " + fmt_val(p["tags"], indent + 2))
    fields.append("rating: " + str(p["rating"]))
    fields.append("address: " + fmt_val(p.get("address", "")))
    fields.append("hours: " + fmt_val(p.get("hours", "")))
    fields.append("transport: " + fmt_val(p.get("transport", "")))
    fields.append("image: " + fmt_val(p.get("image", "")))

    evts = p.get("events", [])
    if evts:
        parts = []
        for e in evts:
            parts.append("{ text: " + fmt_val(e.get("text", "")) + ", schedule: " + fmt_val(e.get("schedule", "")) + " }")
        fields.append("events: [" + ", ".join(parts) + "]")
    else:
        fields.append("events: []")

    dls = p.get("deals", [])
    if dls:
        parts = []
        for d in dls:
            parts.append("{ text: " + fmt_val(d.get("text", "")) + ", validUntil: " + fmt_val(d.get("validUntil", "")) + " }")
        fields.append("deals: [" + ", ".join(parts) + "]")
    else:
        fields.append("deals: []")

    fields.append("age_min: " + str(p.get("age_min", 0)))
    fields.append("age_max: " + str(p.get("age_max", 12)))
    fields.append("price: " + str(p.get("price", 0)))
    fields.append("free: " + ("true" if p.get("free") else "false"))
    fields.append("indoor: " + ("true" if p.get("indoor") else "false"))
    fields.append("parking: " + fmt_val(p.get("parking", "待确认")))

    return "{\n" + ii + (",\n" + ii).join(fields) + "\n" + " " * indent + "}"

def main():
    spots = load_json("spots.json")
    events = load_json("events.json")

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # Find and replace places array
    marker_places = "// 所有推荐场所"
    pos = html.find(marker_places)
    if pos < 0:
        print("ERROR: places marker not found")
        return False

    bracket_start = html.index("[", pos)
    # Find matching closing bracket
    depth = 0
    in_str = False
    in_single = False
    end = -1
    for i in range(bracket_start, len(html)):
        c = html[i]
        if in_str:
            if c == '"' and html[i-1] != "\\":
                in_str = False
        elif in_single:
            if c == "'" and html[i-1] != "\\":
                in_single = False
        else:
            if c == '"': in_str = True
            elif c == "'": in_single = True
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break

    all_places = spots + events
    new_places = "[\n      // ===== 所有推荐场所 (自动生成) =====\n      "
    new_places += ",\n      ".join(fmt_place(p) for p in all_places)
    new_places += "\n    ]"

    html = html[:bracket_start] + new_places + html[end + 1:]

    # Find and replace highlights array
    marker_hl = "// 当前重点优惠/活动（首页高亮）"
    # Also try alternate marker
    pos = html.find(marker_hl)
    if pos < 0:
        marker_hl = "// 当前重点优惠"
        pos = html.find(marker_hl)
    if pos < 0:
        print("ERROR: highlights marker not found")
        return False

    bracket_start = html.index("[", pos)
    depth = 0
    in_str = False
    in_single = False
    end = -1
    for i in range(bracket_start, len(html)):
        c = html[i]
        if in_str:
            if c == '"' and html[i-1] != "\\":
                in_str = False
        elif in_single:
            if c == "'" and html[i-1] != "\\":
                in_single = False
        else:
            if c == '"': in_str = True
            elif c == "'": in_single = True
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break

    highlights = [
        {"title": "汉口江滩亲子游", "desc": "亚洲最大滨江公园，沙池观光小火车，周末遫娃首选", "image": "https://picsum.photos/seed/deal-hankou-river/800/400", "link": "#place-23", "badge": "夏季推荐", "season": "summer"},
        {"title": "欢乐谷HOHA电音节", "desc": "暨期夜场电音派对，游乐+水上+烟花一票畅玩", "image": "https://picsum.photos/seed/deal-hoha/800/400", "link": "#place-9", "badge": "夏季限定", "season": "summer"},
        {"title": "夜上黄鹤楼", "desc": "光影秀+实景演出，登楼远瞰江城夜景", "image": "https://picsum.photos/seed/deal-crane/800/400", "link": "#place-31", "badge": "热门推荐", "season": "all"},
        {"title": "知音号沉浸式演出", "desc": "长江游轮穿越民国，武汉城市文化名片", "image": "https://picsum.photos/seed/deal-zhiyin/800/400", "link": "#place-29", "badge": "文化体验", "season": "all"},
    ]

    items = []
    for h in highlights:
        items.append("{\n      title: " + fmt_val(h["title"]) + ",\n      desc: " + fmt_val(h["desc"]) + ",\n      image: " + fmt_val(h["image"]) + ",\n      link: " + fmt_val(h["link"]) + ",\n      badge: " + fmt_val(h["badge"]) + ",\n      season: " + fmt_val(h["season"]) + "\n    }")

    new_hl = "[\n    " + ",\n    ".join(items) + "\n  ]"
    html = html[:bracket_start] + new_hl + html[end + 1:]

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"OK: index.html updated (places: {len(all_places)}, highlights: {len(highlights)})")
    return True

if __name__ == "__main__":
    main()
