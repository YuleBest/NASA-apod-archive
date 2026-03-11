"""
config.py — 读取 config.yaml，提供全局配置
优先级：config.yaml > 内置默认值；CLI 参数 > config.yaml
"""

import os
from datetime import date, timedelta

import yaml

_DEFAULTS: dict = {
    "api_key_file":     "api-key.txt",
    "data_dir":         "data",
    "dist_dir":         "dist",
    "update_file":      "update.json",
    "workers":          4,
    "apod_start":       "1995-06-16",
    "api_rate_limit":   1000,
    "max_retry_rounds": 3,
    "start_date":       "2024-01-01",
    "end_date":         "2026-03-10",
}

_CONFIG_FILE = "config.yaml"
_cache: dict | None = None


def _resolve_date(value) -> str:
    """将整数偏移量转换为 ISO 日期字符串。

    - 若 value 为 int（或可转成 int 的字符串且 ≤ 0），视为相对今天的天数偏移：
      0 → 今天，-1 → 昨天，-2 → 前天，以此类推。
    - 否则原样返回字符串。
    """
    if isinstance(value, int):
        return (date.today() + timedelta(days=value)).isoformat()
    # 也兼容 YAML 中带引号写成 "-1" 这样的字符串
    try:
        offset = int(value)
        if offset <= 0:
            return (date.today() + timedelta(days=offset)).isoformat()
    except (ValueError, TypeError):
        pass
    return str(value)


def load() -> dict:
    """加载并缓存配置，返回最终配置字典。"""
    global _cache
    if _cache is not None:
        return _cache

    cfg = dict(_DEFAULTS)
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                overrides = yaml.safe_load(f) or {}
            cfg.update(overrides)
        except Exception as e:
            print(f"[config] 读取 {_CONFIG_FILE} 失败，使用默认值：{e}")

    # 将整数偏移转换为实际日期
    for key in ("start_date", "end_date"):
        cfg[key] = _resolve_date(cfg[key])

    _cache = cfg
    return cfg
