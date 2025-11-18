from fastapi import APIRouter, HTTPException
from typing import Optional
from data.yahoo_finance_collector import YahooFinanceCollector
import pandas as pd

router = APIRouter()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.clip(lower=0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace({0: 1e-9})
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    ma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    return ma, upper, lower


@router.get("/ohlcv")
async def get_ohlcv(symbol: str, period: str = "1mo", interval: str = "1h"):
    try:
        collector = YahooFinanceCollector()
        safe_period = period
        if interval in ["1m"] and period not in ["1d", "5d", "7d"]:
            safe_period = "7d"
        elif interval in ["5m", "15m"] and period not in ["7d", "30d", "60d"]:
            safe_period = "60d"

        df = collector.fetch_historical_data(symbol, period=safe_period, interval=interval, use_cache=True)
        if df is None or len(df) == 0:
            return []
        df = df.reset_index()
        return [
            {
                "t": row["Datetime"].isoformat() if "Datetime" in df.columns else row["Date"].isoformat(),
                "o": float(row["Open"]),
                "h": float(row["High"]),
                "l": float(row["Low"]),
                "c": float(row["Close"]),
                "v": float(row.get("Volume", 0))
            }
            for _, row in df.iterrows()
        ]
    except Exception:
        return []


@router.get("/indicators")
async def get_indicators(symbol: str, period: str = "1mo", interval: str = "1h"):
    try:
        collector = YahooFinanceCollector()
        df = collector.fetch_historical_data(symbol, period=period, interval=interval, use_cache=True)
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail="No data")
        df = df.copy()
        df.index = pd.to_datetime(df.index)
        if getattr(df.index, 'tz', None) is not None:
            df.index = df.index.tz_localize(None)
        close = pd.to_numeric(df["Close"], errors='coerce').fillna(method='ffill')
        rsi_val = rsi(close)
        macd_line, signal_line, hist = macd(close)
        ma, upper, lower = bollinger(close)
        idx = df.index
        return {
            "rsi": [{"t": i.isoformat(), "value": float(v)} for i, v in zip(idx, rsi_val.fillna(0))],
            "macd": {
                "line": [{"t": i.isoformat(), "value": float(v)} for i, v in zip(idx, macd_line.fillna(0))],
                "signal": [{"t": i.isoformat(), "value": float(v)} for i, v in zip(idx, signal_line.fillna(0))],
                "hist": [{"t": i.isoformat(), "value": float(v)} for i, v in zip(idx, hist.fillna(0))]
            },
            "bollinger": {
                "ma": [{"t": i.isoformat(), "value": float(v)} for i, v in zip(idx, ma.fillna(0))],
                "upper": [{"t": i.isoformat(), "value": float(v)} for i, v in zip(idx, upper.fillna(0))],
                "lower": [{"t": i.isoformat(), "value": float(v)} for i, v in zip(idx, lower.fillna(0))]
            }
        }
    except HTTPException:
        raise
    except Exception:
        return {
            "rsi": [],
            "macd": {"line": [], "signal": [], "hist": []},
            "bollinger": {"ma": [], "upper": [], "lower": []}
        }