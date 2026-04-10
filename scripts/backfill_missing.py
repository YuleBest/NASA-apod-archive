#!/usr/bin/env python3
"""
backfill_missing.py — 补全缺失的 NASA APOD 数据

缺失范围：
  - 2026-03-01 ~ 2026-03-30
  - 2026-04-01 ~ 2026-04-05

用法：
    # 使用 auto-update/api-key.txt 中的 Key（默认）
    python scripts/backfill_missing.py

    # 或直接传入 Key
    python scripts/backfill_missing.py --api-key YOUR_KEY
"""

import argparse
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent
DB_DIR = SCRIPT_DIR.parent / "public" / "database"
API_KEY_FILE = SCRIPT_DIR / "auto-update" / "api-key.txt"

STRIP_FIELDS = {"media_type", "service_version"}

# 需要补全的日期范围
MISSING_RANGES = [
    ("2026-03-01", "2026-03-30"),
    ("2026-04-01", "2026-04-05"),
]


def load_api_key(cli_key: str | None) -> str:
    if cli_key:
        return cli_key.strip()
    if API_KEY_FILE.exists():
        key = API_KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key
    raise FileNotFoundError(
        f"找不到 API Key。请在 {API_KEY_FILE} 中写入 Key，或通过 --api-key 传入。"
    )


def fetch_apod_range(api_key: str, start_date: str, end_date: str) -> list[dict]:
    """使用 NASA APOD 批量端点获取指定日期区间的数据。"""
    url = (
        "https://api.nasa.gov/planetary/apod"
        f"?api_key={api_key}"
        f"&start_date={start_date}"
        f"&end_date={end_date}"
        f"&thumbs=false"
    )
    print(f"  请求 {start_date} 至 {end_date} ...")
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"  网络错误 (第 {attempt + 1} 次): {e}")
            time.sleep(5)
            continue

        if resp.status_code == 200:
            data = resp.json()
            print(f"  返回 {len(data)} 条记录")
            return data
        elif resp.status_code == 429:
            print("  触发速率限制，等待 60 秒后重试...")
            time.sleep(60)
        else:
            print(f"  HTTP {resp.status_code}，跳过")
            return []
    return []


def load_existing_month(month_key: str) -> dict[str, dict]:
    """从 public/database/ 中读取该月的已有数据。"""
    entries: dict[str, dict] = {}
    for f in DB_DIR.iterdir():
        if (
            f.name.startswith(month_key)
            and f.name.endswith(".json")
            and f.name not in ("update.json", "search.json")
        ):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for entry in data:
                    d = entry.get("date")
                    if d:
                        entries[d] = entry
            except Exception as e:
                print(f"  警告：读取 {f.name} 失败: {e}")
    return entries


def write_month(month_key: str, entries_by_date: dict[str, dict]) -> None:
    """将合并后的月份数据写入正确的文件，并删除旧的分片文件。"""
    entries = sorted(entries_by_date.values(), key=lambda e: e.get("date", ""))

    # 清理无关字段
    for entry in entries:
        for field in STRIP_FIELDS:
            entry.pop(field, None)

    filename = f"{month_key}.json"
    out_path = DB_DIR / filename

    # 删除同月份的旧分片文件（除了即将写入的目标文件）
    for old_f in DB_DIR.iterdir():
        if (
            old_f.name.startswith(month_key)
            and old_f.name.endswith(".json")
            and old_f.name != filename
            and old_f.name not in ("update.json", "search.json")
        ):
            print(f"  删除旧文件: {old_f.name}")
            old_f.unlink()

    out_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  写入: {filename}（{len(entries)} 条）")


def rebuild_index() -> None:
    """重建 search.json 和 update.json。"""
    import glob

    search_path = DB_DIR / "search.json"
    update_path = DB_DIR / "update.json"

    monthly_files = sorted(
        glob.glob(str(DB_DIR / "[0-9][0-9][0-9][0-9]-[0-9][0-9]*.json"))
    )
    print(f"\n重建索引，共 {len(monthly_files)} 个月份文件...")

    search_data = []
    all_dates: set[str] = set()
    month_mapping: dict[str, str] = {}

    for fpath in monthly_files:
        fname = os.path.basename(fpath)
        month_key = fname[:7]
        month_mapping[month_key] = fname

        try:
            entries = json.loads(Path(fpath).read_text(encoding="utf-8"))
            for entry in entries:
                d = entry.get("date")
                if not d:
                    continue
                status = entry.get("http_status")
                is_invalid = entry.get("no_data") and status in (400, 429)
                if not is_invalid:
                    all_dates.add(d)
                if not entry.get("no_data") and entry.get("title"):
                    search_data.append(
                        {
                            "d": entry.get("date"),
                            "t": entry.get("title"),
                            "e": entry.get("explanation", ""),
                        }
                    )
        except Exception as e:
            print(f"  读取 {fname} 失败: {e}")

    # 写入 search.json
    search_data.sort(key=lambda x: x["d"], reverse=True)
    search_path.write_text(
        json.dumps(search_data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"search.json：{len(search_data)} 条")

    # 写入 update.json（区间格式）
    sorted_dates = sorted(all_dates)
    ranges: list[list[str]] = []
    if sorted_dates:
        start = sorted_dates[0]
        prev = sorted_dates[0]
        for i in range(1, len(sorted_dates)):
            curr = sorted_dates[i]
            prev_dt = datetime.strptime(prev, "%Y-%m-%d")
            curr_dt = datetime.strptime(curr, "%Y-%m-%d")
            if curr_dt - prev_dt > timedelta(days=1):
                ranges.append([start, prev])
                start = curr
            prev = curr
        ranges.append([start, prev])

    update_payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "ranges": ranges,
        "files": month_mapping,
    }
    update_path.write_text(
        json.dumps(update_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"update.json：{len(ranges)} 个区间，{len(month_mapping)} 个月份文件")


def main() -> None:
    parser = argparse.ArgumentParser(description="NASA APOD 缺失数据补全")
    parser.add_argument("--api-key", help="NASA API Key（默认读取 auto-update/api-key.txt）")
    args = parser.parse_args()

    print("=" * 60)
    print("NASA APOD 缺失数据补全脚本")
    print("=" * 60)

    api_key = load_api_key(args.api_key)

    # 收集所有需要新增的条目
    all_new: dict[str, dict] = {}
    for start_str, end_str in MISSING_RANGES:
        print(f"\n[获取] {start_str} 至 {end_str}")
        entries = fetch_apod_range(api_key, start_str, end_str)
        for entry in entries:
            d = entry.get("date")
            if d:
                all_new[d] = entry
        time.sleep(1)  # 简单保护，避免立即触发速率限制

    print(f"\n共获取 {len(all_new)} 条新数据")

    # 按月分组
    by_month: dict[str, dict[str, dict]] = {}
    for date_str, entry in all_new.items():
        mk = date_str[:7]
        by_month.setdefault(mk, {})[date_str] = entry

    # 读取现有数据并合并写入
    for month_key in sorted(by_month.keys()):
        print(f"\n[处理] {month_key}")
        existing = load_existing_month(month_key)
        print(f"  已有 {len(existing)} 条")
        merged = {**existing, **by_month[month_key]}  # 新数据覆盖旧数据
        print(f"  合并后 {len(merged)} 条")
        write_month(month_key, merged)

    rebuild_index()

    print("\n[完成] 请将更改提交到 git。")


if __name__ == "__main__":
    main()
