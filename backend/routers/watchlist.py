from fastapi import APIRouter
from models.database import get_watchlist, save_watchlist
from services.scheduler import get_schedule_status
from services.notifier import notify_watchlist, _line_token, _line_target, _email_user, _email_to

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
            "enabled":   bool(_line_token()),
            "token_set": bool(_line_token()),
            "mode":      "broadcast",
        },
        "email": {"enabled": bool(_email_user() and _email_to()), "from": _email_user() or None, "to": _email_to() or None},
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
