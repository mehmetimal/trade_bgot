"""
Quick Demo - Download small dataset for testing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.yahoo_finance_collector import YahooFinanceCollector
from database.db_manager import get_db_manager

def main():
    print("\n" + "="*60)
    print("QUICK DEMO - Downloading sample data")
    print("="*60)

    # Initialize
    collector = YahooFinanceCollector()
    db = get_db_manager()
    db.create_tables()

    # Small test dataset
    symbols = ["AAPL", "MSFT", "BTC-USD", "ETH-USD", "SPY"]

    print(f"\nDownloading {len(symbols)} symbols:")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Period: 1 month")
    print(f"  Timeframe: 1 day")
    print()

    success_count = 0
    total_rows = 0

    for symbol in symbols:
        print(f"[{symbols.index(symbol)+1}/{len(symbols)}] {symbol:10} ...", end=" ")

        try:
            # Fetch data
            data = collector.fetch_historical_data(
                symbol=symbol,
                period="1mo",
                interval="1d",
                use_cache=True
            )

            if data is not None and len(data) > 0:
                # Save to database
                rows = db.insert_ohlcv_data(
                    symbol=symbol,
                    timeframe="1d",
                    data=data,
                    source="yahoo"
                )

                total_rows += rows
                success_count += 1
                print(f"[OK] {len(data)} days, {rows} new rows")
            else:
                print("[FAIL] No data")

        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")

    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE")
    print("="*60)
    print(f"Success: {success_count}/{len(symbols)} symbols")
    print(f"Total rows inserted: {total_rows}")

    # Database stats
    stats = db.get_data_statistics()
    print("\nDatabase Statistics:")
    for key, value in stats.items():
        print(f"  {key:30}: {value}")

    # Show available symbols
    available = db.get_available_symbols("1d")
    print(f"\nAvailable symbols in DB: {', '.join(available)}")

    print("\n" + "="*60)
    print("[SUCCESS] Demo complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Run full download: python scripts/download_backtest_data.py")
    print("  2. Or proceed to PHASE 3: Backtest Engine")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
