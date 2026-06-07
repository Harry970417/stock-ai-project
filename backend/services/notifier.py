import asyncio
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("notifier")

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"


def _line_token() -> str:
    return os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()

def _line_target() -> str:
    return (os.getenv("NOTIFY_TARGET_ID", "") or os.getenv("LINE_TARGET_ID", "")).strip()

def _email_user() -> str:
    return os.getenv("EMAIL_USER", "").strip()

def _email_password() -> str:
    return os.getenv("EMAIL_PASSWORD", "").strip()

def _email_to() -> str:
    return os.getenv("EMAIL_TO", "").strip()

# 保留供 router 匯入（向後相容）
LINE_CHANNEL_TOKEN = ""
LINE_TARGET_ID     = ""
EMAIL_USER         = ""
EMAIL_TO           = ""


# ── 主入口 ────────────────────────────────────────────────────────────────────

async def notify_watchlist(stocks: list, date: str) -> dict:
    """傳送觀察名單通知，回傳各管道結果"""
    if not stocks:
        return {"status": "skipped", "reason": "名單為空"}

    token  = _line_token()
    target = _line_target()
    eu     = _email_user()
    ep     = _email_password()
    et     = _email_to()

    tasks, labels = [], []

    if token:
        tasks.append(_send_line_broadcast(stocks, date, token))
        labels.append("line")
    if eu and ep and et:
        tasks.append(_send_email(stocks, date, eu, ep, et))
        labels.append("email")

    if not tasks:
        logger.warning("未設定任何通知管道，請複製 .env.example 為 .env 並填入憑證")
        return {"status": "skipped", "reason": "未設定通知憑證（LINE_CHANNEL_ACCESS_TOKEN / EMAIL_USER）"}

    results_raw = await asyncio.gather(*tasks, return_exceptions=True)
    results = {}
    for label, result in zip(labels, results_raw):
        if isinstance(result, Exception):
            results[label] = f"失敗：{result}"
            logger.error(f"[{label}] 通知失敗：{result}")
        else:
            results[label] = "ok"

    return {"status": "sent", "channels": results}


# ── LINE Messaging API — Push + Flex Message ──────────────────────────────────

async def _send_line_broadcast(stocks: list, date: str, token: str) -> None:
    payload = {"messages": [_build_flex_message(stocks, date)]}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            LINE_BROADCAST_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
    logger.info("LINE Broadcast 發送成功")


def _build_flex_message(stocks: list, date: str) -> dict:
    """建立 Flex Message Bubble，顯示觀察名單前 10 支"""
    top = stocks[:10]

    stock_rows = []
    for i, s in enumerate(top):
        chg   = s.get("change_pct") or 0
        color = "#16a34a" if chg >= 0 else "#dc2626"
        arrow = "▲" if chg >= 0 else "▼"
        stars = "★" * s.get("score", 0)

        stock_rows.append({
            "type": "box",
            "layout": "horizontal",
            "paddingTop": "8px",
            "paddingBottom": "8px",
            "contents": [
                {
                    "type": "box", "layout": "vertical", "flex": 3,
                    "contents": [
                        {"type": "text", "text": s["symbol"], "weight": "bold", "size": "sm", "color": "#111827"},
                        {"type": "text", "text": s["name"],   "size": "xs",    "color": "#6b7280"},
                    ],
                },
                {
                    "type": "text",
                    "text": f"{arrow}{abs(chg):.2f}%",
                    "size": "sm", "color": color, "weight": "bold",
                    "flex": 2, "align": "end",
                },
                {
                    "type": "text",
                    "text": f"RSI {s.get('rsi', 0):.0f}",
                    "size": "xs", "color": "#7c3aed",
                    "flex": 2, "align": "end",
                },
                {
                    "type": "text",
                    "text": stars,
                    "size": "xs", "color": "#f59e0b",
                    "flex": 2, "align": "end",
                },
            ],
        })
        # 分隔線（最後一行不加）
        if i < len(top) - 1:
            stock_rows.append({"type": "separator", "color": "#f3f4f6"})

    return {
        "type": "flex",
        "altText": f"📊 隔日觀察名單 {date}，共 {len(stocks)} 支",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#1d4ed8",
                "paddingAll": "16px",
                "contents": [
                    {"type": "text", "text": "📊 隔日觀察名單", "weight": "bold", "size": "lg",  "color": "#ffffff"},
                    {"type": "text", "text": date,              "size":   "sm",  "color": "#ffffffcc"},
                    {
                        "type": "text",
                        "text": f"共 {len(stocks)} 支符合篩選條件",
                        "size": "xs", "color": "#ffffffaa", "margin": "sm",
                    },
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "12px",
                "contents": [
                    # 欄位標頭
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "paddingBottom": "6px",
                        "contents": [
                            {"type": "text", "text": "代號／名稱", "size": "xs", "color": "#9ca3af", "flex": 3},
                            {"type": "text", "text": "漲跌",       "size": "xs", "color": "#9ca3af", "flex": 2, "align": "end"},
                            {"type": "text", "text": "RSI",        "size": "xs", "color": "#9ca3af", "flex": 2, "align": "end"},
                            {"type": "text", "text": "評分",       "size": "xs", "color": "#9ca3af", "flex": 2, "align": "end"},
                        ],
                    },
                    {"type": "separator"},
                    *stock_rows,
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#f9fafb",
                "paddingAll": "10px",
                "contents": [
                    {
                        "type": "text",
                        "text": "篩選：MA多頭・RSI健康・MACD看多・異常放量",
                        "size": "xs", "color": "#9ca3af", "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": "僅供參考，非投資建議",
                        "size": "xs", "color": "#d1d5db", "margin": "sm",
                    },
                ],
            },
        },
    }


