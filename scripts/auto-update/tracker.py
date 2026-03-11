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
    """读取 update.json，返回已处理日期的集合。文件不存在时返回空集合。"""
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("dates", []))
    except Exception:
        return set()


def _write(path: str, dates: set[str]) -> None:
    """将日期集合写回 update.json（已持有锁时调用）。"""
    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "dates": sorted(dates),
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # 原子替换，避免写到一半时进程崩溃


def mark_done(path: str, date_str: str) -> None:
    """线程安全地将 date_str 追加到 update.json。"""
    with _lock:
        dates = load(path)
        if date_str in dates:
            return
        dates.add(date_str)
        _write(path, dates)


def get_next_start(path: str, fallback: str) -> str:
    """
    返回已记录的最大日期 + 1 天（即增量起点）。
    若 update.json 不存在或为空，返回 fallback。
    """
    dates = load(path)
    if not dates:
        return fallback
    latest = max(dates)
    next_day = (datetime.strptime(latest, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    return next_day
