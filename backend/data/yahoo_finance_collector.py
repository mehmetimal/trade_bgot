"""
Yahoo Finance Data Collector
Free API for stocks, crypto, forex data
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YahooFinanceCollector:
    """
    Yahoo Finance ücretsiz API ile veri toplama
    - Stocks, ETFs, Crypto, Forex destekler
    - Rate limiting: ~2000 requests/day
    """

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.request_count = 0
        self.last_request_time = None
        self.min_request_interval = 0.5  # 500ms between requests

        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)

    def _rate_limit(self):
        """Rate limiting - request'ler arası minimum bekleme"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)

        self.last_request_time = time.time()
        self.request_count += 1

        if self.request_count % 100 == 0:
            logger.info(f"Total requests made: {self.request_count}")

    def fetch_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Historical OHLCV data çekme

        Args:
            symbol: Trading symbol (AAPL, BTC-USD, EURUSD=X)
            period: Zaman aralığı (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            use_cache: Cache kullan

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        try:
            self._rate_limit()

            # Cache kontrolü
            if use_cache:
                cached_data = self._load_from_cache(symbol, period, interval)
                if cached_data is not None:
                    logger.info(f"Using cached data for {symbol}")
                    return cached_data

            logger.info(f"Fetching {symbol} - period: {period}, interval: {interval}")

            # Yahoo Finance'den veri çek
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)

            if data.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Data normalization
            data = self._normalize_data(data)

            # Cache'e kaydet
            if use_cache:
                self._save_to_cache(data, symbol, period, interval)

            logger.info(f"Successfully fetched {len(data)} rows for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}")
            return None

    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """Birden fazla symbol için data çekme"""
        results = {}

        for symbol in symbols:
            data = self.fetch_historical_data(
                symbol=symbol,
                period=period,
                interval=interval,
                use_cache=use_cache
            )

            if data is not None:
                results[symbol] = data
            else:
                logger.warning(f"Skipping {symbol} - no data")

            # Rate limiting için bekleme
            time.sleep(0.5)

        logger.info(f"Fetched data for {len(results)}/{len(symbols)} symbols")
        return results

    def fetch_realtime_price(self, symbol: str) -> Optional[Dict]:
        """
        Gerçek zamanlı fiyat bilgisi

        Returns:
            {
                'symbol': 'AAPL',
                'price': 150.25,
                'change': 2.50,
                'change_percent': 1.69,
                'volume': 75000000,
                'timestamp': '2024-01-15 16:00:00'
            }
        """
        try:
            self._rate_limit()

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'change': info.get('regularMarketChange'),
                'change_percent': info.get('regularMarketChangePercent'),
                'volume': info.get('volume'),
                'bid': info.get('bid'),
                'ask': info.get('ask'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching realtime price for {symbol}: {str(e)}")
            return None

    def fetch_company_info(self, symbol: str) -> Optional[Dict]:
        """Şirket/Asset bilgileri"""
        try:
            self._rate_limit()

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'name': info.get('longName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'description': info.get('longBusinessSummary')
            }

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {str(e)}")
            return None

    def _normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Yahoo Finance data normalization
        - Column isimleri standardize
        - Timezone remove
        - NaN handling
        """
        # Timezone bilgisini kaldır
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)

        # Column isimleri standardize et (lowercase)
        data.columns = [col.lower().replace(' ', '_') for col in data.columns]

        # Gereksiz kolonları kaldır
        columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
        data = data[[col for col in columns_to_keep if col in data.columns]]

        # NaN values handle et
        data = data.dropna()

        return data

    def _save_to_cache(
        self,
        data: pd.DataFrame,
        symbol: str,
        period: str,
        interval: str
    ):
        """Cache'e kaydet"""
        cache_file = f"{self.cache_dir}/{symbol}_{period}_{interval}.parquet"

        try:
            data.to_parquet(cache_file)
            logger.debug(f"Cached data to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")

    def _load_from_cache(
        self,
        symbol: str,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Cache'den yükle"""
        cache_file = f"{self.cache_dir}/{symbol}_{period}_{interval}.parquet"

        if not os.path.exists(cache_file):
            return None

        # Cache yaşını kontrol et (7 günden eskiyse yenile)
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > 604800:  # 7 days
            logger.debug(f"Cache expired for {symbol}")
            return None

        try:
            data = pd.read_parquet(cache_file)
            logger.debug(f"Loaded from cache: {cache_file}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def clear_cache(self):
        """Clear all cached data"""
        import glob

        cache_files = glob.glob(f"{self.cache_dir}/*.parquet")
        for file in cache_files:
            try:
                os.remove(file)
                logger.info(f"Removed cache file: {file}")
            except Exception as e:
                logger.warning(f"Failed to remove {file}: {e}")


# Convenience function
def fetch_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """Quick data fetch"""
    collector = YahooFinanceCollector()
    return collector.fetch_historical_data(symbol, period, interval)


if __name__ == "__main__":
    # Test the collector
    collector = YahooFinanceCollector()

    # Test single symbol
    print("\n" + "="*50)
    print("Testing Yahoo Finance Collector")
    print("="*50)

    aapl_data = collector.fetch_historical_data("AAPL", period="1mo", interval="1d")
    if aapl_data is not None:
        print(f"\n✓ AAPL: {len(aapl_data)} days fetched")
        print(aapl_data.tail())

    # Test crypto
    btc_data = collector.fetch_historical_data("BTC-USD", period="1mo", interval="1d")
    if btc_data is not None:
        print(f"\n✓ BTC-USD: {len(btc_data)} days fetched")
        print(btc_data.tail())

    # Test realtime price
    price = collector.fetch_realtime_price("AAPL")
    if price:
        print(f"\n✓ AAPL realtime price: ${price.get('price', 'N/A')}")

    print("\n" + "="*50)
    print("Yahoo Finance API is working!")
    print("="*50)
