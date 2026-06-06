import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler(timezone="Asia/Taipei")


def setup_scheduler():
    """註冊所有排程任務並加上執行日誌"""
    from models.database import save_watchlist

    scheduler.add_job(
        _run_watchlist,
        "cron",
        id="daily_watchlist",
        name="每日收盤後產生觀察名單",
        day_of_week="mon-fri",
        hour=14,
        minute=35,
        replace_existing=True,
    )
    scheduler.add_listener(_on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    logger.info("排程已設定：週一至週五 14:35 產生觀察名單")


async def _run_watchlist():
    from models.database import save_watchlist
    logger.info("排程觸發：開始產生觀察名單...")
    stocks = await save_watchlist()
    logger.info(f"排程完成：共篩選出 {len(stocks)} 支觀察股票")


def _on_job_event(event):
    if event.exception:
        logger.error(f"排程任務失敗 [{event.job_id}]: {event.exception}")
    else:
        logger.info(f"排程任務完成 [{event.job_id}]")


def get_schedule_status() -> dict:
    """回傳目前排程狀態，供 API 查詢"""
    job = scheduler.get_job("daily_watchlist")
    if not job:
        return {"running": False, "next_run": None, "message": "排程未設定"}
    return {
        "running": scheduler.running,
        "job_id": job.id,
        "job_name": job.name,
        "next_run": str(job.next_run_time) if job.next_run_time else None,
        "trigger": str(job.trigger),
    }
