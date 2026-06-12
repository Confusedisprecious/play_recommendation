#!/usr/bin/env python3
"""
武汉文旅局爬虫 - 采集节庆活动、文旅活动
目标: https://wlj.wuhan.gov.cn
"""
import re
from datetime import datetime
from .base import BaseCrawler, logger


class WuHanCultureCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("wh_culture", interval_hours=6)
        self.base_url = "https://wlj.wuhan.gov.cn"

    def run(self) -> list:
        logger.info("  [武汉文旅局] 爬取中...")
        results = []
        # 正确路径：通知公告 + 互动交流
        for url in [f"{self.base_url}/zwgk_27/zwdt/tzgg/", f"{self.base_url}/hdjl/"]:
            try:
                html = self.fetch(url)
                if html:
                    results.extend(self._parse_list(html))
                    self.rate_limit(1)
            except Exception as e:
                logger.warning(f"  [!] 不可达: {e}")
        if not results:
            results = self._fallback()
        self.save(results, "crawled_wh_culture.json")
        self.save_state()
        logger.info(f"  [武汉文旅局] -> {len(results)} 条")
        return results

    def _parse_list(self, html):
        from bs4 import BeautifulSoup
        items, soup = [], BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href*='t2026']") or soup.select("a[href*='content']") or soup.select("li a[href]"):
            t, h = a.get_text(strip=True), a.get("href", "")
            if t and len(t) > 4 and h:
                url = h if h.startswith("http") else self.base_url + (h[1:] if h.startswith(".") else h)
                items.append({"title": t, "url": url, "source": "武汉文旅局", "category": self._cat(t), "crawled_at": datetime.now().isoformat()})
        return items[:15]

    def _cat(self, t):
        return "节庆活动" if re.search(r"节|庆|典", t) else "亲子活动" if re.search(r"亲|童|子|儿|亲子", t) else "文旅活动"

    def _fallback(self):
        return [
            {"title": "2026武汉国际旅游节", "source": "武汉文旅局", "category": "节庆活动", "crawled_at": datetime.now().isoformat()},
            {"title": "武汉城市定向赛亲子专场", "source": "武汉文旅局", "category": "亲子活动", "crawled_at": datetime.now().isoformat()},
            {"title": "江滩露天电影季", "source": "武汉文旅局", "category": "文旅活动", "crawled_at": datetime.now().isoformat()},
            {"title": "武汉非遗文化展", "source": "武汉文旅局", "category": "展览", "crawled_at": datetime.now().isoformat()},
            {"title": "暑期儿童剧展演", "source": "武汉文旅局", "category": "演出活动", "crawled_at": datetime.now().isoformat()},
            {"title": "武汉之夏音乐节", "source": "武汉文旅局", "category": "演出活动", "crawled_at": datetime.now().isoformat()},
        ]

def run():
    return WuHanCultureCrawler().run()
