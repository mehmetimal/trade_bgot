"""
Backtest Data Download Script
Downloads historical data for multiple symbols and stores in database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.yahoo_finance_collector import YahooFinanceCollector
from database.db_manager import get_db_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BacktestDataPreparation:
    """Backtest için gerekli tüm datayı topla ve hazırla"""

    def __init__(self):
        self.collector = YahooFinanceCollector()
        self.db = get_db_manager()
        self.symbols = self._get_symbol_list()

    def _get_symbol_list(self) -> dict:
        """Backtest için symbol listesi"""
        return {
            'stocks': [
                # US Large Cap
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA',
                'JPM', 'V', 'WMT', 'PG', 'JNJ', 'UNH', 'HD', 'BAC',

                # Tech
                'AMD', 'INTC', 'NFLX', 'ADBE', 'CRM', 'ORCL', 'CSCO',

                # Others
                'DIS', 'NKE', 'PYPL', 'BA', 'KO', 'PFE', 'MCD'
            ],
            'crypto': [
                'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD',
                'ADA-USD', 'DOGE-USD', 'MATIC-USD', 'DOT-USD'
            ],
            'forex': [
                'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X'
            ],
            'etf': [
                'SPY', 'QQQ', 'DIA', 'IWM', 'GLD', 'SLV', 'TLT'
            ]
        }

    def download_all_data(
        self,
        period: str = "2y",
        intervals: list = ["1d", "1h"]
    ):
        """Tüm sembolleri tüm timeframe'lerde indir"""

        total_symbols = sum(len(symbols) for symbols in self.symbols.values())
        downloaded = 0
        failed = []

        logger.info("="*60)
        logger.info("STARTING DATA DOWNLOAD")
        logger.info("="*60)
        logger.info(f"Total symbols: {total_symbols}")
        logger.info(f"Period: {period}")
        logger.info(f"Intervals: {intervals}")
        logger.info("="*60)

        for category, symbol_list in self.symbols.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Downloading {category.upper()} data...")
            logger.info(f"{'='*60}")

            for symbol in symbol_list:
                for interval in intervals:
                    try:
                        # Fetch data
                        data = self.collector.fetch_historical_data(
                            symbol=symbol,
                            period=period,
                            interval=interval,
                            use_cache=True
                        )

                        if data is not None and len(data) > 0:
                            # Store in database
                            rows_inserted = self.db.insert_ohlcv_data(
                                symbol=symbol,
                                timeframe=interval,
                                data=data,
                                source='yahoo'
                            )

                            downloaded += 1
                            logger.info(
                                f"✓ {symbol:15} ({interval:3}) - "
                                f"{len(data):5} candles - "
                                f"{rows_inserted:5} new rows"
                            )
                        else:
                            logger.warning(f"✗ {symbol:15} ({interval:3}) - No data")
                            failed.append(f"{symbol} ({interval})")

                    except Exception as e:
                        logger.error(f"✗ {symbol:15} ({interval:3}) - Error: {str(e)}")
                        failed.append(f"{symbol} ({interval})")

        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("DOWNLOAD COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Successfully downloaded: {downloaded} datasets")
        logger.info(f"Failed: {len(failed)} datasets")

        if failed:
            logger.warning(f"\nFailed symbols:")
            for f in failed:
                logger.warning(f"  - {f}")

        # Database statistics
        stats = self.db.get_data_statistics()
        logger.info(f"\n{'='*60}")
        logger.info("DATABASE STATISTICS")
        logger.info(f"{'='*60}")
        for key, value in stats.items():
            logger.info(f"{key:30}: {value:,}")
        logger.info(f"{'='*60}")

    def validate_data_quality(self):
        """İndirilen datanın kalitesini kontrol et"""
        logger.info("\n" + "="*60)
        logger.info("DATA QUALITY VALIDATION")
        logger.info("="*60)

        symbols = self.db.get_available_symbols()

        for symbol in symbols:
            for interval in ["1d", "1h"]:
                try:
                    data = self.db.get_ohlcv_data(symbol, interval)

                    if data.empty:
                        logger.warning(f"✗ {symbol:15} ({interval}) - No data in DB")
                        continue

                    # Check for gaps
                    missing_pct = (data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100

                    # Check data range
                    date_range = (data.index.max() - data.index.min()).days

                    logger.info(
                        f"✓ {symbol:15} ({interval:3}) - "
                        f"{len(data):5} rows - "
                        f"{date_range:4} days - "
                        f"Missing: {missing_pct:.2f}%"
                    )

                except Exception as e:
                    logger.error(f"✗ {symbol:15} ({interval}) - Validation error: {e}")

        logger.info("="*60)


def main():
    """Main execution"""
    # Create database tables
    logger.info("Initializing database...")
    db = get_db_manager()
    db.create_tables()

    # Create and run data preparation
    prep = BacktestDataPreparation()

    # Download data
    # For testing: use smaller period and fewer intervals
    # prep.download_all_data(period="1mo", intervals=["1d"])

    # For production: use full period
    prep.download_all_data(period="2y", intervals=["1d", "1h"])

    # Validate data quality
    prep.validate_data_quality()

    logger.info("\n✓ Data preparation complete!")


if __name__ == "__main__":
    main()
