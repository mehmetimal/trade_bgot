"""
Comprehensive Test Suite - All Components
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.yahoo_finance_collector import YahooFinanceCollector
from backtest.engine import BacktestEngine
from strategies.simple_ma_strategy import SimpleMAStrategy
from paper_trading import PaperTradingEngine
from database.db_manager import get_db_manager


class TestDataCollection:
    """Test data collection"""

    def test_yahoo_finance_connection(self):
        """Test Yahoo Finance API connection"""
        collector = YahooFinanceCollector()
        data = collector.fetch_historical_data("AAPL", period="1mo", interval="1d")
        assert data is not None
        assert len(data) > 0
        assert 'close' in data.columns

    def test_realtime_price_fetch(self):
        """Test real-time price fetching"""
        collector = YahooFinanceCollector()
        price_data = collector.fetch_realtime_price("AAPL")
        assert price_data is not None


class TestBacktestEngine:
    """Test backtest engine"""

    def test_backtest_execution(self):
        """Test backtest execution"""
        collector = YahooFinanceCollector()
        data = collector.fetch_historical_data("AAPL", period="6mo", interval="1d")

        strategy = SimpleMAStrategy({
            'ma_fast': 10,
            'ma_slow': 30,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })

        engine = BacktestEngine(initial_capital=10000)
        result = engine.run_backtest(data, strategy, "AAPL")

        assert result is not None
        assert result.total_trades >= 0
        assert -100 <= result.total_return_pct <= 1000

    def test_backtest_metrics(self):
        """Test backtest metrics calculation"""
        collector = YahooFinanceCollector()
        data = collector.fetch_historical_data("AAPL", period="3mo", interval="1d")

        strategy = SimpleMAStrategy({
            'ma_fast': 10,
            'ma_slow': 30,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })

        engine = BacktestEngine(initial_capital=10000)
        result = engine.run_backtest(data, strategy, "AAPL")

        assert hasattr(result, 'sharpe_ratio')
        assert hasattr(result, 'max_drawdown_pct')
        assert hasattr(result, 'win_rate')


class TestPaperTrading:
    """Test paper trading system"""

    def test_paper_trading_initialization(self):
        """Test paper trading engine initialization"""
        engine = PaperTradingEngine(initial_capital=10000)
        status = engine.get_status()

        assert status['initial_capital'] == 10000
        assert status['current_value'] == 10000
        assert status['total_trades'] == 0

    def test_order_placement(self):
        """Test order placement"""
        engine = PaperTradingEngine(initial_capital=10000)
        engine.update_market_data("AAPL", 175.00)

        order = engine.place_order("AAPL", "buy", 10, "market")
        assert order is not None
        assert order.symbol == "AAPL"

    def test_position_tracking(self):
        """Test position tracking"""
        engine = PaperTradingEngine(initial_capital=10000)
        engine.update_market_data("AAPL", 175.00)
        engine.place_order("AAPL", "buy", 10, "market")

        positions = engine.get_positions()
        assert len(positions) > 0
        assert positions[0].symbol == "AAPL"


class TestDatabase:
    """Test database operations"""

    def test_database_connection(self):
        """Test database connection"""
        db = get_db_manager()
        assert db is not None

    def test_strategy_save_retrieve(self):
        """Test strategy save and retrieve"""
        db = get_db_manager()

        strategy_id = db.save_strategy(
            name="test_strategy",
            parameters={'ma_fast': 10, 'ma_slow': 30},
            description="Test strategy"
        )

        assert strategy_id is not None


class TestIntegration:
    """Integration tests"""

    def test_full_backtest_workflow(self):
        """Test complete backtest workflow"""
        # Fetch data
        collector = YahooFinanceCollector()
        data = collector.fetch_historical_data("AAPL", period="3mo", interval="1d")

        # Create strategy
        strategy = SimpleMAStrategy({
            'ma_fast': 10,
            'ma_slow': 30,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })

        # Run backtest
        engine = BacktestEngine(initial_capital=10000)
        result = engine.run_backtest(data, strategy, "AAPL")

        # Verify results
        assert result.total_trades >= 0
        assert result.total_return_pct is not None

    def test_paper_trading_workflow(self):
        """Test complete paper trading workflow"""
        engine = PaperTradingEngine(initial_capital=10000)

        # Update market data
        engine.update_market_data("AAPL", 175.00)

        # Place buy order
        buy_order = engine.place_order("AAPL", "buy", 5, "market")
        assert buy_order.status.value == "filled"

        # Update price
        engine.update_market_data("AAPL", 180.00)

        # Place sell order
        sell_order = engine.place_order("AAPL", "sell", 5, "market")
        assert sell_order.status.value == "filled"

        # Check results
        status = engine.get_status()
        assert status['total_trades'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
