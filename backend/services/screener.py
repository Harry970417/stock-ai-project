import asyncio
import yfinance as yf
import pandas as pd
from typing import Optional
from services.ta_engine import compute_indicators, compute_support_resistance
from services.data_fetcher import fetch_volume_ranking

CONCURRENCY = 8   # 同時抓取的股票數，避免 yfinance rate limit
MIN_SCORE = 3     # 至少達 3 分才進觀察名單
CANDIDATE_POOL = 150  # 從成交量前 150 支篩選


# ── 評分規則 ─────────────────────────────────────────────────────────────────

CRITERIA = [
    {
        "key": "ma_golden",
        "desc": "MA5 > MA20（短期均線多頭排列）",
        "check": lambda ind: (
            _last(ind["ma5"]) is not None and
            _last(ind["ma20"]) is not None and
            _last(ind["ma5"]) > _last(ind["ma20"])
        ),
    },
    {
        "key": "above_ma60",
        "desc": "收盤 > MA60（站上長期均線）",
        "check": lambda ind: (
            _last(ind["close"]) is not None and
            _last(ind["ma60"]) is not None and
            _last(ind["close"]) > _last(ind["ma60"])
        ),
    },
    {
        "key": "rsi_healthy",
        "desc": "RSI 40–68（動能健康，未超買）",
        "check": lambda ind: (
            _last(ind["rsi"]) is not None and
            40 <= _last(ind["rsi"]) <= 68
        ),
    },
    {
        "key": "macd_bullish",
        "desc": "MACD > Signal（多頭動能）",
        "check": lambda ind: (
            _last(ind["macd"]) is not None and
            _last(ind["macd_signal"]) is not None and
            _last(ind["macd"]) > _last(ind["macd_signal"])
        ),
    },
    {
        "key": "volume_surge",
        "desc": "今日成交量 > 20 日均量 1.5 倍（異常放量）",
        "check": lambda ind: _check_volume_surge(ind["volume"]),
    },
]


# ── 主入口 ───────────────────────────────────────────────────────────────────

async def generate_watchlist(max_results: int = 20) -> list:
    """產生隔日觀察名單"""
    candidates = await fetch_volume_ranking("tw", CANDIDATE_POOL)
    if not candidates:
        return []

    semaphore = asyncio.Semaphore(CONCURRENCY)
    tasks = [_score_stock(c, semaphore) for c in candidates]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    scored = [r for r in results if isinstance(r, dict) and r["score"] >= MIN_SCORE]
    scored.sort(key=lambda x: (-x["score"], -x["change_pct"] if x["change_pct"] else 0))
    return scored[:max_results]


# ── 單股評分 ─────────────────────────────────────────────────────────────────

async def _score_stock(candidate: dict, semaphore: asyncio.Semaphore) -> Optional[dict]:
    symbol = candidate["symbol"]
    async with semaphore:
        try:
            df = await asyncio.to_thread(_fetch_history_sync, symbol)
            if df is None or len(df) < 60:
                return None

            ind = compute_indicators(df)
            levels = compute_support_resistance(df)

            matched = [c for c in CRITERIA if c["check"](ind)]
            score = len(matched)

            close = _last(ind["close"])
            if close is None or close <= levels["support"] * 0.97:
                return None

            return {
                "symbol": symbol,
                "name": candidate["name"],
                "close": close,
                "change_pct": candidate.get("change_pct"),
                "score": score,
                "matched_criteria": [c["desc"] for c in matched],
                "rsi": _last(ind["rsi"]),
                "ma5": _last(ind["ma5"]),
                "ma20": _last(ind["ma20"]),
                "macd_signal": ind["signal"],
                "support": levels["support"],
                "resistance": levels["resistance"],
            }
        except Exception:
            return None


# ── 工具函式 ─────────────────────────────────────────────────────────────────

def _fetch_history_sync(symbol: str) -> Optional[pd.DataFrame]:
    """同步版 yfinance 抓取，供 asyncio.to_thread 使用"""
    yf_symbol = symbol if "." in symbol else f"{symbol}.TW"
    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period="3mo")
    if df.empty:
        return None
    df.index = df.index.strftime("%Y-%m-%d")
    return df


def _last(lst: list) -> Optional[float]:
    """取 list 最後一個非 None 值"""
    if not lst:
        return None
    for v in reversed(lst):
        if v is not None:
            return v
    return None


def _check_volume_surge(volumes: list) -> bool:
    """今日成交量是否超過 20 日均量的 1.5 倍"""
    valid = [v for v in volumes if v is not None and v > 0]
    if len(valid) < 21:
        return False
    avg20 = sum(valid[-21:-1]) / 20
    today = valid[-1]
    return today >= avg20 * 1.5
