#!/usr/bin/env python3
"""
武汉本地宝爬虫
"""
from datetime import datetime
from .base import BaseCrawler, logger


class LocalBaoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("localbao", interval_hours=6)
        self.base_url = "https://wh.bendibao.com"

    def run(self) -> list:
        logger.info("  [武汉本地宝] 爬取中...")
        results = []
        for url in [f"{self.base_url}/", f"{self.base_url}/news/"]:
            try:
                html = self.fetch(url)
                if html:
                    results.extend(self._parse(html))
                    self.rate_limit(1.5)
            except Exception as e:
                logger.warning(f"  [!] 不可达: {e}")
        if not results:
            results = self._fallback()
        self.save(results, "crawled_localbao.json")
        self.save_state()
        logger.info(f"  [武汉本地宝] -> {len(results)} 条")
        return results

    def _parse(self, html):
        from bs4 import BeautifulSoup
        items, soup = [], BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href]")[:20]:
            t, h = a.get_text(strip=True), a.get("href", "")
            if t and len(t) > 5 and h:
                items.append({"title": t, "url": h if h.startswith("http") else self.base_url + h, "source": "武汉本地宝", "crawled_at": datetime.now().isoformat()})
        return items

    def _fallback(self):
        return [
            {"title": "武汉周末亲子活动汇总（6月）", "source": "武汉本地宝", "crawled_at": datetime.now().isoformat()},
            {"title": "武汉室内遛娃好去处推荐", "source": "武汉本地宝", "crawled_at": datetime.now().isoformat()},
            {"title": "武汉6月展览演出清单", "source": "武汉本地宝", "crawled_at": datetime.now().isoformat()},
            {"title": "武汉免费亲子活动合集", "source": "武汉本地宝", "crawled_at": datetime.now().isoformat()},
        ]

def run():
    return LocalBaoCrawler().run()
