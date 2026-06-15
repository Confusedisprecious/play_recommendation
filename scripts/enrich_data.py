#!/usr/bin/env python3
"""
丰富数据脚本 - 添加公园、户外演出、音乐节等信息
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
    print(f"  ✔ {filename} saved ({len(data)} items)")

def enrich_events():
    """清理并丰富events.json：保留好数据、删除垃圾、添加新活动"""
    events = load_json("events.json")

    # 保留的真实活动ID (23-30)
    good_ids = {23, 24, 25, 26, 27, 28, 29, 30}
    # 保留的有用爬虫数据 (有实际地址和描述的)
    keep_ids = {36, 37, 38, 47, 48, 49, 50, 51}
    # 需要丰富的数据 (有潜力的标题但信息不全)
    enrich_ids = {31, 32, 33, 34, 35, 46}

    kept = []
    for e in events:
        eid = e["id"]
        if eid in good_ids:
            kept.append(e)
        elif eid in keep_ids:
            kept.append(e)
        elif eid in enrich_ids:
            # 丰富数据
            enriched = _enrich_event(e)
            kept.append(enriched)
        # 其他全部丢弃 (IDs 39-45, 52-68)

    # 找到最大ID
    max_id = max(e["id"] for e in kept) if kept else 30
    next_id = max_id + 1

    # 添加新活动
    new_events = [
        # ===== 音乐节 =====
        {
            "id": next_id, "name": "VAC电音节", "category": "event",
            "district": "硚口区",
            "seasons": ["summer", "autumn"],
            "description": "华中地区最大电子音乐节，邀请国内外知名DJ，世界级舞台和炫酷灯光秀，园博园内举办。",
            "tags": ["电子音乐", "音乐节", "灯光秀", "潮流文化"],
            "rating": 4.3, "address": "硚口区武汉园博园",
            "hours": "15:00-22:00", "transport": "地铁7号线园博园站",
            "image": "https://picsum.photos/seed/wuhan-vac/400/300",
            "events": [], "deals": [],
            "age_min": 6, "age_max": 12, "price": 280, "free": False,
            "indoor": False, "parking": "园博园停车场", "source": "VAC电音节"
        },
        {
            "id": next_id + 1, "name": "麦田音乐节", "category": "event",
            "district": "硚口区",
            "seasons": ["spring", "autumn"],
            "description": "知名综合性音乐节品牌，涵盖摇滚、民谣、流行等多种风格，设有亲子休息区。",
            "tags": ["音乐节", "亲子友好", "摇滚", "民谣"],
            "rating": 4.4, "address": "硚口区武汉园博园",
            "hours": "13:00-21:00", "transport": "地铁7号线园博园站",
            "image": "https://picsum.photos/seed/wuhan-maitian/400/300",
            "events": [], "deals": [],
            "age_min": 6, "age_max": 12, "price": 260, "free": False,
            "indoor": False, "parking": "园博园停车场", "source": "麦田音乐节"
        },
        {
            "id": next_id + 2, "name": "江城民谣音乐节", "category": "event",
            "district": "江岸区",
            "seasons": ["autumn"],
            "description": "武汉本土民谣音乐盛会，风格清新温和，以城市文化为主题，江滩开阔，氛围轻松。",
            "tags": ["民谣", "音乐节", "江滩", "户外音乐"],
            "rating": 4.5, "address": "江岸区汉口江滩",
            "hours": "14:00-21:00", "transport": "地铁1号线/8号线黄浦路站",
            "image": "https://picsum.photos/seed/wuhan-minyao/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "汉口江滩停车场", "source": "江城民谣音乐节"
        },
        {
            "id": next_id + 3, "name": "武汉琴台音乐节", "category": "event",
            "district": "汉阳区",
            "seasons": ["autumn"],
            "description": "涵盖古典音乐、民乐、交响乐的高雅音乐节，多场室内演出，部分场次设有儿童专场。",
            "tags": ["古典音乐", "交响乐", "儿童专场", "室内演出"],
            "rating": 4.6, "address": "汉阳区琴台大剧院/琴台音乐厅",
            "hours": "演出日 19:30-21:30", "transport": "地铁6号线琴台站",
            "image": "https://picsum.photos/seed/wuhan-qintai/400/300",
            "events": [], "deals": [],
            "age_min": 4, "age_max": 12, "price": 80, "free": False,
            "indoor": True, "parking": "琴台大剧院停车场", "source": "琴台音乐节"
        },
        {
            "id": next_id + 4, "name": "武汉欢乐谷HOHA电音节", "category": "event",
            "district": "洪山区",
            "seasons": ["summer"],
            "description": "欢乐谷夏季夜间大型电音派对，结合游乐设施、水上项目和电音舞台，还有烟花秀。",
            "tags": ["电音", "水上乐园", "烟花秀", "夜场"],
            "rating": 4.5, "address": "洪山区欢乐大道196号（武汉欢乐谷）",
            "hours": "17:00-21:00（7月-8月）", "transport": "地铁4号线仁和路站换乘公交",
            "image": "https://picsum.photos/seed/wuhan-hoha/400/300",
            "events": [], "deals": [{"text": "欢乐谷夜场票 120元", "validUntil": "2026-08-31"}],
            "age_min": 3, "age_max": 12, "price": 120, "free": False,
            "indoor": False, "parking": "欢乐谷停车场", "source": "武汉欢乐谷"
        },
        {
            "id": next_id + 5, "name": "夏至音乐日（中法音乐节）", "category": "event",
            "district": "江岸区",
            "seasons": ["summer"],
            "description": "源自法国的夏至音乐节传统，武汉多个场地同时举办免费户外音乐会，涵盖多种音乐风格。",
            "tags": ["免费活动", "户外音乐", "中法交流", "亲子友好"],
            "rating": 4.3, "address": "江岸区汉口江滩/403艺术中心等多场地",
            "hours": "6月21日前后 16:00-21:00", "transport": "地铁1号线/8号线黄浦路站",
            "image": "https://picsum.photos/seed/wuhan-summer-music/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "汉口江滩停车场", "source": "夏至音乐日"
        },
        # ===== 户外演出/夜游 =====
        {
            "id": next_id + 6, "name": "知音号沉浸式演出", "category": "event",
            "district": "江岸区",
            "seasons": ["spring", "autumn"],
            "description": "长江上的复古游轮沉浸式演出，观众可换装参与，体验上世纪武汉故事，城市文化名片。",
            "tags": ["沉浸式演出", "游轮", "文化体验", "长江"],
            "rating": 4.7, "address": "江岸区汉口江滩知音号码头",
            "hours": "每晚 19:30-21:00", "transport": "地铁1号线/8号线黄浦路站",
            "image": "https://picsum.photos/seed/wuhan-zhiyin/400/300",
            "events": [], "deals": [{"text": "亲子套票 428元（1大1小）", "validUntil": "2026-12-31"}],
            "age_min": 6, "age_max": 12, "price": 298, "free": False,
            "indoor": False, "parking": "汉口江滩停车场", "source": "知音号"
        },
        {
            "id": next_id + 7, "name": "长江两江游览夜游", "category": "event",
            "district": "武昌区",
            "seasons": ["summer"],
            "description": "乘船游览长江和汉江，欣赏两江四岸灯光秀，途经黄鹤楼、长江大桥、龟山电视塔等地标。",
            "tags": ["游船", "夜景", "灯光秀", "长江大桥"],
            "rating": 4.5, "address": "武昌区汉阳门码头/江岸区粤汉码头",
            "hours": "每晚 19:00-21:00（多班次）", "transport": "地铁2号线积玉桥站",
            "image": "https://picsum.photos/seed/wuhan-river-cruise/400/300",
            "events": [], "deals": [{"text": "亲子票 150元（1大1小）", "validUntil": "2026-10-31"}],
            "age_min": 3, "age_max": 12, "price": 100, "free": False,
            "indoor": False, "parking": "码头附近停车场", "source": "两江游览"
        },
        {
            "id": next_id + 8, "name": "夜上黄鹤楼", "category": "event",
            "district": "武昌区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "黄鹤楼夜间开放，光影秀和实景演出结合，讲述黄鹤楼历史故事，登楼远眺江城夜景。",
            "tags": ["夜游", "光影秀", "历史文化", "地标"],
            "rating": 4.6, "address": "武昌区黄鹤楼公园",
            "hours": "19:30-22:00（夜间场次）", "transport": "地铁5号线司门口黄鹤楼站",
            "image": "https://picsum.photos/seed/wuhan-yellow-crane/400/300",
            "events": [], "deals": [],
            "age_min": 4, "age_max": 12, "price": 80, "free": False,
            "indoor": False, "parking": "黄鹤楼停车场", "source": "黄鹤楼公园"
        },
        {
            "id": next_id + 9, "name": "昙华林历史文化街区", "category": "event",
            "district": "武昌区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "百年历史文化街区，有文创市集、手作体验、街头艺人表演、特色咖啡馆，文艺氛围浓厚。",
            "tags": ["文化街区", "文创市集", "手作体验", "网红打卡"],
            "rating": 4.4, "address": "武昌区昙华林",
            "hours": "全天开放（店铺10:00-21:00）", "transport": "地铁2号线/7号线螃蟹岬站",
            "image": "https://picsum.photos/seed/wuhan-tanhuain/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "附近停车场有限，建议公共交通", "source": "昙华林"
        },
        {
            "id": next_id + 10, "name": "光谷步行街光影秀", "category": "event",
            "district": "洪山区",
            "seasons": ["summer"],
            "description": "光谷广场灯光音乐喷泉和大型光影秀，步行街夜市汇集各类小吃和文创摊位，年轻活力。",
            "tags": ["光影秀", "音乐喷泉", "夜市", "免费"],
            "rating": 4.2, "address": "洪山区光谷广场/光谷步行街",
            "hours": "19:00-22:00（光影秀）", "transport": "地铁2号线光谷广场站",
            "image": "https://picsum.photos/seed/wuhan-optics-valley/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "光谷国际广场停车场", "source": "光谷步行街"
        },
        # ===== 文化节/季节性活动 =====
        {
            "id": next_id + 11, "name": "武汉东湖樱花节", "category": "event",
            "district": "武昌区",
            "seasons": ["spring"],
            "description": "世界三大樱花之都之一，上万株樱花盛开，夜间灯光赏樱、汉服游园等配套活动。",
            "tags": ["樱花", "赏花", "汉服", "摄影"],
            "rating": 4.8, "address": "武昌区东湖樱花园",
            "hours": "07:00-22:00（3月-4月）", "transport": "地铁8号线梨园站",
            "image": "https://picsum.photos/seed/wuhan-sakura/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 60, "free": False,
            "indoor": False, "parking": "东湖樱花园停车场", "source": "东湖风景区"
        },
        {
            "id": next_id + 12, "name": "武汉荷花节", "category": "event",
            "district": "武昌区",
            "seasons": ["summer"],
            "description": "夏季赏荷盛会，多个公园设展区，有荷花园艺展、摄影比赛、荷花宴美食等。",
            "tags": ["赏花", "荷花", "摄影", "免费"],
            "rating": 4.3, "address": "武昌区东湖磨山荷花园/沙湖公园",
            "hours": "全天（6月-8月）", "transport": "地铁8号线梨园站/4号线东亭站",
            "image": "https://picsum.photos/seed/wuhan-lotus/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "各展区有停车场", "source": "武汉荷花节"
        },
        {
            "id": next_id + 13, "name": "武汉国际赛马节", "category": "event",
            "district": "东西湖区",
            "seasons": ["autumn"],
            "description": "武汉传统赛事，速度赛马、马术表演、嘉年华活动，嘉年华区有儿童活动。",
            "tags": ["赛马", "马术", "嘉年华", "特色赛事"],
            "rating": 4.2, "address": "东西湖区东方马城",
            "hours": "10月 全天", "transport": "地铁6号线金银湖站换乘",
            "image": "https://picsum.photos/seed/wuhan-horse/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 50, "free": False,
            "indoor": False, "parking": "东方马城停车场", "source": "东方马城"
        },
        {
            "id": next_id + 14, "name": "木兰文化旅游节", "category": "event",
            "district": "黄陂区",
            "seasons": ["spring", "autumn"],
            "description": "以木兰文化为主题的大型旅游节，民俗表演、草原露营、格桑花海、滑草射箭等儿童友好项目。",
            "tags": ["木兰文化", "草原露营", "花海", "亲子户外"],
            "rating": 4.4, "address": "黄陂区木兰草原/木兰天池",
            "hours": "08:00-18:00", "transport": "建议自驾，汉口有旅游专线大巴",
            "image": "https://picsum.photos/seed/wuhan-mulan/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 70, "free": False,
            "indoor": False, "parking": "各大景区有停车场", "source": "木兰文化节"
        },
        {
            "id": next_id + 15, "name": "武汉江滩芦苇节", "category": "event",
            "district": "江岸区",
            "seasons": ["autumn"],
            "description": "汉口江滩大片芦苇荡变白，形成「芦花飞雪」壮丽景观，有摄影展和自然教育活动。",
            "tags": ["芦苇", "自然景观", "摄影", "免费"],
            "rating": 4.4, "address": "江岸区汉口江滩三期",
            "hours": "全天（10月-11月）", "transport": "地铁1号线/8号线黄浦路站",
            "image": "https://picsum.photos/seed/wuhan-reed/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "汉口江滩停车场", "source": "汉口江滩"
        },
        {
            "id": next_id + 16, "name": "武汉园博园元宵灯会", "category": "event",
            "district": "硚口区",
            "seasons": ["winter"],
            "description": "大型新春花灯展，自贡彩灯技艺打造，有民俗表演、美食集市、非遗手作体验。",
            "tags": ["灯会", "元宵", "民俗", "非遗体验"],
            "rating": 4.5, "address": "硚口区武汉园博园",
            "hours": "17:00-22:00（春节-元宵期间）", "transport": "地铁7号线园博园站",
            "image": "https://picsum.photos/seed/wuhan-lantern/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 30, "free": False,
            "indoor": False, "parking": "园博园停车场", "source": "武汉园博园"
        },
    ]

    kept.extend(new_events)

    # 按ID排序
    kept.sort(key=lambda x: x["id"])

    save_json("events.json", kept)
    print(f"  ➕ 新增 {len(new_events)} 条活动，保留 {len(kept) - len(new_events)} 条原有活动")
    print(f"  🗑️ 删除 {len(events) - len(kept) + len(new_events)} 条垃圾数据")
    return kept

def _enrich_event(e):
    """丰富爬虫数据的字段"""
    enrichments = {
        31: {  # 2026武汉国际旅游节
            "district": "武昌区",
            "description": "武汉年度旅游盛会，覆盖全市各大景区和文旅场馆，推出旅游惠民政策和特色主题活动。",
            "tags": ["旅游节", "惠民", "主题活动", "全市范围"],
            "address": "武昌区楚河汉街（主会场）",
            "hours": "全天（9月-10月）",
            "transport": "地铁4号线楚河汉街站",
            "rating": 4.3,
            "indoor": False,
            "parking": "楚河汉街停车场",
        },
        32: {  # 武汉城市定向赛亲子专场
            "district": "武昌区",
            "description": "以城市为赛场的亲子定向运动，沿东湖绿道和城市地标设置打卡点，完成挑战获纪念奖牌。",
            "tags": ["定向赛", "亲子运动", "东湖绿道", "户外挑战"],
            "address": "武昌区东湖绿道（起点：梨园广场）",
            "hours": "赛程半天 09:00-12:00",
            "transport": "地铁8号线梨园站",
            "rating": 4.4,
            "indoor": False,
            "parking": "梨园广场停车场",
        },
        33: {  # 江滩露天电影季
            "district": "江岸区",
            "description": "汉口江滩夏季露天电影放映活动，精选亲子动画和经典影片，免费观看。",
            "tags": ["露天电影", "免费活动", "江滩", "亲子"],
            "address": "江岸区汉口江滩三峡石广场",
            "hours": "19:30-21:30（7月-8月 每周末）",
            "transport": "地铁1号线/8号线黄浦路站",
            "rating": 4.2,
            "indoor": False,
            "parking": "汉口江滩停车场",
        },
        34: {  # 武汉非遗文化展
            "district": "武昌区",
            "description": "集中展示武汉非物质文化遗产项目，包括汉绣、剪纸、面塑等传统手工艺，可现场体验。",
            "tags": ["非遗", "手工艺", "文化体验", "展览"],
            "address": "武昌区武汉非遗文化馆",
            "hours": "09:00-17:00",
            "transport": "地铁4号线东亭站",
            "rating": 4.1,
            "parking": "文化馆停车场",
        },
        35: {  # 暑期儿童剧展演
            "district": "江岸区",
            "description": "暑期儿童剧目集中展演，包括童话剧、木偶剧、音乐剧等，多个剧场同步上演。",
            "tags": ["儿童剧", "暑期", "演出", "亲子"],
            "address": "江岸区中南剧场/武汉剧院",
            "hours": "演出日 10:30/15:00/19:30",
            "transport": "地铁1号线/8号线黄浦路站",
            "rating": 4.3,
            "indoor": True,
            "parking": "各剧场有停车场",
        },
        46: {  # 武汉之夏音乐节
            "district": "武昌区",
            "description": "武汉夏季传统音乐盛会，在广场和公园举办多场免费露天音乐会，涵盖流行、民谣等多种风格。",
            "tags": ["音乐节", "免费活动", "露天音乐会", "夏季"],
            "address": "武昌区首义广场/各城区广场",
            "hours": "19:00-21:00（7月-8月）",
            "transport": "地铁4号线首义路站",
            "rating": 4.1,
            "indoor": False,
            "parking": "首义广场停车场",
        },
    }

    if e["id"] in enrichments:
        e.update(enrichments[e["id"]])
    return e

def add_parks():
    """向spots.json添加新的公园"""
    spots = load_json("spots.json")
    max_id = max(s["id"] for s in spots) if spots else 22

    new_parks = [
        {
            "id": max_id + 1, "name": "汉口江滩", "category": "park",
            "district": "江岸区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "亚洲最大滨江公园，有大型沙池、观光小火车、大草坪、放风筝，江滩三期芦苇荡秋季绝美。",
            "tags": ["江滩公园", "沙池", "观光小火车", "放风筝", "大草坪"],
            "rating": 4.7, "address": "江岸区沿江大道",
            "hours": "全天开放", "transport": "地铁1号线/8号线黄浦路站",
            "image": "https://picsum.photos/seed/wuhan-hankou-river/400/300",
            "events": [{"text": "汉口江滩芦苇节", "schedule": "10月-11月"}, {"text": "江滩露天电影季", "schedule": "7月-8月 每周末"}],
            "deals": [], "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "汉口江滩停车场"
        },
        {
            "id": max_id + 2, "name": "堤角公园", "category": "park",
            "district": "江岸区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "苏州园林风格公园，有湖可划船、儿童乐园、竹林和樱花，还有锦鲤池，小朋友很喜欢。",
            "tags": ["江南园林", "儿童乐园", "划船", "樱花", "竹林"],
            "rating": 4.3, "address": "江岸区解放大道2058号",
            "hours": "06:00-22:00", "transport": "地铁1号线堤角站",
            "image": "https://picsum.photos/seed/wuhan-dijiao/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
        {
            "id": max_id + 3, "name": "王家墩公园", "category": "park",
            "district": "江汉区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "原王家墩机场跑道改造的航空主题公园，超大草坪适合奔跑放风筝，有儿童游乐区和运动场地。",
            "tags": ["航空主题", "大草坪", "儿童游乐区", "放风筝"],
            "rating": 4.3, "address": "江汉区青年路与淮海路交汇处",
            "hours": "全天开放", "transport": "地铁2号线/3号线王家墩东站",
            "image": "https://picsum.photos/seed/wuhan-wangjiadun/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
        {
            "id": max_id + 4, "name": "菱角湖公园", "category": "park",
            "district": "江汉区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "城市滨湖公园，环湖步道适合散步推车，有儿童乐园和健身设施，晚饭后遛娃好去处。",
            "tags": ["滨湖步道", "儿童乐园", "夜景", "健身设施"],
            "rating": 4.1, "address": "江汉区菱角湖路",
            "hours": "全天开放", "transport": "地铁2号线/3号线范湖站",
            "image": "https://picsum.photos/seed/wuhan-lingjiao/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "停车不便，建议公共交通"
        },
        {
            "id": max_id + 5, "name": "紫阳公园", "category": "park",
            "district": "武昌区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "2021年改造后成为武昌最美城市公园之一，超大儿童沙池、划船、鸽子广场，周末亲子热门。",
            "tags": ["儿童乐园", "沙池", "划船", "鸽子", "亭台楼阁"],
            "rating": 4.5, "address": "武昌区张之洞路222号",
            "hours": "06:00-22:00", "transport": "地铁4号线/5号线复兴路站",
            "image": "https://picsum.photos/seed/wuhan-ziyang/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "紫阳公园停车场"
        },
        {
            "id": max_id + 6, "name": "四美塘公园", "category": "park",
            "district": "武昌区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "宁静的城市湖泊公园，有儿童游乐区、亲水平台和树荫步道，人少清静，适合低龄幼儿。",
            "tags": ["城市公园", "亲水平台", "儿童游乐", "清静"],
            "rating": 4.0, "address": "武昌区四美塘路",
            "hours": "全天开放", "transport": "地铁5号线余家头站",
            "image": "https://picsum.photos/seed/wuhan-simeitang/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有少量停车位"
        },
        {
            "id": max_id + 7, "name": "月湖公园", "category": "park",
            "district": "汉阳区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "毗邻琴台大剧院的湖景公园，有开阔儿童乐园、大草坪可野餐，文化氛围浓厚，适合平衡车骑行。",
            "tags": ["湖景公园", "儿童乐园", "琴台剧院", "大草坪", "艺术氛围"],
            "rating": 4.4, "address": "汉阳区琴台大道",
            "hours": "全天开放", "transport": "地铁6号线琴台站",
            "image": "https://picsum.photos/seed/wuhan-yuehu/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "琴台大剧院停车场"
        },
        {
            "id": max_id + 8, "name": "汉水公园", "category": "park",
            "district": "汉阳区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "汉江边沿河公园，有儿童乐园、健身步道和大量绿化，人少清静，适合午后休闲遛娃。",
            "tags": ["沿河公园", "儿童乐园", "健身步道", "清静"],
            "rating": 4.0, "address": "汉阳区郭茨口汉江边",
            "hours": "全天开放", "transport": "地铁3号线王家湾站",
            "image": "https://picsum.photos/seed/wuhan-hanshui/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "停车位较少"
        },
        {
            "id": max_id + 9, "name": "和平公园", "category": "park",
            "district": "青山区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "青山最大公园之一，以玫瑰园闻名（5月玫瑰节），有儿童乐园、大草坪和健身设施。",
            "tags": ["玫瑰园", "儿童乐园", "花展", "大草坪"],
            "rating": 4.3, "address": "青山区和平大道与建设五路交汇处",
            "hours": "全天开放", "transport": "地铁5号线和平公园站",
            "image": "https://picsum.photos/seed/wuhan-heping/400/300",
            "events": [{"text": "和平公园玫瑰节", "schedule": "5月"}],
            "deals": [], "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
        {
            "id": max_id + 10, "name": "戴家湖公园", "category": "park",
            "district": "青山区",
            "seasons": ["spring", "autumn"],
            "description": "工业遗址改造的独特公园，有老火车车厢可以攀爬探索（工业记忆主题），大草坪和运动区。",
            "tags": ["工业遗址", "火车主题", "大草坪", "怀旧", "儿童游乐"],
            "rating": 4.2, "address": "青山区建设十路与冶金大道交汇处",
            "hours": "全天开放", "transport": "地铁5号线工人村站",
            "image": "https://picsum.photos/seed/wuhan-daijiahu/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
        {
            "id": max_id + 11, "name": "竹叶海公园", "category": "park",
            "district": "硚口区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "湿地湖泊公园，有亲水步道、儿童乐园和湖景，比园博园清静人少，适合安静遛娃。",
            "tags": ["湿地公园", "儿童乐园", "湖景", "步道"],
            "rating": 4.1, "address": "硚口区长丰大道与竹叶海路交汇处",
            "hours": "全天开放", "transport": "地铁1号线竹叶海站",
            "image": "https://picsum.photos/seed/wuhan-zhuye-sea/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车位"
        },
        {
            "id": max_id + 12, "name": "金银湖湿地公园", "category": "park",
            "district": "东西湖区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "国家城市湿地公园，木质栈道穿行湿地，观鸟天堂，适合亲子骑行和自然科普教育。",
            "tags": ["湿地公园", "观鸟", "栈道", "自然科普", "骑行"],
            "rating": 4.4, "address": "东西湖区金山大道",
            "hours": "全天开放", "transport": "地铁6号线金银湖站",
            "image": "https://picsum.photos/seed/wuhan-yinjin-lake/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
        {
            "id": max_id + 13, "name": "张公堤城市森林公园", "category": "park",
            "district": "东西湖区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "沿百年张公堤修建的线性森林公园，有独立自行车绿道和步行道，贯穿多个公园，亲子骑行圣地。",
            "tags": ["森林公园", "骑行绿道", "城市绿带", "自然风光"],
            "rating": 4.2, "address": "东西湖区张公堤（东起姑嫂树路）",
            "hours": "全天开放", "transport": "地铁2号线金银潭站",
            "image": "https://picsum.photos/seed/wuhan-zhanggong/400/300",
            "events": [], "deals": [],
            "age_min": 3, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有多个入口停车场"
        },
        {
            "id": max_id + 14, "name": "后官湖湿地公园", "category": "park",
            "district": "蔡甸区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "武汉最大湿地公园之一（3186公顷），20+公里环湖绿道可骑行划船，大草坪可露营，适合全家出游一整天。",
            "tags": ["湿地公园", "骑行", "划船", "露营", "大草坪"],
            "rating": 4.4, "address": "蔡甸区彭家山头58号",
            "hours": "08:00-18:00", "transport": "建议自驾，地铁4号线新农站换乘公交",
            "image": "https://picsum.photos/seed/wuhan-houguanhu/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "大型免费停车场"
        },
        {
            "id": max_id + 15, "name": "汤湖公园", "category": "park",
            "district": "蔡甸区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "独特公园内含图书馆、戏院和美术馆！儿童乐园+图书馆故事会+儿童剧，一站式文体亲子体验。",
            "tags": ["图书馆", "戏院", "儿童乐园", "湖景", "美术馆"],
            "rating": 4.3, "address": "蔡甸区（沌口）车城大道与兴华路交汇处",
            "hours": "公园全天开放（图书馆09:00-17:00）", "transport": "建议自驾，地铁3号线沌阳大道站换乘公交",
            "image": "https://picsum.photos/seed/wuhan-tanghu/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "免费停车场"
        },
        {
            "id": max_id + 16, "name": "藏龙岛湿地公园", "category": "park",
            "district": "江夏区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "国家级湿地公园，湿地湖泊和树林由栈道和骑行道连接，可观鸟赏鱼，人少清静的自然探索地。",
            "tags": ["湿地公园", "骑行", "观鸟", "栈道", "自然风光"],
            "rating": 4.2, "address": "江夏区藏龙岛科技园",
            "hours": "全天开放", "transport": "建议自驾，地铁2号线佛祖岭站换乘公交",
            "image": "https://picsum.photos/seed/wuhan-canglong/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
        {
            "id": max_id + 17, "name": "南湖幸福湾公园", "category": "park",
            "district": "洪山区",
            "seasons": ["spring", "summer", "autumn"],
            "description": "南湖之滨的公园，有儿童乐园、大草坪和沿湖步道，南湖片区居民日常遛娃好去处。",
            "tags": ["滨湖公园", "儿童乐园", "大草坪", "步道"],
            "rating": 4.0, "address": "洪山区南湖大道与珞狮南路交汇处",
            "hours": "全天开放", "transport": "地铁8号线文昌路站",
            "image": "https://picsum.photos/seed/wuhan-nanhu/400/300",
            "events": [], "deals": [],
            "age_min": 0, "age_max": 12, "price": 0, "free": True,
            "indoor": False, "parking": "有停车场"
        },
    ]

    spots.extend(new_parks)
    save_json("spots.json", spots)
    print(f"  ➕ 新增 {len(new_parks)} 个公园")
    return spots

if __name__ == "__main__":
    print("🗺️ 添加新公园...")
    add_parks()
    print("\n🎪 清理和丰富活动数据...")
    enrich_events()
    print("\n✅ 数据更新完成！")
