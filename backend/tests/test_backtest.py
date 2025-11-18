"""
Backtest Engine Test
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.yahoo_finance_collector import YahooFinanceCollector
from backtest.engine import BacktestEngine
from strategies.simple_ma_strategy import SimpleMAStrategy, RSIMAStrategy
from database.db_manager import get_db_manager


def test_backtest_engine():
    """Test backtest engine with real data"""

    print("\n" + "="*60)
    print("BACKTEST ENGINE TEST")
    print("="*60)

    # Initialize
    collector = YahooFinanceCollector()
    db = get_db_manager()

    # Test 1: MA Crossover Strategy on AAPL
    print("\n[1/3] Testing MA Crossover Strategy on AAPL...")
    print("-"*60)

    try:
        # Get data
        data = collector.fetch_historical_data("AAPL", period="1y", interval="1d")
        if data is None or len(data) < 100:
            print("[FAIL] Insufficient data")
            return False

        print(f"[OK] Data loaded: {len(data)} days")

        # Create strategy
        strategy = SimpleMAStrategy(parameters={
            'ma_fast': 10,
            'ma_slow': 30,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })
        print(f"[OK] Strategy created: {strategy.name}")

        # Run backtest
        engine = BacktestEngine(initial_capital=10000)
        result = engine.run_backtest(data, strategy, symbol="AAPL")

        # Print results
        result.print_summary()

        # Validate results
        assert result.total_trades >= 0, "Total trades should be >= 0"
        assert -100 <= result.total_return_pct <= 1000, "Return % should be reasonable"

        print("\n[OK] MA Crossover backtest passed")

    except Exception as e:
        print(f"[FAIL] MA Crossover test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: RSI + MA Strategy on BTC
    print("\n[2/3] Testing RSI + MA Strategy on BTC-USD...")
    print("-"*60)

    try:
        # Get data
        data = collector.fetch_historical_data("BTC-USD", period="6mo", interval="1d")
        if data is None or len(data) < 100:
            print("[FAIL] Insufficient data")
            return False

        print(f"[OK] Data loaded: {len(data)} days")

        # Create strategy
        strategy = RSIMAStrategy(parameters={
            'ma_slow': 50,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.06
        })
        print(f"[OK] Strategy created: {strategy.name}")

        # Run backtest
        engine = BacktestEngine(initial_capital=10000)
        result = engine.run_backtest(data, strategy, symbol="BTC-USD")

        # Print results
        result.print_summary()

        print("\n[OK] RSI + MA backtest passed")

    except Exception as e:
        print(f"[FAIL] RSI + MA test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Save results to database
    print("\n[3/3] Testing database save...")
    print("-"*60)

    try:
        # Save strategy
        strategy_id = db.save_strategy(
            name="test_ma_10_30",
            parameters=strategy.parameters,
            description="Test MA crossover 10/30"
        )
        print(f"[OK] Strategy saved with ID: {strategy_id}")

        # Save backtest result
        backtest_data = {
            'initial_capital': 10000,
            'final_value': result.total_return + 10000,
            'total_return': result.total_return,
            'total_return_pct': result.total_return_pct,
            'sharpe_ratio': result.sharpe_ratio,
            'sortino_ratio': result.sortino_ratio,
            'max_drawdown': result.max_drawdown,
            'max_drawdown_pct': result.max_drawdown_pct,
            'total_trades': result.total_trades,
            'winning_trades': result.winning_trades,
            'losing_trades': result.losing_trades,
            'win_rate': result.win_rate,
            'avg_win': result.avg_win,
            'avg_loss': result.avg_loss,
            'profit_factor': result.profit_factor,
            'parameters': strategy.parameters,
            'trades': [t.to_dict() for t in result.trades]
        }

        backtest_id = db.save_backtest_result(
            strategy_id=strategy_id,
            symbol="BTC-USD",
            timeframe="1d",
            start_date=data.index[0],
            end_date=data.index[-1],
            result=backtest_data
        )
        print(f"[OK] Backtest result saved with ID: {backtest_id}")

        # Retrieve results
        results = db.get_backtest_results(strategy_id=strategy_id, limit=5)
        print(f"[OK] Retrieved {len(results)} backtest results")

    except Exception as e:
        print(f"[FAIL] Database save failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*60)
    print("[SUCCESS] ALL BACKTEST TESTS PASSED!")
    print("="*60)
    print("\nBacktest engine is working correctly.")
    print("\nNext steps:")
    print("  1. Create more strategies")
    print("  2. Run parameter optimization")
    print("  3. Proceed to PHASE 4: Paper Trading")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    import sys
    success = test_backtest_engine()
    sys.exit(0 if success else 1)
