# stock-ai-project

股票分析網站，功能包含即時行情、技術分析、支撐壓力判斷、進出場提示、成交量排行、收盤後觀察名單。

## 技術架構

- **前端**：Next.js (React + TypeScript)
- **後端**：FastAPI (Python)
- **資料來源**：yfinance / twstock
- **資料庫**：SQLite（初期）
- **排程**：APScheduler

## 快速啟動

### 後端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```
