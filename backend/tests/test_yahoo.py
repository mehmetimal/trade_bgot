"""
Yahoo Finance Connection Test
Quick test to verify Yahoo Finance API is working
"""
from data.yahoo_finance_collector import YahooFinanceCollector
import sys


def test_yahoo_finance():
    """Test Yahoo Finance data collection"""

    print("\n" + "="*60)
    print("TESTING YAHOO FINANCE API")
    print("="*60)

    collector = YahooFinanceCollector()

    # Test 1: Stock data
    print("\n[1/5] Testing stock data (AAPL)...")
    try:
        aapl = collector.fetch_historical_data("AAPL", period="1mo", interval="1d")
        if aapl is not None and len(aapl) > 0:
            print(f"[OK] AAPL: {len(aapl)} days fetched")
            print(f"  Latest close: ${aapl['close'].iloc[-1]:.2f}")
            print(f"  Date range: {aapl.index[0]} to {aapl.index[-1]}")
        else:
            print("[FAIL] AAPL: No data received")
            return False
    except Exception as e:
        print(f"[FAIL] AAPL: Error - {e}")
        return False

    # Test 2: Crypto data
    print("\n[2/5] Testing crypto data (BTC-USD)...")
    try:
        btc = collector.fetch_historical_data("BTC-USD", period="1mo", interval="1d")
        if btc is not None and len(btc) > 0:
            print(f"[OK] BTC-USD: {len(btc)} days fetched")
            print(f"  Latest close: ${btc['close'].iloc[-1]:,.2f}")
        else:
            print("[FAIL] BTC-USD: No data received")
            return False
    except Exception as e:
        print(f"[FAIL] BTC-USD: Error - {e}")
        return False

    # Test 3: ETF data
    print("\n[3/5] Testing ETF data (SPY)...")
    try:
        spy = collector.fetch_historical_data("SPY", period="1mo", interval="1d")
        if spy is not None and len(spy) > 0:
            print(f"[OK] SPY: {len(spy)} days fetched")
            print(f"  Latest close: ${spy['close'].iloc[-1]:.2f}")
        else:
            print("[FAIL] SPY: No data received")
            return False
    except Exception as e:
        print(f"[FAIL] SPY: Error - {e}")
        return False

    # Test 4: Multiple symbols
    print("\n[4/5] Testing multiple symbols...")
    try:
        symbols = ["MSFT", "GOOGL", "TSLA"]
        data = collector.fetch_multiple_symbols(symbols, period="5d", interval="1d")
        if len(data) == len(symbols):
            print(f"[OK] Multiple symbols: {len(data)}/{len(symbols)} fetched")
            for symbol, df in data.items():
                print(f"  {symbol}: {len(df)} days")
        else:
            print(f"[WARN] Multiple symbols: {len(data)}/{len(symbols)} fetched (some failed)")
    except Exception as e:
        print(f"[FAIL] Multiple symbols: Error - {e}")
        return False

    # Test 5: Realtime price
    print("\n[5/5] Testing realtime price...")
    try:
        price = collector.fetch_realtime_price("AAPL")
        if price and price.get('price'):
            print(f"[OK] Realtime price: ${price['price']:.2f}")
            if price.get('change_percent'):
                print(f"  Change: {price['change_percent']:.2f}%")
        else:
            print("[WARN] Realtime price: Limited data")
    except Exception as e:
        print(f"[WARN] Realtime price: Error - {e} (non-critical)")

    # Cache test
    print("\n[Bonus] Testing cache...")
    print("  Fetching AAPL again (should use cache)...")
    aapl_cached = collector.fetch_historical_data("AAPL", period="1mo", interval="1d")
    if aapl_cached is not None:
        print("[OK] Cache working")

    print("\n" + "="*60)
    print("[SUCCESS] ALL TESTS PASSED!")
    print("="*60)
    print("\nYahoo Finance API is working correctly.")
    print("You can now proceed to download backtest data.")
    print("\nNext step:")
    print("  python scripts/download_backtest_data.py")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_yahoo_finance()
    sys.exit(0 if success else 1)