# ── Email ─────────────────────────────────────────────────────────────────────

async def _send_email(stocks: list, date: str, eu: str, ep: str, et: str) -> None:
    text_body = _build_text(stocks, date)
    html_body = _build_html(stocks, date)
    await asyncio.to_thread(_send_email_sync, date, text_body, html_body, eu, ep, et)


def _send_email_sync(date: str, text_body: str, html_body: str, eu: str, ep: str, et: str) -> None:
    host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.getenv("EMAIL_PORT", "587"))
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 隔日觀察名單 {date}"
    msg["From"]    = eu
    msg["To"]      = et
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(eu, ep)
        smtp.sendmail(eu, [t.strip() for t in et.split(",")], msg.as_string())
    logger.info(f"Email 發送成功 → {et}")


# ── 文字格式（Email 純文字備用 & log）────────────────────────────────────────

def _build_text(stocks: list, date: str) -> str:
    lines = [f"📊 隔日觀察名單 {date}", f"共 {len(stocks)} 支符合條件\n"]
    for s in stocks[:10]:
        chg   = s.get("change_pct") or 0
        arrow = "▲" if chg >= 0 else "▼"
        stars = "★" * s.get("score", 0)
        lines.append(f"{stars} {s['symbol']} {s['name']}  {arrow}{abs(chg):.2f}%  RSI {s.get('rsi', 0):.1f}")
    lines.append("\n篩選：MA多頭・RSI健康・MACD看多・異常放量\n僅供參考，非投資建議")
    return "\n".join(lines)


def _build_html(stocks: list, date: str) -> str:
    rows = ""
    for i, s in enumerate(stocks, 1):
        chg    = s.get("change_pct") or 0
        color  = "#16a34a" if chg >= 0 else "#dc2626"
        arrow  = "▲" if chg >= 0 else "▼"
        score  = s.get("score", 0)
        stars  = "★" * score + "☆" * (5 - score)
        rows += f"""
        <tr style="border-bottom:1px solid #f3f4f6">
          <td style="padding:8px 12px;color:#9ca3af;text-align:center">{i}</td>
          <td style="padding:8px 12px;font-weight:700">{s['symbol']}</td>
          <td style="padding:8px 12px">{s['name']}</td>
          <td style="padding:8px 12px;font-weight:700">{s.get('close','')}</td>
          <td style="padding:8px 12px;color:{color};font-weight:700">{arrow}{abs(chg):.2f}%</td>
          <td style="padding:8px 12px;color:#7c3aed">{s.get('rsi',0):.1f}</td>
          <td style="padding:8px 12px;color:#f59e0b;letter-spacing:1px">{stars}</td>
        </tr>"""
    return f"""<!DOCTYPE html>
<html>
<body style="font-family:system-ui,sans-serif;max-width:700px;margin:0 auto;padding:24px;color:#111827">
  <h2 style="color:#1d4ed8;margin-bottom:4px">📊 隔日觀察名單</h2>
  <p style="color:#6b7280;margin-top:0">{date} · 共 <strong>{len(stocks)}</strong> 支</p>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <thead>
      <tr style="background:#f9fafb;color:#6b7280;font-size:12px">
        <th style="padding:8px 12px">#</th>
        <th style="padding:8px 12px;text-align:left">代號</th>
        <th style="padding:8px 12px;text-align:left">名稱</th>
        <th style="padding:8px 12px;text-align:left">收盤</th>
        <th style="padding:8px 12px;text-align:left">漲跌</th>
        <th style="padding:8px 12px;text-align:left">RSI</th>
        <th style="padding:8px 12px;text-align:left">評分</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <p style="color:#9ca3af;font-size:11px;margin-top:16px;border-top:1px solid #f3f4f6;padding-top:12px">
    由 stock-ai-project 自動產生 · 僅供參考，非投資建議
  </p>
</body>
</html>"""
