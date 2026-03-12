"""
tracker.py — 管理 update.json，记录已处理（下载成功或确认无数据）的 APOD 日期

update.json 结构：
{
  "updated_at": "2026-03-12T03:33:00",
  "dates": ["1995-06-16", "1995-06-17", ...]
}

公共 API：
    load(path)             -> set[str]   读取已处理日期集合
    mark_done(path, date)               线程安全地追加一条日期
    get_start_date(path, fallback) -> str  取已记录的最大日期+1天，或返回 fallback
"""

import json
import os
from datetime import datetime, date, timedelta
from threading import Lock

_lock = Lock()


def load(path: str) -> set[str]:
    """读取 update.json，返回已处理日期的集合。"""
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        dates = set(data.get("dates", []))
        # 兼容新的 ranges 格式
        ranges = data.get("ranges", [])
        for r in ranges:
            if len(r) == 2:
                start_dt = datetime.strptime(r[0], "%Y-%m-%d")
                end_dt = datetime.strptime(r[1], "%Y-%m-%d")
                curr = start_dt
                while curr <= end_dt:
                    dates.add(curr.strftime("%Y-%m-%d"))
                    curr += timedelta(days=1)
        return dates
    except Exception:
        return set()


def _write(path: str, dates_set: set[str]) -> None:
    """将日期合并为区间并写回 update.json（不再写入全量 dates 数组）。"""
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except:
            pass

    dates = sorted(dates_set)
    ranges = []
    if dates:
        start = dates[0]
        prev = dates[0]
        for i in range(1, len(dates)):
            curr = dates[i]
            prev_dt = datetime.strptime(prev, "%Y-%m-%d")
            curr_dt = datetime.strptime(curr, "%Y-%m-%d")
            if curr_dt - prev_dt > timedelta(days=1):
                ranges.append([start, prev])
                start = curr
            prev = curr
        ranges.append([start, prev])

    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "ranges": ranges,
        "files": existing.get("files", {})  # 保持现有的文件映射
    }
    
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def mark_done(path: str, date_str: str) -> None:
    """线程安全地将 date_str 追加到 update.json。"""
    with _lock:
        dates = load(path)
        if date_str in dates:
            return
        dates.add(date_str)
        _write(path, dates)


def get_next_start(path: str, fallback: str) -> str:
    """返回增量起点。"""
    dates = load(path)
    if not dates:
        return fallback
    latest = max(dates)
    next_day = (datetime.strptime(latest, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    return next_day
