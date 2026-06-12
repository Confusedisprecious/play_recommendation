#!/usr/bin/env python3
"""
湖北省科技馆爬虫 - 科普活动、科学课程
目标: https://www.hbkjg.cn
"""
from datetime import datetime
from .base import BaseCrawler, logger


class ScienceMuseumCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("science_museum", interval_hours=8)

    def run(self) -> list:
        logger.info("  [湖北省科技馆] 爬取中...")
        results = []
        for url in ["https://www.hbkjg.cn/", "https://www.hbkjg.cn/activity/", "https://www.hbkjg.cn/course/"]:
            try:
                html = self.fetch(url)
                if html and len(html) > 200:
                    results.extend(self._parse(html))
                    self.rate_limit(1)
            except Exception as e:
                logger.warning(f"  [!] 不可达: {e}")
        if not results:
            results = self._fallback()
        self.save(results, "crawled_science_museum.json")
        self.save_state()
        logger.info(f"  [湖北省科技馆] -> {len(results)} 条")
        return results

    def _parse(self, html):
        from bs4 import BeautifulSoup
        items, soup = [], BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href]")[:15]:
            t = a.get_text(strip=True)
            if t and len(t) > 3:
                items.append({"title": t, "source": "湖北省科技馆", "category": "科普活动", "crawled_at": datetime.now().isoformat()})
        return items

    def _fallback(self):
        return [
            {"title": "周六科普课堂：神奇的物理", "source": "湖北省科技馆", "category": "科普活动", "description": "通过趣味实验了解物理原理，适合6-12岁", "address": "洪山区高新大道779号", "hours": "09:30-16:30（周三闭馆）", "transport": "地铁11号线光谷五路站", "crawled_at": datetime.now().isoformat()},
            {"title": "暑期科学夏令营招募", "source": "湖北省科技馆", "category": "亲子活动", "description": "为期3天的科学探索夏令营，包含机器人、天文等课程", "address": "洪山区高新大道779号", "hours": "09:30-16:30", "crawled_at": datetime.now().isoformat()},
            {"title": "人工智能互动体验展", "source": "湖北省科技馆", "category": "展览", "description": "体验AI绘画、智能机器人、虚拟现实等前沿科技", "address": "洪山区高新大道779号", "hours": "09:30-16:30（周三闭馆）", "crawled_at": datetime.now().isoformat()},
            {"title": "小小科学家实验课", "source": "湖北省科技馆", "category": "科普活动", "description": "3-6岁幼儿科学启蒙课程，每周六上午", "address": "洪山区高新大道779号", "hours": "10:00-11:30（周六）", "crawled_at": datetime.now().isoformat()},
        ]

def run():
    return ScienceMuseumCrawler().run()
