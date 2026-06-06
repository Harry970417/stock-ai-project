import Link from "next/link";
import VolumeRank from "../components/VolumeRank";

export default function HomePage() {
  return (
    <main style={{ maxWidth: 1000, margin: "0 auto", padding: "2rem 1.5rem", fontFamily: "system-ui, sans-serif" }}>

      {/* 頂部導覽 */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.5rem", color: "#111827" }}>股票分析儀表板</h1>
        <nav style={{ display: "flex", gap: "1rem" }}>
          <Link href="/" style={navStyle}>首頁</Link>
          <Link href="/watchlist" style={{ ...navStyle, background: "#2563eb", color: "#fff" }}>
            隔日觀察名單
          </Link>
        </nav>
      </header>

      <VolumeRank />
    </main>
  );
}

const navStyle: React.CSSProperties = {
  padding: "0.4rem 1rem",
  borderRadius: 6,
  border: "1px solid #d1d5db",
  color: "#374151",
  textDecoration: "none",
  fontSize: "0.9rem",
  fontWeight: 500,
};
