import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import { API_BASE } from "../../lib/api";
import PriceChart from "../../components/PriceChart";

interface Quote {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  previous_close: number;
  change_pct: number;
}

interface SignalData {
  symbol: string;
  support_resistance: { support: number; resistance: number; mid: number };
  signal: string;
}

const SIGNAL_STYLE: Record<string, { bg: string; color: string }> = {
  買進: { bg: "#dcfce7", color: "#15803d" },
  賣出: { bg: "#fee2e2", color: "#b91c1c" },
  觀望: { bg: "#fef3c7", color: "#b45309" },
};

export default function StockPage() {
  const router = useRouter();
  const { id } = router.query;
  const symbol = id as string;

  const [quote, setQuote]   = useState<Quote | null>(null);
  const [signal, setSignal] = useState<SignalData | null>(null);

  useEffect(() => {
    if (!symbol) return;
    axios.get(`${API_BASE}/api/quote/${symbol}`).then((r) => setQuote(r.data));
    axios.get(`${API_BASE}/api/signal/${symbol}`).then((r) => setSignal(r.data));
  }, [symbol]);

  if (!symbol) return <p style={{ padding: "2rem" }}>載入中...</p>;

  const up = (quote?.change_pct ?? 0) >= 0;
  const changeColor = up ? "#16a34a" : "#dc2626";
  const sig = signal?.signal ?? "";
  const sigStyle = SIGNAL_STYLE[sig] ?? { bg: "#f3f4f6", color: "#374151" };

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "1.5rem", fontFamily: "system-ui, sans-serif" }}>

      {/* 導覽 */}
      <div style={{ marginBottom: "1rem", fontSize: "0.88rem", display: "flex", gap: "1rem" }}>
        <Link href="/" style={{ color: "#6b7280", textDecoration: "none" }}>← 首頁</Link>
        <Link href="/watchlist" style={{ color: "#6b7280", textDecoration: "none" }}>觀察名單</Link>
      </div>

      {/* 標題 + 報價 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1.2rem" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.5rem", color: "#111827" }}>
            {symbol}
            {quote && <span style={{ fontSize: "1rem", color: "#6b7280", marginLeft: 10, fontWeight: 400 }}>台股</span>}
          </h1>
          {quote && (
            <div style={{ marginTop: 6, display: "flex", alignItems: "baseline", gap: "0.8rem", flexWrap: "wrap" }}>
              <span style={{ fontSize: "2rem", fontWeight: 700, color: "#111827" }}>
                {quote.price?.toLocaleString()}
              </span>
              <span style={{ fontSize: "1.1rem", fontWeight: 600, color: changeColor }}>
                {up ? "▲" : "▼"} {Math.abs(quote.change_pct).toFixed(2)}%
              </span>
              <span style={{ fontSize: "0.85rem", color: "#9ca3af" }}>
                前收 {quote.previous_close?.toLocaleString()}
              </span>
            </div>
          )}
        </div>

        {/* 訊號 Badge */}
        {sig && (
          <div style={{ background: sigStyle.bg, color: sigStyle.color, padding: "0.5rem 1.5rem", borderRadius: 999, fontWeight: 700, fontSize: "1.1rem", alignSelf: "center" }}>
            {sig}
          </div>
        )}
      </div>

      {/* 今日行情小卡 */}
      {quote && (
        <div style={{ display: "flex", gap: "0.8rem", marginBottom: "1.2rem", flexWrap: "wrap" }}>
          {[
            ["開盤", quote.open],
            ["最高", quote.high],
            ["最低", quote.low],
            ["成交量", quote.volume?.toLocaleString()],
          ].map(([label, val]) => (
            <div key={label as string} style={{ background: "#f9fafb", borderRadius: 8, padding: "0.5rem 0.9rem", fontSize: "0.85rem", border: "1px solid #e5e7eb" }}>
              <div style={{ color: "#9ca3af", marginBottom: 2 }}>{label}</div>
              <div style={{ fontWeight: 600, color: "#111827" }}>{val?.toLocaleString()}</div>
            </div>
          ))}
        </div>
      )}

      {/* 支撐壓力 */}
      {signal?.support_resistance && (
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1.2rem", flexWrap: "wrap", fontSize: "0.85rem" }}>
          {[
            ["支撐", signal.support_resistance.support, "#16a34a"],
            ["中樞", signal.support_resistance.mid,     "#374151"],
            ["壓力", signal.support_resistance.resistance, "#dc2626"],
          ].map(([label, val, color]) => (
            <div key={label as string} style={{ background: "#fff", border: `1px solid ${color}30`, borderRadius: 8, padding: "0.4rem 0.8rem" }}>
              <span style={{ color: "#9ca3af" }}>{label} </span>
              <span style={{ fontWeight: 700, color: color as string }}>{(val as number)?.toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}

      {/* K 線圖 */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: "1rem", boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
        <PriceChart symbol={symbol} />
      </div>
    </main>
  );
}
