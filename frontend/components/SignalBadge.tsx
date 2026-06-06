import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE } from "../lib/api";

interface Props {
  symbol: string;
}

const COLOR: Record<string, string> = {
  買進: "#22c55e",
  賣出: "#ef4444",
  觀望: "#f59e0b",
};

export default function SignalBadge({ symbol }: Props) {
  const [signal, setSignal] = useState<string>("載入中");

  useEffect(() => {
    axios.get(`${API_BASE}/api/signal/${symbol}`).then((res) => {
      setSignal(res.data.signal ?? "觀望");
    });
  }, [symbol]);

  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.3rem 1rem",
        borderRadius: "999px",
        background: COLOR[signal] ?? "#6b7280",
        color: "#fff",
        fontWeight: "bold",
        fontSize: "1.1rem",
        marginBottom: "1rem",
      }}
    >
      {signal}
    </span>
  );
}
