import { useEffect, useRef, useState } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  LineStyle,
  type IChartApi,
} from "lightweight-charts";
import axios from "axios";
import { API_BASE } from "../lib/api";

interface AnalysisData {
  dates: string[];
  open: (number | null)[];
  high: (number | null)[];
  low: (number | null)[];
  close: (number | null)[];
  volume: number[];
  ma5: (number | null)[];
  ma20: (number | null)[];
  ma60: (number | null)[];
  rsi: (number | null)[];
  macd: (number | null)[];
  macd_signal: (number | null)[];
  macd_diff: (number | null)[];
  bb_upper: (number | null)[];
  bb_lower: (number | null)[];
  signal: string;
}

interface Props {
  symbol: string;
}

const BASE_OPTIONS = {
  layout: {
    background: { type: ColorType.Solid, color: "#ffffff" },
    textColor: "#374151",
  },
  grid: {
    vertLines: { color: "#f3f4f6" },
    horzLines: { color: "#f3f4f6" },
  },
  rightPriceScale: { borderColor: "#e5e7eb" },
  timeScale: { borderColor: "#e5e7eb", timeVisible: false },
  crosshair: { mode: CrosshairMode.Normal },
  handleScroll: true,
  handleScale: true,
};

function last(arr: (number | null)[] | undefined): number | null {
  if (!arr) return null;
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] != null) return arr[i]!;
  }
  return null;
}

function toLine(dates: string[], arr: (number | null)[]) {
  return dates
    .map((d, i) => ({ time: d as any, value: arr[i] }))
    .filter((p) => p.value != null);
}

function SubLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: "0.72rem", color: "#9ca3af", padding: "4px 0 2px 4px" }}>
      {children}
    </div>
  );
}

