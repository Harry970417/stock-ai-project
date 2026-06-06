import time
from fastapi import APIRouter, HTTPException
from services.data_fetcher import fetch_volume_ranking

router = APIRouter()

_cache: dict = {"data": None, "ts": 0}
CACHE_TTL = 300  # TWSE 資料每 5 分鐘更新一次


@router.get("/ranking")
async def get_volume_ranking(market: str = "tw", top: int = 20):
    """取得成交量排行（依成交金額），market=tw，top 最多 50"""
    top = min(top, 50)

    if market == "tw":
        now = time.time()
        if _cache["data"] is None or now - _cache["ts"] > CACHE_TTL:
            result = await fetch_volume_ranking("tw", 50)
            if not result:
                raise HTTPException(status_code=503, detail="無法取得 TWSE 資料，請稍後再試")
            _cache["data"] = result
            _cache["ts"] = now
        return _cache["data"][:top]

    return await fetch_volume_ranking(market, top)
