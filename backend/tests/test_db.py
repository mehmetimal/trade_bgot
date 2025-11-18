"""
Database Test Script
Tests database operations and data storage
"""
from database.db_manager import get_db_manager
from data.yahoo_finance_collector import YahooFinanceCollector
import sys


def test_database():
    """Test database operations"""

    print("\n" + "="*60)
    print("TESTING DATABASE OPERATIONS")
    print("="*60)

    # Initialize database
    print("\n[1/6] Initializing database...")
    try:
        db = get_db_manager()
        db.create_tables()
        print("[OK] Database tables created")
    except Exception as e:
        print(f"[FAIL] Database initialization failed: {e}")
        return False

    # Test data insertion
    print("\n[2/6] Testing OHLCV data insertion...")
    try:
        collector = YahooFinanceCollector()
        data = collector.fetch_historical_data("AAPL", period="5d", interval="1d")

        if data is not None:
            rows = db.insert_ohlcv_data("AAPL", "1d", data, source="yahoo")
            print(f"[OK] Inserted {rows} rows for AAPL")
        else:
            print("[FAIL] No data to insert")
            return False
    except Exception as e:
        print(f"[FAIL] Data insertion failed: {e}")
        return False

    # Test data retrieval
    print("\n[3/6] Testing data retrieval...")
    try:
        retrieved_data = db.get_ohlcv_data("AAPL", "1d")
        if not retrieved_data.empty:
            print(f"[OK] Retrieved {len(retrieved_data)} rows for AAPL")
            print(f"  Date range: {retrieved_data.index[0]} to {retrieved_data.index[-1]}")
        else:
            print("[FAIL] No data retrieved")
            return False
    except Exception as e:
        print(f"[FAIL] Data retrieval failed: {e}")
        return False

    # Test strategy save
    print("\n[4/6] Testing strategy save...")
    try:
        strategy_id = db.save_strategy(
            name="test_ma_crossover",
            parameters={"fast_ma": 10, "slow_ma": 30},
            description="Test moving average crossover"
        )
        print(f"[OK] Strategy saved with ID: {strategy_id}")
    except Exception as e:
        print(f"[FAIL] Strategy save failed: {e}")
        return False

    # Test strategy retrieval
    print("\n[5/6] Testing strategy retrieval...")
    try:
        strategy = db.get_strategy("test_ma_crossover")
        if strategy:
            print(f"[OK] Strategy retrieved: {strategy['name']}")
            print(f"  Parameters: {strategy['parameters']}")
        else:
            print("[FAIL] Strategy not found")
            return False
    except Exception as e:
        print(f"[FAIL] Strategy retrieval failed: {e}")
        return False

    # Test database statistics
    print("\n[6/6] Testing database statistics...")
    try:
        stats = db.get_data_statistics()
        print("[OK] Database statistics:")
        for key, value in stats.items():
            print(f"  {key:30}: {value}")
    except Exception as e:
        print(f"[FAIL] Statistics failed: {e}")
        return False

    print("\n" + "="*60)
    print("[OK] ALL DATABASE TESTS PASSED!")
    print("="*60)
    print("\nDatabase is working correctly.")
    print("You can now proceed to download full backtest data.")
    print("\nNext step:")
    print("  python scripts/download_backtest_data.py")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
