import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from services.data_fetcher import fetch_history
from services.ta_engine import compute_indicators

router = APIRouter()


def _safe_json(obj):
    """自訂序列化：None → null，其餘正常輸出"""
    return json.loads(json.dumps(obj, default=lambda x: None))


@router.get("/{symbol}")
async def get_analysis(symbol: str, period: str = "6mo"):
    """取得個股技術分析指標（MA、RSI、MACD、布林通道）"""
    history = await fetch_history(symbol, period)
    if history is None:
        raise HTTPException(status_code=404, detail=f"找不到股票代碼：{symbol}")
    data = compute_indicators(history)
    return JSONResponse(content=_safe_json(data))
