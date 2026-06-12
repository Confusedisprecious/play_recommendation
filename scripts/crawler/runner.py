#!/usr/bin/env python3
"""
爬虫统一调度器 - 按优先级顺序执行所有爬虫
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))


def run_all_crawlers():
    """按顺序执行所有爬虫"""
    print("\n" + "=" * 50)
    print("  武汉亲子游玩 - 数据爬取")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    results = {}

    # 一级源 - 官方
    crawlers = [
        ("wh_culture", "武汉文旅局"),
        ("museum", "湖北省博物馆"),
        ("science_museum", "湖北省科技馆"),
        ("happy_valley", "武汉欢乐谷"),
        ("polar_ocean", "武汉海昌极地"),
    ]

    for module_name, display_name in crawlers:
        try:
            module = __import__(f"crawler.{module_name}", fromlist=["run"])
            data = module.run()
            results[module_name] = len(data)
            print(f"  ✔ {display_name}: {len(data)} 条\n")
        except Exception as e:
            logger.warning(f"  ⚠ {display_name} 爬取失败: {e}\n")

    # 二级源
    try:
        from crawler import localbao
        data = localbao.run()
        results["localbao"] = len(data)
        print(f"  ✔ 武汉本地宝: {len(data)} 条\n")
    except Exception as e:
        logger.warning(f"  ⚠ 武汉本地宝 爬取失败: {e}\n")

    # 热点发现
    try:
        from crawler import hot_events
        data = hot_events.run()
        results["hot_events"] = len(data)
        print(f"  ✔ 热点发现: {len(data)} 条\n")
    except Exception as e:
        logger.warning(f"  ⚠ 热点发现 失败: {e}\n")

    # 汇总
    total = sum(results.values())
    print("-" * 50)
    print(f"  汇总: {total} 条数据 (来自 {len(results)} 个源)")
    print("=" * 50)

    return results


if __name__ == "__main__":
    run_all_crawlers()
