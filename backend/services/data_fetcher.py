import httpx
import yfinance as yf
import pandas as pd
from typing import Optional

TWSE_STOCK_DAY_ALL = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY_ALL?response=json"


async def fetch_quote(symbol: str) -> Optional[dict]:
    """抓取個股即時報價"""
    ticker = yf.Ticker(_to_yf_symbol(symbol))
    info = ticker.fast_info
    try:
        return {
            "symbol": symbol,
            "price": info.last_price,
            "open": info.open,
            "high": info.day_high,
            "low": info.day_low,
            "volume": info.last_volume,
            "previous_close": info.previous_close,
            "change_pct": round((info.last_price - info.previous_close) / info.previous_close * 100, 2),
        }
    except Exception:
        return None


async def fetch_history(symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
    """抓取個股歷史 OHLCV"""
    ticker = yf.Ticker(_to_yf_symbol(symbol))
    df = ticker.history(period=period)
    if df.empty:
        return None
    df.index = df.index.strftime("%Y-%m-%d")
    return df


async def fetch_volume_ranking(market: str = "tw", top: int = 20) -> list:
    """取得成交量排行，依成交金額由大到小排序"""
    if market != "tw":
        return []
    return await _fetch_twse_volume_ranking(top)


async def _fetch_twse_volume_ranking(top: int) -> list:
    """呼叫 TWSE STOCK_DAY_ALL，解析後依成交金額排行"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(TWSE_STOCK_DAY_ALL)
        resp.raise_for_status()
        data = resp.json()

    if data.get("stat") != "OK":
        return []

    rows = []
    for row in data.get("data", []):
        try:
            symbol   = row[0].strip()
            name     = row[1].strip()
            shares   = _parse_num(row[2])   # 成交股數
            value    = _parse_num(row[3])   # 成交金額（排序依據）
            open_p   = _parse_price(row[4])
            high     = _parse_price(row[5])
            low      = _parse_price(row[6])
            close    = _parse_price(row[7])
            change   = _parse_price(row[8])  # 漲跌金額（含正負號）

            if close is None or close == 0 or value is None:
                continue

            prev_close = close - change if change is not None else None
            change_pct = round(change / prev_close * 100, 2) if prev_close and prev_close != 0 else None

            rows.append({
                "symbol": symbol,
                "name": name,
                "close": close,
                "open": open_p,
                "high": high,
                "low": low,
                "change": change,
                "change_pct": change_pct,
                "volume_shares": int(shares) if shares else None,
                "volume_value": int(value) if value else None,
            })
        except (IndexError, ValueError):
            continue

    rows.sort(key=lambda x: x["volume_value"] or 0, reverse=True)
    return rows[:top]


def _parse_num(s: str) -> Optional[float]:
    """移除千分位逗號後轉 float"""
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_price(s: str) -> Optional[float]:
    """解析價格字串，處理 '--' 等無成交符號"""
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _to_yf_symbol(symbol: str) -> str:
    """台股代碼補上 .TW 後綴"""
    if symbol.isdigit():
        return f"{symbol}.TW"
    return symbol
