import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import { API_BASE } from "../lib/api";

interface Stock {
  symbol: string;
  name: string;
  close: number;
  change_pct: number | null;
  volume_value: number | null;
  volume_shares: number | null;
}

function fmtValue(v: number | null) {
  if (v == null) return "-";
  if (v >= 1e8) return `${(v / 1e8).toFixed(1)} 億`;
  if (v >= 1e4) return `${(v / 1e4).toFixed(0)} 萬`;
  return v.toLocaleString();
}

export default function VolumeRank() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE}/api/volume/ranking?market=tw&top=20`)
      .then((res) => setStocks(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <h2 style={{ fontSize: "1.1rem", color: "#374151", marginBottom: "0.8rem" }}>
        成交量排行 Top 20
        <span style={{ fontSize: "0.8rem", color: "#9ca3af", marginLeft: 8 }}>依成交金額</span>
      </h2>

      {loading ? (
        <p style={{ color: "#9ca3af" }}>載入中...</p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.9rem" }}>
          <thead>
            <tr style={{ background: "#f9fafb", color: "#6b7280" }}>
              {["名次", "代號", "名稱", "收盤", "漲跌幅", "成交金額"].map((h) => (
                <th key={h} style={{ padding: "0.5rem 0.8rem", textAlign: "left", fontWeight: 600, borderBottom: "2px solid #e5e7eb" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stocks.map((s, i) => {
              const up = s.change_pct != null && s.change_pct >= 0;
              return (
                <tr key={s.symbol} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "0.55rem 0.8rem", color: "#9ca3af", fontWeight: 600 }}>{i + 1}</td>
                  <td style={{ padding: "0.55rem 0.8rem" }}>
                    <Link href={`/stock/${s.symbol}`}
                      style={{ color: "#2563eb", textDecoration: "none", fontWeight: 600 }}>
                      {s.symbol}
                    </Link>
                  </td>
                  <td style={{ padding: "0.55rem 0.8rem", color: "#374151" }}>{s.name}</td>
                  <td style={{ padding: "0.55rem 0.8rem", fontWeight: 600, color: "#111827" }}>
                    {s.close?.toLocaleString()}
                  </td>
                  <td style={{ padding: "0.55rem 0.8rem", fontWeight: 600, color: up ? "#16a34a" : "#dc2626" }}>
                    {up ? "▲" : "▼"} {s.change_pct != null ? Math.abs(s.change_pct).toFixed(2) : "-"}%
                  </td>
                  <td style={{ padding: "0.55rem 0.8rem", color: "#374151" }}>
                    {fmtValue(s.volume_value)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
