import { useEffect, useState } from "react";
import axios from "axios";
import Link from "next/link";
import { API_BASE } from "../lib/api";

interface Stock {
  symbol: string;
  name: string;
  close: number;
  change_pct: number | null;
  score: number;
  matched_criteria: string[];
  rsi: number | null;
  ma5: number | null;
  ma20: number | null;
  macd_signal: string;
  support: number;
  resistance: number;
}

interface WatchlistData {
  date: string;
  total: number;
  stocks: Stock[];
  message?: string;
}

const SIGNAL_COLOR: Record<string, string> = {
  買進: "#16a34a",
  賣出: "#dc2626",
  觀望: "#d97706",
};

function ScoreStars({ score }: { score: number }) {
  return (
    <span style={{ fontSize: "1rem", letterSpacing: 1 }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span key={i} style={{ color: i < score ? "#f59e0b" : "#d1d5db" }}>★</span>
      ))}
    </span>
  );
}

function CriteriaBadge({ text }: { text: string }) {
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 8px",
      marginRight: 4,
      marginBottom: 4,
      borderRadius: 4,
      fontSize: "0.75rem",
      background: "#dcfce7",
      color: "#15803d",
      border: "1px solid #bbf7d0",
    }}>
      ✓ {text}
    </span>
  );
}

function StockCard({ stock, rank }: { stock: Stock; rank: number }) {
  const up = stock.change_pct != null && stock.change_pct >= 0;
  const changeColor = up ? "#16a34a" : "#dc2626";
  const distToRes = stock.resistance > 0
    ? (((stock.resistance - stock.close) / stock.close) * 100).toFixed(1)
    : null;

  return (
    <div style={{
      background: "#fff",
      border: "1px solid #e5e7eb",
      borderRadius: 10,
      padding: "1.2rem 1.4rem",
      marginBottom: "1rem",
      boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
    }}>
      {/* 頭部：名次、代號、評分 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{
            background: "#f3f4f6", borderRadius: "50%",
            width: 28, height: 28, display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.8rem", fontWeight: 700, color: "#6b7280",
          }}>{rank}</span>
          <div>
            <Link href={`/stock/${stock.symbol}`}
              style={{ fontWeight: 700, fontSize: "1.1rem", color: "#1d4ed8", textDecoration: "none" }}>
              {stock.symbol}
            </Link>
            <span style={{ marginLeft: 8, color: "#374151", fontWeight: 500 }}>{stock.name}</span>
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <ScoreStars score={stock.score} />
          <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: 2 }}>
            {stock.score}/5 條件
          </div>
        </div>
      </div>

      {/* 價格資訊 */}
      <div style={{ display: "flex", gap: "1.5rem", marginBottom: 10, flexWrap: "wrap" }}>
        <div>
          <span style={{ fontSize: "1.4rem", fontWeight: 700, color: "#111827" }}>
            {stock.close.toLocaleString()}
          </span>
          <span style={{ marginLeft: 8, fontWeight: 600, color: changeColor }}>
            {up ? "▲" : "▼"} {stock.change_pct != null ? Math.abs(stock.change_pct).toFixed(2) : "-"}%
          </span>
        </div>
        <div style={{ display: "flex", gap: "1rem", fontSize: "0.85rem", color: "#6b7280", alignItems: "center", flexWrap: "wrap" }}>
          <span>RSI <b style={{ color: "#111827" }}>{stock.rsi?.toFixed(1) ?? "-"}</b></span>
          <span>MA5 <b style={{ color: "#111827" }}>{stock.ma5?.toFixed(1) ?? "-"}</b></span>
          <span>MA20 <b style={{ color: "#111827" }}>{stock.ma20?.toFixed(1) ?? "-"}</b></span>
          <span>訊號 <b style={{ color: SIGNAL_COLOR[stock.macd_signal] ?? "#374151" }}>{stock.macd_signal}</b></span>
        </div>
      </div>

      {/* 支撐壓力 */}
      <div style={{ fontSize: "0.82rem", color: "#6b7280", marginBottom: 10, display: "flex", gap: "1.2rem", flexWrap: "wrap" }}>
        <span>支撐 <b style={{ color: "#374151" }}>{stock.support.toLocaleString()}</b></span>
        <span>壓力 <b style={{ color: "#374151" }}>{stock.resistance.toLocaleString()}</b></span>
        {distToRes && (
          <span>距壓力 <b style={{ color: "#374151" }}>{distToRes}%</b></span>
        )}
      </div>

      {/* 符合條件 */}
      <div>
        {stock.matched_criteria.map((c, i) => <CriteriaBadge key={i} text={c} />)}
      </div>
    </div>
  );
}

export default function WatchlistPage() {
  const [data, setData] = useState<WatchlistData | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWatchlist = () => {
    setLoading(true);
    setError(null);
    axios.get(`${API_BASE}/api/watchlist/tomorrow`)
      .then((res) => setData(res.data))
      .catch(() => setError("無法載入觀察名單，請確認後端服務正常"))
      .finally(() => setLoading(false));
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await axios.post(`${API_BASE}/api/watchlist/generate`);
      fetchWatchlist();
    } catch {
      setError("產生失敗，請稍後再試");
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => { fetchWatchlist(); }, []);

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem", fontFamily: "system-ui, sans-serif" }}>

      {/* 導覽 */}
      <div style={{ marginBottom: "1.5rem", fontSize: "0.9rem" }}>
        <Link href="/" style={{ color: "#6b7280", textDecoration: "none" }}>← 回首頁</Link>
      </div>

      {/* 標題列 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.6rem", color: "#111827" }}>隔日觀察名單</h1>
          {data?.date && (
            <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: "0.9rem" }}>
              產生日期：{data.date}　共 <b>{data.total}</b> 支
            </p>
          )}
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          style={{
            padding: "0.5rem 1.2rem",
            background: generating ? "#9ca3af" : "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: generating ? "not-allowed" : "pointer",
            fontWeight: 600,
            fontSize: "0.9rem",
          }}
        >
          {generating ? "篩選中（約 30–60 秒）..." : "重新產生名單"}
        </button>
      </div>

      {/* 評分說明 */}
      <div style={{
        background: "#f8fafc", border: "1px solid #e2e8f0",
        borderRadius: 8, padding: "0.8rem 1rem", marginBottom: "1.5rem",
        fontSize: "0.82rem", color: "#64748b",
      }}>
        <b>評分標準（滿 5 分）：</b>
        MA5 &gt; MA20（多頭排列）／收盤 &gt; MA60（站上長線）／RSI 40–68（健康動能）／MACD 多頭訊號／今日量 &gt; 均量 1.5×（異常放量）
      </div>

      {/* 內容區 */}
      {loading && <p style={{ color: "#6b7280" }}>載入中...</p>}
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      {!loading && !error && data?.message && (
        <p style={{ color: "#d97706" }}>{data.message}</p>
      )}
      {!loading && !error && data?.stocks?.length === 0 && (
        <p style={{ color: "#6b7280" }}>目前名單為空，請點「重新產生名單」</p>
      )}
      {!loading && !error && data?.stocks?.map((stock, i) => (
        <StockCard key={stock.symbol} stock={stock} rank={i + 1} />
      ))}
    </main>
  );
}
