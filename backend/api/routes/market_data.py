from fastapi import APIRouter, HTTPException
from typing import Optional
from data.yahoo_finance_collector import YahooFinanceCollector
from strategies.combined_strategy import CombinedStrategy
from strategies.parameters import ParameterDefinitions
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
        # Support for 500+ days of data
        if interval in ["1m"] and period not in ["1d", "5d", "7d"]:
            safe_period = "7d"
        elif interval in ["5m", "15m"] and period not in ["7d", "30d", "60d"]:
            safe_period = "60d"
        elif period == "500d":
            safe_period = "2y"  # Yahoo Finance doesn't support "500d", use 2 years instead

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
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {symbol}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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


@router.get("/position-analysis/{symbol}")
async def get_position_analysis(symbol: str, lookback_candles: int = 100):
    """
    Açık pozisyon için detaylı analiz - NEDEN GİRİLDİ?

    Returns:
    - Pozisyon bilgileri
    - Giriş yapılan mum ve önceki/sonraki mumlar
    - Her mumda hangi kuralların aktif olduğu
    - Giriş sebebi detaylı açıklama
    """
    try:
        from api.routes.paper_trading import engine

        # Pozisyonu al
        position = engine.get_position(symbol)
        if not position:
            return {
                "symbol": symbol,
                "has_position": False,
                "message": f"No open position for {symbol}"
            }

        # Pozisyon bilgileri
        pos_dict = position.to_dict()
        entry_time = pos_dict['opened_at']

        # Market data çek (pozisyon açılmadan önce ve sonra)
        collector = YahooFinanceCollector()
        df = collector.fetch_historical_data(symbol, period="3mo", interval="1h", use_cache=True)

        if df is None or len(df) == 0:
            return {"error": "No market data available"}

        # DataFrame normalization
        df = df.reset_index()
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # Zaman sütununu belirle
        time_col = 'datetime' if 'datetime' in df.columns else 'date'
        df[time_col] = pd.to_datetime(df[time_col])

        # Entry zamanını bul
        from datetime import datetime
        entry_dt = pd.to_datetime(entry_time)

        # Entry zamanına en yakın mumu bul
        df['time_diff'] = abs(df[time_col] - entry_dt)
        entry_idx = df['time_diff'].idxmin()

        # Entry mumu ve etrafındaki mumları al
        start_idx = max(0, entry_idx - lookback_candles//2)
        end_idx = min(len(df), entry_idx + lookback_candles//2)

        candles_df = df.iloc[start_idx:end_idx].copy()

        # Combined strategy ile detaylı sinyalleri al
        params = {
            'ma_fast': 10,
            'ma_slow': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bollinger_period': 20,
            'bollinger_std': 2.0,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 5.0
        }
        strategy = CombinedStrategy(params)
        signals_df = strategy.get_detailed_signals(candles_df)

        # Entry mumunu işaretle
        entry_candle_idx = entry_idx - start_idx

        # Mumları formatla
        candles = []
        for idx, row in signals_df.iterrows():
            is_entry_candle = (idx == entry_candle_idx)

            candle_data = {
                "t": row.get(time_col, idx).isoformat() if hasattr(row.get(time_col, idx), "isoformat") else str(row.get(time_col, idx)),
                "o": float(row["open"]) if "open" in row else 0,
                "h": float(row["high"]) if "high" in row else 0,
                "l": float(row["low"]) if "low" in row else 0,
                "c": float(row["close"]) if "close" in row else 0,
                "v": float(row.get("volume", 0)),

                # Indicators
                "rsi": float(row.get("rsi", 0)) if pd.notna(row.get("rsi")) else None,
                "ma_fast": float(row.get("ma_fast_val", 0)) if pd.notna(row.get("ma_fast_val")) else None,
                "ma_slow": float(row.get("ma_slow_val", 0)) if pd.notna(row.get("ma_slow_val")) else None,
                "macd_line": float(row.get("macd_line", 0)) if pd.notna(row.get("macd_line")) else None,
                "macd_signal": float(row.get("macd_signal", 0)) if pd.notna(row.get("macd_signal")) else None,
                "bb_upper": float(row.get("bb_upper", 0)) if pd.notna(row.get("bb_upper")) else None,
                "bb_mid": float(row.get("bb_mid", 0)) if pd.notna(row.get("bb_mid")) else None,
                "bb_lower": float(row.get("bb_lower", 0)) if pd.notna(row.get("bb_lower")) else None,

                # Signals
                "entry_signal": bool(row.get("entry_signal", False)),
                "exit_signal": bool(row.get("exit_signal", False)),
                "buy_strength": float(row.get("buy_strength", 0)),
                "sell_strength": float(row.get("sell_strength", 0)),

                # Active Rules
                "buy_rules": {
                    "ma": bool(row.get("buy_ma", False)),
                    "rsi": bool(row.get("buy_rsi", False)),
                    "bb": bool(row.get("buy_bb", False)),
                    "macd": bool(row.get("buy_macd", False)),
                },
                "sell_rules": {
                    "ma": bool(row.get("sell_ma", False)),
                    "rsi": bool(row.get("sell_rsi", False)),
                    "bb": bool(row.get("sell_bb", False)),
                    "macd": bool(row.get("sell_macd", False)),
                },

                # Explanations
                "buy_explanation": row.get("buy_rules", ""),
                "sell_explanation": row.get("sell_rules", ""),

                # Entry marker
                "is_entry_point": is_entry_candle
            }
            candles.append(candle_data)

        # Entry mumundaki bilgileri özel olarak çıkar
        entry_candle = candles[entry_candle_idx] if entry_candle_idx < len(candles) else None

        # P&L hesapla
        current_price = float(candles[-1]['c']) if candles else position.current_price
        pnl = (current_price - position.avg_entry_price) * position.quantity
        pnl_pct = ((current_price / position.avg_entry_price) - 1) * 100

        return {
            "symbol": symbol,
            "has_position": True,

            # Position Info
            "position": {
                "quantity": position.quantity,
                "entry_price": position.avg_entry_price,
                "current_price": current_price,
                "entry_time": entry_time,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "unrealized_pnl": position.unrealized_pnl,
            },

            # Entry Candle Detail
            "entry_candle": entry_candle,
            "entry_reason": entry_candle['buy_explanation'] if entry_candle else "Unknown",

            # All Candles
            "candles": candles,
            "total_candles": len(candles),
            "entry_candle_index": entry_candle_idx,

            # Summary
            "summary": f"Position opened at {entry_time} with {entry_candle['buy_explanation'] if entry_candle else 'unknown reason'}"
        }

    except Exception as e:
        import traceback
        print(f"Error in position-analysis: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}


@router.get("/all-positions-analysis")
async def get_all_positions_analysis():
    """
    TÜM açık pozisyonlar için detaylı analiz
    Her pozisyon için neden girildiğini gösterir
    """
    try:
        from api.routes.paper_trading import engine

        # Tüm pozisyonları al
        positions = engine.get_positions()

        if not positions:
            return {
                "positions": [],
                "count": 0,
                "message": "No open positions"
            }

        # Her pozisyon için analiz yap
        analyses = []
        for position in positions:
            symbol = position.symbol

            # Pozisyon analizi çağır
            analysis = await get_position_analysis(symbol, lookback_candles=50)
            analyses.append(analysis)

        return {
            "positions": analyses,
            "count": len(analyses),
            "message": f"Analysis for {len(analyses)} open positions"
        }

    except Exception as e:
        import traceback
        print(f"Error in all-positions-analysis: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}


@router.get("/candles-with-signals")
async def get_candles_with_signals(symbol: str, period: str = "1mo", interval: str = "1h"):
    """
    Her mum için detaylı trade sinyalleri ve kuralları döndürür

    Response:
    - OHLCV verileri
    - Her mumda hangi kuralların tetiklendiği
    - Alım/satım sinyalleri
    - Sinyal gücü (0-1)
    - Detaylı kural açıklamaları
    """
    try:
        collector = YahooFinanceCollector()

        # Veri çek
        safe_period = period
        if interval in ["1m"] and period not in ["1d", "5d", "7d"]:
            safe_period = "7d"
        elif interval in ["5m", "15m"] and period not in ["7d", "30d", "60d"]:
            safe_period = "60d"
        elif period == "500d":
            safe_period = "2y"

        df = collector.fetch_historical_data(symbol, period=safe_period, interval=interval, use_cache=True)

        if df is None or len(df) == 0:
            return []

        # DataFrame normalization
        df = df.reset_index()
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # Combined strategy ile detaylı sinyalleri al
        params = {
            'ma_fast': 10,
            'ma_slow': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bollinger_period': 20,
            'bollinger_std': 2.0,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 5.0
        }
        strategy = CombinedStrategy(params)

        # Detaylı sinyal analizi
        signals_df = strategy.get_detailed_signals(df)

        # Response formatla
        result = []
        for idx, row in signals_df.iterrows():
            candle_data = {
                # OHLCV
                "t": row.get("datetime", row.get("date", idx)).isoformat() if hasattr(row.get("datetime", row.get("date", idx)), "isoformat") else str(row.get("datetime", row.get("date", idx))),
                "o": float(row["open"]) if "open" in row else 0,
                "h": float(row["high"]) if "high" in row else 0,
                "l": float(row["low"]) if "low" in row else 0,
                "c": float(row["close"]) if "close" in row else 0,
                "v": float(row.get("volume", 0)),

                # Indicators
                "rsi": float(row.get("rsi", 0)) if pd.notna(row.get("rsi")) else None,
                "ma_fast": float(row.get("ma_fast_val", 0)) if pd.notna(row.get("ma_fast_val")) else None,
                "ma_slow": float(row.get("ma_slow_val", 0)) if pd.notna(row.get("ma_slow_val")) else None,
                "macd_line": float(row.get("macd_line", 0)) if pd.notna(row.get("macd_line")) else None,
                "macd_signal": float(row.get("macd_signal", 0)) if pd.notna(row.get("macd_signal")) else None,
                "bb_upper": float(row.get("bb_upper", 0)) if pd.notna(row.get("bb_upper")) else None,
                "bb_mid": float(row.get("bb_mid", 0)) if pd.notna(row.get("bb_mid")) else None,
                "bb_lower": float(row.get("bb_lower", 0)) if pd.notna(row.get("bb_lower")) else None,

                # Signals
                "entry_signal": bool(row.get("entry_signal", False)),
                "exit_signal": bool(row.get("exit_signal", False)),
                "buy_strength": float(row.get("buy_strength", 0)),
                "sell_strength": float(row.get("sell_strength", 0)),

                # Active Rules
                "buy_rules": {
                    "ma": bool(row.get("buy_ma", False)),
                    "rsi": bool(row.get("buy_rsi", False)),
                    "bb": bool(row.get("buy_bb", False)),
                    "macd": bool(row.get("buy_macd", False)),
                },
                "sell_rules": {
                    "ma": bool(row.get("sell_ma", False)),
                    "rsi": bool(row.get("sell_rsi", False)),
                    "bb": bool(row.get("sell_bb", False)),
                    "macd": bool(row.get("sell_macd", False)),
                },

                # Detailed explanations
                "buy_explanation": row.get("buy_rules", ""),
                "sell_explanation": row.get("sell_rules", ""),
            }
            result.append(candle_data)

        return result

    except Exception as e:
        import traceback
        print(f"Error in candles-with-signals: {e}")
        print(traceback.format_exc())
        return []