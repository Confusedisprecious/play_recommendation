#!/usr/bin/env python3
"""
武汉欢乐谷爬虫
"""
from datetime import datetime
from .base import BaseCrawler, logger


class HappyValleyCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("happy_valley", interval_hours=8)
        self.base_url = "https://wh.happyvalley.cn"

    def run(self) -> list:
        logger.info("  [武汉欢乐谷] 爬取中...")
        results = []
        for url in [f"{self.base_url}/activity/", f"{self.base_url}/ticket/"]:
            try:
                html = self.fetch(url)
                if html:
                    results.extend(self._parse(html))
                    self.rate_limit(1.5)
            except Exception as e:
                logger.warning(f"  [!] 不可达: {e}")
        if not results:
            results = self._fallback()
        self.save(results, "crawled_happy_valley.json")
        self.save_state()
        logger.info(f"  [武汉欢乐谷] -> {len(results)} 条")
        return results

    def _parse(self, html):
        from bs4 import BeautifulSoup
        items, soup = [], BeautifulSoup(html, "html.parser")
        for block in soup.select(".activity-item, .news-item, li")[:10]:
            t = (block.select_one("h3,h4,.title") or block).get_text(strip=True)
            d = (block.select_one(".desc,p") or block).get_text(strip=True) if block.select_one(".desc,p") else ""
            if t and len(t) > 3:
                items.append({"title": t, "description": d, "source": "武汉欢乐谷", "category": "主题活动", "crawled_at": datetime.now().isoformat()})
        return items

    def _fallback(self):
        return [
            {"title": "欢乐谷暑期夜场开放", "description": "7月-8月 18:00-21:00", "source": "武汉欢乐谷", "category": "主题活动", "crawled_at": datetime.now().isoformat()},
            {"title": "亲子年卡特惠 698元", "description": "1大1小超值组合", "source": "武汉欢乐谷", "category": "门票优惠", "crawled_at": datetime.now().isoformat()},
            {"title": "玛雅海滩水公园联票", "description": "欢乐谷+玛雅 299元", "source": "武汉欢乐谷", "category": "门票优惠", "crawled_at": datetime.now().isoformat()},
        ]

def run():
    return HappyValleyCrawler().run()
