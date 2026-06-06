import pandas as pd
import ta


def _sanitize(series: pd.Series) -> list:
    """將 NaN / NA 轉為 None，避免 JSON 序列化失敗"""
    return [None if pd.isna(v) else round(float(v), 4) for v in series]


def compute_indicators(df: pd.DataFrame) -> dict:
    """計算技術指標：MA、RSI、MACD、布林通道，並產生進出場訊號"""
    close = df["Close"]
    volume = df["Volume"]

    ma5 = ta.trend.sma_indicator(close, window=5)
    ma20 = ta.trend.sma_indicator(close, window=20)
    ma60 = ta.trend.sma_indicator(close, window=60)
    rsi = ta.momentum.rsi(close, window=14)
    macd = ta.trend.macd(close)
    macd_signal = ta.trend.macd_signal(close)
    bb_upper = ta.volatility.bollinger_hband(close)
    bb_lower = ta.volatility.bollinger_lband(close)

    macd_diff = macd - macd_signal
    signal = _determine_signal(close, ma5, ma20, rsi, macd, macd_signal)

    return {
        "dates": df.index.tolist(),
        "open":  _sanitize(df["Open"]),
        "high":  _sanitize(df["High"]),
        "low":   _sanitize(df["Low"]),
        "close": _sanitize(close),
        "volume": volume.tolist(),
        "ma5": _sanitize(ma5),
        "ma20": _sanitize(ma20),
        "ma60": _sanitize(ma60),
        "rsi": _sanitize(rsi),
        "macd": _sanitize(macd),
        "macd_signal": _sanitize(macd_signal),
        "macd_diff": _sanitize(macd_diff),
        "bb_upper": _sanitize(bb_upper),
        "bb_lower": _sanitize(bb_lower),
        "signal": signal,
    }


def compute_support_resistance(df: pd.DataFrame) -> dict:
    """以近期高低點計算支撐壓力位"""
    recent = df.tail(60)
    return {
        "resistance": round(float(recent["High"].max()), 2),
        "support": round(float(recent["Low"].min()), 2),
        "mid": round((float(recent["High"].max()) + float(recent["Low"].min())) / 2, 2),
    }


def _determine_signal(close, ma5, ma20, rsi, macd, macd_signal) -> str:
    """綜合判斷進出場訊號"""
    last_close = close.iloc[-1]
    last_rsi = rsi.iloc[-1]
    macd_cross_up = macd.iloc[-1] > macd_signal.iloc[-1] and macd.iloc[-2] <= macd_signal.iloc[-2]
    macd_cross_down = macd.iloc[-1] < macd_signal.iloc[-1] and macd.iloc[-2] >= macd_signal.iloc[-2]

    if ma5.iloc[-1] > ma20.iloc[-1] and macd_cross_up and last_rsi < 70:
        return "買進"
    if ma5.iloc[-1] < ma20.iloc[-1] and macd_cross_down and last_rsi > 30:
        return "賣出"
    return "觀望"
