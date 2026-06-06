import json
import logging
import os
from datetime import date
from services.screener import generate_watchlist
from services.notifier import notify_watchlist

logger  = logging.getLogger("database")
_data_dir = os.getenv("WATCHLIST_DIR", os.path.join(os.path.dirname(__file__), ".."))
DB_FILE   = os.path.join(_data_dir, "watchlist.json")


async def get_watchlist() -> dict:
    """讀取最新觀察名單"""
    if not os.path.exists(DB_FILE):
        return {"date": None, "stocks": [], "message": "尚未產生觀察名單，請呼叫 POST /api/watchlist/generate"}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


async def save_watchlist() -> list:
    """執行篩選、儲存觀察名單，並發送通知"""
    today  = str(date.today())
    stocks = await generate_watchlist(max_results=20)

    payload = {"date": today, "total": len(stocks), "stocks": stocks}
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    notify_result = await notify_watchlist(stocks, today)
    logger.info(f"通知結果：{notify_result}")

    return stocks
