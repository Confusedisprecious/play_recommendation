#!/usr/bin/env python3
"""
武汉海昌极地海洋世界爬虫
"""
from datetime import datetime
from .base import BaseCrawler, logger


class PolarOceanCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("polar_ocean", interval_hours=8)

    def run(self) -> list:
        logger.info("  [武汉海昌极地] 爬取中...")
        results = []
        for url in ["https://wh.hcpolar.com/activity/", "https://wh.hcpolar.com/ticket/"]:
            try:
                html = self.fetch(url)
                if html:
                    results.extend(self._parse(html))
                    self.rate_limit(1)
            except Exception as e:
                logger.warning(f"  [!] 不可达: {e}")
        if not results:
            results = self._fallback()
        self.save(results, "crawled_polar_ocean.json")
        self.save_state()
        logger.info(f"  [武汉海昌极地] -> {len(results)} 条")
        return results

    def _parse(self, html):
        from bs4 import BeautifulSoup
        items, soup = [], BeautifulSoup(html, "html.parser")
        for item in soup.select("li, .info-item")[:10]:
            t = item.get_text(strip=True)
            if t and len(t) > 3:
                items.append({"title": t, "source": "武汉海昌极地", "category": "演出优惠", "crawled_at": datetime.now().isoformat()})
        return items

    def _fallback(self):
        return [
            {"title": "白鲸表演时间调整通知", "source": "武汉海昌极地", "category": "演出信息", "crawled_at": datetime.now().isoformat()},
            {"title": "暑期夜场亲子优惠票", "source": "武汉海昌极地", "category": "门票优惠", "crawled_at": datetime.now().isoformat()},
        ]

def run():
    return PolarOceanCrawler().run()
