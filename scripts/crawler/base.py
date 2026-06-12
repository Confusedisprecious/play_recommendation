#!/usr/bin/env python3
"""
爬虫基类 - 提供通用爬取功能
"""
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class BaseCrawler:
    """爬虫基类"""

    def __init__(self, name: str, interval_hours: int = 6):
        self.name = name
        self.interval_hours = interval_hours
        self.session = None
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/json,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def should_run(self) -> bool:
        """检查是否应该运行（基于间隔时间）"""
        state_file = DATA_DIR / f".crawler_{self.name}.json"
        if not state_file.exists():
            return True
        try:
            with open(state_file, encoding="utf-8") as f:
                state = json.load(f)
            last_run = datetime.fromisoformat(state.get("last_run", "2000-01-01"))
            hours_since = (datetime.now() - last_run).total_seconds() / 3600
            return hours_since >= self.interval_hours
        except Exception:
            return True

    def save_state(self):
        """保存爬取状态"""
        state_file = DATA_DIR / f".crawler_{self.name}.json"
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump({"last_run": datetime.now().isoformat(), "name": self.name}, f)
        except Exception as e:
            logger.warning(f"  [!] 保存状态失败: {e}")

    def fetch(self, url: str, timeout: int = 30) -> Optional[str]:
        """通用 HTTP GET 请求"""
        try:
            import httpx
            with httpx.Client(headers=self.headers, timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return resp.text
        except ImportError:
            logger.warning("  [!] httpx 未安装，尝试 urllib")
            try:
                from urllib.request import Request, urlopen
                req = Request(url, headers=self.headers)
                with urlopen(req, timeout=timeout) as resp:
                    return resp.read().decode("utf-8", errors="replace")
            except Exception as e:
                logger.error(f"  [!] urllib 请求失败: {e}")
                return None
        except Exception as e:
            logger.error(f"  [!] 请求失败 {url}: {e}")
            return None

    def fetch_json(self, url: str, timeout: int = 30) -> Optional[dict]:
        """请求 JSON API"""
        text = self.fetch(url, timeout)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.warning(f"  [!] JSON 解析失败: {e}")
        return None

    def parse(self, html: str) -> list:
        """子类实现：解析 HTML 提取数据"""
        raise NotImplementedError

    def run(self) -> list:
        """子类实现：执行爬取"""
        raise NotImplementedError

    def save(self, data: list, filename: str):
        """保存数据到 JSON 文件"""
        path = DATA_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"  ✔ 已保存 {len(data)} 条数据到 {filename}")

    def rate_limit(self, seconds: float = 1.0):
        """请求间隔限制"""
        time.sleep(seconds)
