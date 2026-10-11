#!/usr/bin/env python3
"""抓取武汉实时天气与 3 天预报，生成 data/weather.json。

数据来源 Open-Meteo 免费接口（无需 API key，非商业使用免费），
供前端在首屏展示天气并根据降雨/气温给出室内外建议。
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "weather.json"
LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")

# 武汉市中心坐标
LATITUDE, LONGITUDE = 30.5928, 114.3055

API_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    + urllib.parse.urlencode(
        {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Asia/Shanghai",
            "forecast_days": 3,
        }
    )
)

WEATHER_LABELS = {
    0: "晴", 1: "基本晴", 2: "局部多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨", 56: "冻毛毛雨", 57: "冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨", 66: "冻雨", 67: "冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "阵雨", 81: "阵雨", 82: "强阵雨", 85: "阵雪", 86: "阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "雷阵雨伴冰雹",
}

RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
SNOW_CODES = {71, 73, 75, 77, 85, 86}


def weather_label(code) -> str:
    try:
        return WEATHER_LABELS.get(int(code), "天气待确认")
    except (TypeError, ValueError):
        return "天气待确认"


def build_advice(current_code, days) -> dict:
    """根据今天与明天的降雨概率、气温给出室内外建议。"""
    if not days:
        return {"scene": "indoor", "headline": "天气数据待确认", "detail": "可先看看室内场馆。"}
    today = days[0]
    rain_prob = int(today.get("rain_prob") or 0)
    t_max = today.get("t_max")
    t_min = today.get("t_min")
    code = today.get("code")

    rainy = rain_prob >= 40 or code in RAIN_CODES or code in SNOW_CODES
    hot = isinstance(t_max, (int, float)) and t_max >= 33
    cold = isinstance(t_min, (int, float)) and t_min <= 3

    if rainy:
        return {
            "scene": "indoor",
            "headline": f"今天降水概率 {rain_prob}%，优先室内场馆",
            "detail": "雨具备好；若午后转晴，绿道散步也可以安排。",
        }
    if hot:
        return {
            "scene": "indoor",
            "headline": f"今天最高 {round(t_max)}°C，避开午间暴晒",
            "detail": "早晨或傍晚再安排户外，中午留给有空调的场馆。",
        }
    if cold:
        return {
            "scene": "indoor",
            "headline": f"今天最低仅 {round(t_min)}°C，注意保暖",
            "detail": "户外活动选在午后最暖的时段，多带一件外套。",
        }
    scene_hint = "户外放电正合适" if rain_prob < 30 else "户外出行问题不大"
    tomorrow_rain = len(days) > 1 and (int(days[1].get("rain_prob") or 0) >= 40 or days[1].get("code") in RAIN_CODES)
    detail = "公园、绿道和骑行都适合安排。" if not tomorrow_rain else "明天降雨概率较高，户外活动尽量安排在今天。"
    return {
        "scene": "outdoor",
        "headline": f"今天{weather_label(code)} {round(t_max)}°C，{scene_hint}",
        "detail": detail,
    }


def fetch_weather() -> dict:
    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "WuhanFamilyGuide/1.0 (weather-step)"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)

    daily = payload.get("daily", {})
    dates = daily.get("time", []) or []
    days = []
    for index, date in enumerate(dates):
        days.append(
            {
                "date": date,
                "code": daily.get("weather_code", [None] * len(dates))[index],
                "label": weather_label(daily.get("weather_code", [None] * len(dates))[index]),
                "t_max": daily.get("temperature_2m_max", [None] * len(dates))[index],
                "t_min": daily.get("temperature_2m_min", [None] * len(dates))[index],
                "rain_prob": daily.get("precipitation_probability_max", [None] * len(dates))[index],
            }
        )

    current = payload.get("current", {}) or {}
    weather = {
        "city": "武汉",
        "source": "Open-Meteo",
        "fetched_at": datetime.now(LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M"),
        "current": {
            "temperature": current.get("temperature_2m"),
            "code": current.get("weather_code"),
            "label": weather_label(current.get("weather_code")),
        },
        "days": days,
        "advice": build_advice(current.get("weather_code"), days),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(weather, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  ✔ weather.json saved ({weather['current']['label']} {weather['current']['temperature']}°C)")
    return weather


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        fetch_weather()
    except Exception as error:
        print(f"  ⚠ 天气获取失败: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
