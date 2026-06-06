from fastapi import APIRouter
from models.database import get_watchlist, save_watchlist
from services.scheduler import get_schedule_status
from services.notifier import notify_watchlist, LINE_CHANNEL_TOKEN, LINE_TARGET_ID, EMAIL_USER, EMAIL_TO

router = APIRouter()


@router.get("/tomorrow")
async def get_tomorrow_watchlist():
    """取得最新一次收盤後產生的隔日觀察名單"""
    return await get_watchlist()


@router.post("/generate")
async def generate_watchlist():
    """手動觸發產生隔日觀察名單（正常由排程自動執行）"""
    result = await save_watchlist()
    return {"status": "ok", "generated": len(result), "stocks": result}


@router.get("/schedule")
def get_schedule():
    """查詢排程狀態與下次執行時間"""
    return get_schedule_status()


@router.get("/notify/config")
def get_notify_config():
    """查詢目前通知設定（不顯示實際憑證）"""
    return {
        "line_messaging_api": {
            "enabled":   bool(LINE_CHANNEL_TOKEN and LINE_TARGET_ID),
            "token_set": bool(LINE_CHANNEL_TOKEN),
            "target_id": LINE_TARGET_ID or None,
        },
        "email":       {"enabled": bool(EMAIL_USER and EMAIL_TO), "from": EMAIL_USER or None, "to": EMAIL_TO or None},
    }


@router.post("/notify/test")
async def test_notify():
    """用目前名單測試發送通知"""
    data = await get_watchlist()
    stocks = data.get("stocks", [])
    date   = data.get("date", "test")
    if not stocks:
        return {"status": "skipped", "reason": "名單為空，請先呼叫 POST /api/watchlist/generate"}
    result = await notify_watchlist(stocks[:5], date)
    return result
