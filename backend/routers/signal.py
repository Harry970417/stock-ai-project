from fastapi import APIRouter, HTTPException
from services.data_fetcher import fetch_history
from services.ta_engine import compute_indicators, compute_support_resistance

router = APIRouter()


@router.get("/{symbol}")
async def get_signal(symbol: str):
    """取得支撐壓力位與進出場提示"""
    history = await fetch_history(symbol, "6mo")
    if history is None:
        raise HTTPException(status_code=404, detail=f"找不到股票代碼：{symbol}")

    indicators = compute_indicators(history)
    levels = compute_support_resistance(history)

    return {
        "symbol": symbol,
        "support_resistance": levels,
        "signal": indicators.get("signal"),
    }
