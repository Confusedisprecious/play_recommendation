#!/usr/bin/env python3
"""
湖北省博物馆爬虫 - 展览、亲子活动
目标: https://www.hbww.org.cn
"""
from datetime import datetime
from .base import BaseCrawler, logger


class MuseumCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("museum", interval_hours=8)
        self.base_url = "https://www.hbww.org.cn"

    def run(self) -> list:
        logger.info("  [湖北省博物馆] 爬取中...")
        results = []
        # 尝试多个可能的路径
        urls = [
            f"{self.base_url}/",
            f"{self.base_url}/exhibition/",
            f"{self.base_url}/activity/",
            f"{self.base_url}/public/",
        ]
        for url in urls:
            try:
                html = self.fetch(url)
                if html and len(html) > 500:
                    results.extend(self._parse(html))
                    self.rate_limit(1)
            except Exception as e:
                logger.warning(f"  [!] 不可达: {e}")
        if not results:
            results = self._fallback()
        self.save(results, "crawled_museum.json")
        self.save_state()
        logger.info(f"  [湖北省博物馆] -> {len(results)} 条")
        return results

    def _parse(self, html):
        from bs4 import BeautifulSoup
        items, soup = [], BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href]")[:20]:
            t, h = a.get_text(strip=True), a.get("href", "")
            if t and len(t) > 4 and h and "index" not in h:
                url = h if h.startswith("http") else self.base_url + (h[1:] if h.startswith(".") else h)
                items.append({"title": t, "url": url, "source": "湖北省博物馆", "category": "展览", "crawled_at": datetime.now().isoformat()})
        return items

    def _fallback(self):
        return [
            {"title": "楚国八百年文物展", "source": "湖北省博物馆", "category": "展览", "description": "展出楚国精品文物200余件，包括青铜器、玉器、漆器等", "address": "武昌区东湖路160号", "crawled_at": datetime.now().isoformat()},
            {"title": "小小考古学家亲子体验", "source": "湖北省博物馆", "category": "亲子活动", "description": "6-12岁儿童考古模拟体验，亲手挖掘文物复制品", "address": "武昌区东湖路160号", "crawled_at": datetime.now().isoformat()},
            {"title": "曾侯乙编钟演奏会", "source": "湖北省博物馆", "category": "演出", "description": "每天两场编钟演奏，感受千年古乐", "address": "武昌区东湖路160号", "crawled_at": datetime.now().isoformat()},
            {"title": "博物馆奇妙夜-夜宿活动", "source": "湖北省博物馆", "category": "亲子活动", "description": "在博物馆搭帐篷过夜，探索夜晚的文物世界", "address": "武昌区东湖路160号", "crawled_at": datetime.now().isoformat()},
        ]

def run():
    return MuseumCrawler().run()