export default function PriceChart({ symbol }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mainRef   = useRef<HTMLDivElement>(null);
  const volRef    = useRef<HTMLDivElement>(null);
  const rsiRef    = useRef<HTMLDivElement>(null);
  const macdRef   = useRef<HTMLDivElement>(null);
  const chartsRef = useRef<IChartApi[]>([]);

  const [data, setData]       = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  // ── fetch ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null);
    axios
      .get(`${API_BASE}/api/analysis/${symbol}?period=6mo`)
      .then((r) => setData(r.data))
      .catch(() => setError("無法載入技術分析資料，請確認後端服務正常"))
      .finally(() => setLoading(false));
  }, [symbol]);

  // ── build charts ───────────────────────────────────────────────────────────
  useEffect(() => {
    const refs = [mainRef, volRef, rsiRef, macdRef];
    if (!data || refs.some((r) => !r.current)) return;

    const w = containerRef.current?.clientWidth ?? 800;

    // 1. Main chart — candlestick + MA + Bollinger
    const mainChart = createChart(mainRef.current!, { ...BASE_OPTIONS, width: w, height: 360 });

    const candle = mainChart.addCandlestickSeries({
      upColor: "#16a34a", downColor: "#dc2626",
      borderUpColor: "#16a34a", borderDownColor: "#dc2626",
      wickUpColor: "#16a34a", wickDownColor: "#dc2626",
    });
    candle.setData(
      data.dates
        .map((d, i) => ({ time: d as any, open: data.open[i], high: data.high[i], low: data.low[i], close: data.close[i] }))
        .filter((p) => p.open != null && p.close != null)
    );

    const addLine = (key: keyof AnalysisData, color: string, style = LineStyle.Solid, lw: 1 | 2 | 3 | 4 = 1) => {
      const s = mainChart.addLineSeries({ color, lineWidth: lw, lineStyle: style, priceLineVisible: false, lastValueVisible: false });
      s.setData(toLine(data.dates, data[key] as (number | null)[]));
    };
    addLine("ma5",      "#3b82f6");
    addLine("ma20",     "#f59e0b");
    addLine("ma60",     "#8b5cf6");
    addLine("bb_upper", "#94a3b8", LineStyle.Dashed);
    addLine("bb_lower", "#94a3b8", LineStyle.Dashed);
    mainChart.timeScale().fitContent();

    // 2. Volume chart
    const volChart = createChart(volRef.current!, {
      ...BASE_OPTIONS, width: w, height: 80,
      rightPriceScale: { ...BASE_OPTIONS.rightPriceScale, scaleMargins: { top: 0.1, bottom: 0 } },
    });
    const volSeries = volChart.addHistogramSeries({ priceFormat: { type: "volume" }, priceScaleId: "" });
    volSeries.setData(
      data.dates.map((d, i) => ({
        time: d as any,
        value: data.volume[i],
        color: (data.close[i] ?? 0) >= (data.open[i] ?? 0) ? "#bbf7d0" : "#fecaca",
      }))
    );
    volChart.timeScale().fitContent();

    // 3. RSI chart
    const rsiChart = createChart(rsiRef.current!, {
      ...BASE_OPTIONS, width: w, height: 90,
      rightPriceScale: { ...BASE_OPTIONS.rightPriceScale, scaleMargins: { top: 0.1, bottom: 0.1 } },
    });
    const rsiLine = rsiChart.addLineSeries({ color: "#7c3aed", lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    const rsiData = toLine(data.dates, data.rsi);
    rsiLine.setData(rsiData);

    if (rsiData.length >= 2) {
      const t0 = rsiData[0].time, t1 = rsiData[rsiData.length - 1].time;
      const ob = rsiChart.addLineSeries({ color: "#ef4444", lineWidth: 1, lineStyle: LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false });
      const os = rsiChart.addLineSeries({ color: "#16a34a", lineWidth: 1, lineStyle: LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false });
      ob.setData([{ time: t0, value: 70 }, { time: t1, value: 70 }]);
      os.setData([{ time: t0, value: 30 }, { time: t1, value: 30 }]);
    }
    rsiChart.timeScale().fitContent();

    // 4. MACD chart
    const macdChart = createChart(macdRef.current!, {
      ...BASE_OPTIONS, width: w, height: 90,
      rightPriceScale: { ...BASE_OPTIONS.rightPriceScale, scaleMargins: { top: 0.1, bottom: 0.1 } },
    });
    const macdHist = macdChart.addHistogramSeries({ priceLineVisible: false, lastValueVisible: false });
    macdHist.setData(
      data.dates
        .map((d, i) => ({ time: d as any, value: data.macd_diff[i], color: (data.macd_diff[i] ?? 0) >= 0 ? "#bbf7d0" : "#fecaca" }))
        .filter((p) => p.value != null)
    );
    const macdLine = macdChart.addLineSeries({ color: "#2563eb", lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    macdLine.setData(toLine(data.dates, data.macd));
    const sigLine = macdChart.addLineSeries({ color: "#ef4444", lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    sigLine.setData(toLine(data.dates, data.macd_signal));
    macdChart.timeScale().fitContent();

    // ── sync time scales across all sub-charts ──
    const subs = [volChart, rsiChart, macdChart];
    mainChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (range) subs.forEach((c) => c.timeScale().setVisibleLogicalRange(range));
    });

    chartsRef.current = [mainChart, volChart, rsiChart, macdChart];
    return () => {
      chartsRef.current.forEach((c) => c.remove());
      chartsRef.current = [];
    };
  }, [data]);

  // ── resize ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      const w = el.clientWidth;
      chartsRef.current.forEach((c) => c.applyOptions({ width: w }));
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // ── render ─────────────────────────────────────────────────────────────────
  if (loading) return <p style={{ color: "#9ca3af" }}>載入 K 線資料...</p>;
  if (error)   return <p style={{ color: "#dc2626" }}>{error}</p>;
  if (!data)   return null;

  const l = {
    close: last(data.close), ma5: last(data.ma5),
    ma20: last(data.ma20),   ma60: last(data.ma60),
    rsi: last(data.rsi),     macd: last(data.macd),
  };

  return (
    <div ref={containerRef} style={{ width: "100%" }}>

      {/* Legend */}
      <div style={{ display: "flex", gap: "1.2rem", fontSize: "0.8rem", marginBottom: 6, flexWrap: "wrap", color: "#374151" }}>
        <span>收盤 <b>{l.close?.toLocaleString()}</b></span>
        <span style={{ color: "#3b82f6" }}>MA5 <b>{l.ma5?.toFixed(1)}</b></span>
        <span style={{ color: "#f59e0b" }}>MA20 <b>{l.ma20?.toFixed(1)}</b></span>
        <span style={{ color: "#8b5cf6" }}>MA60 <b>{l.ma60?.toFixed(1)}</b></span>
        <span style={{ color: "#94a3b8" }}>── 布林通道</span>
      </div>

      {/* Main chart */}
      <div ref={mainRef} />

      {/* Volume */}
      <SubLabel>成交量</SubLabel>
      <div ref={volRef} />

      {/* RSI — label with overbought/oversold hints */}
      <SubLabel>
        RSI&nbsp;
        <span style={{ color: "#7c3aed", fontWeight: 600 }}>{l.rsi?.toFixed(1)}</span>
        &nbsp;
        <span style={{ color: "#ef4444" }}>70超買</span> /&nbsp;
        <span style={{ color: "#16a34a" }}>30超賣</span>
      </SubLabel>
      <div ref={rsiRef} />

      {/* MACD — label with current values */}
      <SubLabel>
        MACD&nbsp;
        <span style={{ color: "#2563eb", fontWeight: 600 }}>{l.macd?.toFixed(2)}</span>
        &nbsp;Signal&nbsp;
        <span style={{ color: "#ef4444", fontWeight: 600 }}>{last(data.macd_signal)?.toFixed(2)}</span>
      </SubLabel>
      <div ref={macdRef} />
    </div>
  );
}
