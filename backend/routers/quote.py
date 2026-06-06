from fastapi import APIRouter, HTTPException
from services.data_fetcher import fetch_quote, fetch_history

router = APIRouter()


@router.get("/{symbol}")
async def get_quote(symbol: str):
    """取得個股即時報價"""
    data = await fetch_quote(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"找不到股票代碼：{symbol}")
    return data


@router.get("/{symbol}/history")
async def get_history(symbol: str, period: str = "3mo"):
    """取得個股歷史行情，period 可為 1mo / 3mo / 6mo / 1y"""
    data = await fetch_history(symbol, period)
    if data is None:
        raise HTTPException(status_code=404, detail=f"找不到股票代碼：{symbol}")
    return data
