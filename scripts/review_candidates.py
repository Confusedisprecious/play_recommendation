#!/usr/bin/env python3
"""人工核验 social_candidates.json 中的待审核条目。

用法：
  python scripts/review_candidates.py --list                 # 列出待审核条目
  python scripts/review_candidates.py --approve --days 14    # 核验最近 14 天内的全部待审核条目
  python scripts/review_candidates.py --approve --keyword 遛娃 --days 7   # 只核验标题含关键词的

核验（pending -> reviewed）后立即重建 social_feed.json，下一轮定时更新也会沿用该状态。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
CANDIDATES_PATH = BASE_DIR / "data" / "social_candidates.json"
LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")

try:
    from social_ingest import build_feed
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from social_ingest import build_feed


def load_candidates() -> dict:
    return json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))


def save_candidates(payload: dict) -> None:
    CANDIDATES_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def list_pending(payload: dict) -> list[dict]:
    return [i for i in payload.get("items", []) if i.get("review_status") == "pending"]


def main() -> None:
    parser = argparse.ArgumentParser(description="核验待审核的社交/视频候选")
    parser.add_argument("--list", action="store_true", help="列出待审核条目")
    parser.add_argument("--approve", action="store_true", help="把符合条件的待审核条目标记为 reviewed")
    parser.add_argument("--days", type=int, default=14, help="只处理最近 N 天内发布的条目（默认 14）")
    parser.add_argument("--keyword", default="", help="只处理标题/摘要包含该关键词的条目")
    args = parser.parse_args()

    payload = load_candidates()
    pending = list_pending(payload)
    cutoff = (datetime.now(LOCAL_TIMEZONE) - timedelta(days=args.days)).date().isoformat()

    if args.list or not args.approve:
        print(f"待审核条目：{len(pending)} 条（全部候选 {len(payload.get('items', []))} 条）")
        for item in pending:
            print(f"  [{item.get('published_at', '????-??-??')}] {item.get('platform', ''):12s} "
                  f"{item.get('title', '')[:44]}")
            print(f"      {item.get('url', '')[:96]}")
        if not args.approve:
            print("\n核验：python scripts/review_candidates.py --approve --days 14")
        return

    keyword = args.keyword.strip().lower()
    approved = 0
    for item in payload.get("items", []):
        if item.get("review_status") != "pending":
            continue
        published = str(item.get("published_at", ""))
        if published and published < cutoff:
            continue
        if keyword:
            haystack = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            if keyword not in haystack:
                continue
        item["review_status"] = "reviewed"
        item["reviewed_at"] = datetime.now(LOCAL_TIMEZONE).isoformat(timespec="seconds")
        approved += 1
        print(f"  ✔ reviewed: [{published}] {item.get('title', '')[:44]}")

    if approved:
        save_candidates(payload)
        print(f"\n已核验 {approved} 条，重建 social_feed…")
        build_feed()
        print("完成。")
    else:
        print("没有符合条件的待审核条目。")


if __name__ == "__main__":
    main()
