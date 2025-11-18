import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict

from data.yahoo_finance_collector import YahooFinanceCollector
from database.db_manager import get_db_manager
from data.turkish_symbols import get_turkish_symbols

logger = logging.getLogger(__name__)


class DataUpdateService:
    def __init__(self):
        self.collector = YahooFinanceCollector()
        self.db = get_db_manager()
        self.running = False
        self.last_run: Dict[str, str] = {}

    def _ensure_min_history(self, symbols: List[str], min_business_days: int = 500):
        for symbol in symbols:
            for interval in ["1d", "1h"]:
                try:
                    df = self.db.get_ohlcv_data(symbol, interval)
                    days = 0
                    if not df.empty:
                        days = (df.index.max() - df.index.min()).days
                    if df.empty or days < min_business_days:
                        period = "2y"
                        data = self.collector.fetch_historical_data(symbol, period=period, interval=interval, use_cache=True)
                        if data is not None and len(data) > 0:
                            self.db.insert_ohlcv_data(symbol, interval, data, source="yahoo")
                            logger.info(f"History ensured for {symbol} ({interval}) rows={len(data)})")
                except Exception as e:
                    logger.error(f"Ensure history failed for {symbol} ({interval}): {e}")

    def _update_intraday(self, symbols: List[str]):
        for symbol in symbols:
            for interval in ["1m", "5m", "15m"]:
                try:
                    data = self.collector.fetch_historical_data(symbol, period="7d", interval=interval, use_cache=True)
                    if data is not None and len(data) > 0:
                        self.db.insert_ohlcv_data(symbol, interval, data, source="yahoo")
                        logger.info(f"Intraday updated for {symbol} ({interval}) rows={len(data)})")
                except Exception as e:
                    logger.error(f"Intraday update failed for {symbol} ({interval}): {e}")

    def _validate(self, symbols: List[str]):
        for symbol in symbols:
            for interval in ["1d", "1h", "1m", "5m", "15m"]:
                try:
                    df = self.db.get_ohlcv_data(symbol, interval)
                    if df.empty:
                        logger.warning(f"✗ {symbol} ({interval}) - No data")
                        continue
                    missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                    date_range_days = (df.index.max() - df.index.min()).days
                    logger.info(f"✓ {symbol} ({interval}) rows={len(df)} range={date_range_days}d missing={missing_pct:.2f}%")
                except Exception as e:
                    logger.error(f"Validation error {symbol} ({interval}): {e}")

    async def run_daily_update(self):
        self.running = True
        symbols = get_turkish_symbols()
        while self.running:
            try:
                logger.info("📈 Daily data update started")
                self._ensure_min_history(symbols)
                self._update_intraday(symbols)
                self._validate(symbols)
                self.last_run = {"time": datetime.now().isoformat(), "symbols": len(symbols)}
                logger.info("✅ Daily data update completed")
            except Exception as e:
                logger.error(f"Daily update failed: {e}")
            # Sleep ~24h
            await asyncio.sleep(24 * 3600)

    def get_status(self) -> Dict:
        return {
            "running": self.running,
            "last_run": self.last_run
        }