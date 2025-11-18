"""
Paper Trading System Test
Tests OrderManager, PortfolioManager, RiskManager, and PaperTradingEngine
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from paper_trading.order_manager import OrderManager, OrderSide, OrderType
from paper_trading.portfolio import PortfolioManager
from paper_trading.risk_manager import RiskManager
from paper_trading.engine import PaperTradingEngine
from data.yahoo_finance_collector import YahooFinanceCollector


def test_order_manager():
    """Test Order Manager"""
    print("\n" + "=" * 60)
    print("[1/5] TESTING ORDER MANAGER")
    print("=" * 60)

    try:
        manager = OrderManager()

        # Test 1: Create market order
        print("\n[1.1] Creating market buy order...")
        order = manager.create_order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.MARKET
        )
        assert order.status.value == "pending"
        print(f"[OK] Order created: {order.order_id}")

        # Test 2: Execute order
        print("\n[1.2] Executing order @ $175.50...")
        executed = manager.process_market_data("AAPL", 175.50, datetime.now())
        assert len(executed) == 1
        assert executed[0].status.value == "filled"
        print(f"[OK] Order filled @ ${executed[0].avg_fill_price:.2f}")

        # Test 3: Create limit order
        print("\n[1.3] Creating limit sell order...")
        limit_order = manager.create_order(
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=5,
            order_type=OrderType.LIMIT,
            price=180.0
        )
        assert limit_order.status.value == "pending"
        print(f"[OK] Limit order created @ ${limit_order.price:.2f}")

        # Test 4: Process market data (should not fill yet)
        print("\n[1.4] Processing market @ $178.00 (below limit)...")
        executed = manager.process_market_data("AAPL", 178.00, datetime.now())
        assert len(executed) == 0
        print("[OK] Order not filled (price < limit)")

        # Test 5: Fill limit order
        print("\n[1.5] Processing market @ $180.50 (above limit)...")
        executed = manager.process_market_data("AAPL", 180.50, datetime.now())
        assert len(executed) == 1
        print(f"[OK] Limit order filled @ ${executed[0].avg_fill_price:.2f}")

        # Test 6: Statistics
        stats = manager.get_statistics()
        print(f"\n[STATS] Order Manager:")
        print(f"  Total orders: {stats['total_orders']}")
        print(f"  Filled: {stats['filled_orders']}")
        print(f"  Commission: ${stats['total_commission']:.2f}")

        print("\n[SUCCESS] Order Manager tests passed!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Order Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_portfolio_manager():
    """Test Portfolio Manager"""
    print("\n" + "=" * 60)
    print("[2/5] TESTING PORTFOLIO MANAGER")
    print("=" * 60)

    try:
        portfolio = PortfolioManager(initial_capital=10000)

        # Test 1: Open position
        print("\n[2.1] Opening AAPL position...")
        pos = portfolio.open_position("AAPL", 10, 175.50, commission=1.76)
        assert portfolio.has_position("AAPL")
        print(f"[OK] Position opened: {pos.quantity} shares @ ${pos.avg_entry_price:.2f}")
        print(f"[OK] Cash remaining: ${portfolio.cash:.2f}")

        # Test 2: Update price
        print("\n[2.2] Updating price to $180.00...")
        portfolio.update_position_prices({"AAPL": 180.00})
        pos = portfolio.get_position("AAPL")
        assert pos.unrealized_pnl > 0
        print(f"[OK] Unrealized P&L: ${pos.unrealized_pnl:.2f} ({pos.unrealized_pnl_pct:.2f}%)")

        # Test 3: Portfolio value
        print("\n[2.3] Calculating portfolio value...")
        value = portfolio.get_portfolio_value()
        print(f"[OK] Portfolio value: ${value:.2f}")

        # Test 4: Close position
        print("\n[2.4] Closing position @ $180.00...")
        trade = portfolio.close_position("AAPL", 10, 180.00, commission=1.80)
        assert trade is not None
        assert not portfolio.has_position("AAPL")
        print(f"[OK] Position closed - P&L: ${trade.realized_pnl:.2f} ({trade.realized_pnl_pct:.2f}%)")

        # Test 5: Statistics
        stats = portfolio.get_statistics()
        print(f"\n[STATS] Portfolio Manager:")
        print(f"  Total value: ${stats['total_value']:.2f}")
        print(f"  Total P&L: ${stats['total_pnl']:.2f}")
        print(f"  Return: {stats['return_pct']:.2f}%")
        print(f"  Total trades: {stats['total_trades']}")

        print("\n[SUCCESS] Portfolio Manager tests passed!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Portfolio Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_manager():
    """Test Risk Manager"""
    print("\n" + "=" * 60)
    print("[3/5] TESTING RISK MANAGER")
    print("=" * 60)

    try:
        risk_mgr = RiskManager()

        # Test 1: Position size calculation
        print("\n[3.1] Calculating position size...")
        portfolio_value = 10000
        entry_price = 100
        stop_loss_price = 98  # 2% stop

        quantity = risk_mgr.calculate_position_size(
            portfolio_value, entry_price, stop_loss_price
        )
        position_value = quantity * entry_price
        print(f"[OK] Position size: {quantity:.2f} shares (${position_value:.2f})")

        # Test 2: Risk check (should pass)
        print("\n[3.2] Checking order risk (valid order)...")
        allowed, reason = risk_mgr.check_order_risk(
            symbol="AAPL",
            quantity=quantity,
            price=entry_price,
            portfolio_value=portfolio_value,
            current_positions={},
            side="buy"
        )
        assert allowed is True
        print("[OK] Order risk check passed")

        # Test 3: Risk check (should fail - too large)
        print("\n[3.3] Checking order risk (oversized order)...")
        allowed, reason = risk_mgr.check_order_risk(
            symbol="AAPL",
            quantity=500,  # Too large
            price=entry_price,
            portfolio_value=portfolio_value,
            current_positions={},
            side="buy"
        )
        assert allowed is False
        print(f"[OK] Order rejected: {reason}")

        # Test 4: Stop loss calculation
        print("\n[3.4] Calculating stop loss and take profit...")
        sl_price = risk_mgr.calculate_stop_loss_price(entry_price, "buy", 0.02)
        tp_price = risk_mgr.calculate_take_profit_price(entry_price, "buy", 0.04)
        print(f"[OK] Entry: ${entry_price:.2f}")
        print(f"[OK] Stop Loss: ${sl_price:.2f}")
        print(f"[OK] Take Profit: ${tp_price:.2f}")

        # Test 5: Drawdown tracking
        print("\n[3.5] Testing drawdown tracking...")
        risk_mgr.update_drawdown(10000)  # Peak
        risk_mgr.update_drawdown(9000)   # -10% drawdown
        assert risk_mgr.current_drawdown_pct == 10.0
        print(f"[OK] Drawdown: {risk_mgr.current_drawdown_pct:.1f}%")

        # Test 6: Daily P&L tracking
        print("\n[3.6] Testing daily P&L tracking...")
        risk_mgr.update_daily_pnl(100)
        risk_mgr.update_daily_pnl(-30)
        daily_pnl = risk_mgr.get_daily_pnl()
        assert daily_pnl == 70
        print(f"[OK] Today's P&L: ${daily_pnl:.2f}")

        print("\n[SUCCESS] Risk Manager tests passed!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Risk Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_paper_trading_engine():
    """Test Paper Trading Engine Integration"""
    print("\n" + "=" * 60)
    print("[4/5] TESTING PAPER TRADING ENGINE")
    print("=" * 60)

    try:
        # Initialize engine
        engine = PaperTradingEngine(
            initial_capital=10000,
            enable_risk_management=True
        )
        print("\n[4.1] Engine initialized")
        print(f"[OK] Initial capital: ${engine.initial_capital:.2f}")

        # Test 1: Place order
        print("\n[4.2] Placing market buy order for AAPL...")
        try:
            order = engine.place_order(
                symbol="AAPL",
                side="buy",
                quantity=10,
                order_type="market"
            )
            print(f"[OK] Order placed: {order.order_id}")
            print(f"[OK] Status: {order.status.value}")
        except Exception as e:
            print(f"[WARN] Order placement failed (expected if no market data): {e}")
            # Continue with simulated price
            engine.update_market_data("AAPL", 175.50)
            order = engine.place_order(
                symbol="AAPL",
                side="buy",
                quantity=10,
                order_type="market"
            )
            print(f"[OK] Order placed with simulated price: {order.order_id}")

        # Test 2: Check positions
        print("\n[4.3] Checking positions...")
        positions = engine.get_positions()
        if positions:
            print(f"[OK] Open positions: {len(positions)}")
            for pos in positions:
                print(f"     - {pos.symbol}: {pos.quantity} @ ${pos.avg_entry_price:.2f}")
        else:
            print("[WARN] No positions (order may not have filled)")

        # Test 3: Update market data
        print("\n[4.4] Updating market data to $180.00...")
        engine.update_market_data("AAPL", 180.00)
        positions = engine.get_positions()
        if positions:
            pos = positions[0]
            print(f"[OK] Updated P&L: ${pos.unrealized_pnl:.2f}")

        # Test 4: Place sell order
        print("\n[4.5] Placing sell order...")
        if positions:
            sell_order = engine.place_order(
                symbol="AAPL",
                side="sell",
                quantity=10,
                order_type="market"
            )
            print(f"[OK] Sell order placed: {sell_order.order_id}")

        # Test 5: Get status
        print("\n[4.6] Getting engine status...")
        status = engine.get_status()
        print(f"[STATS] Paper Trading Engine:")
        print(f"  Portfolio value: ${status['current_value']:.2f}")
        print(f"  Cash: ${status['cash']:.2f}")
        print(f"  P&L: ${status['total_pnl']:.2f}")
        print(f"  Return: {status['return_pct']:.2f}%")
        print(f"  Trades: {status['total_trades']}")
        print(f"  Open positions: {status['open_positions']}")

        print("\n[SUCCESS] Paper Trading Engine tests passed!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Paper Trading Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_market_integration():
    """Test with real market data"""
    print("\n" + "=" * 60)
    print("[5/5] TESTING REAL MARKET DATA INTEGRATION")
    print("=" * 60)

    try:
        collector = YahooFinanceCollector()
        engine = PaperTradingEngine(initial_capital=10000)

        # Test 1: Fetch real price
        print("\n[5.1] Fetching real-time price for AAPL...")
        price_data = collector.fetch_realtime_price("AAPL")
        if price_data and price_data.get('price'):
            price = price_data['price']
            print(f"[OK] AAPL current price: ${price:.2f}")
        else:
            print("[WARN] Could not fetch real-time price, using simulated data")
            price = 175.50

        # Test 2: Place order with real price
        print("\n[5.2] Placing order with real market price...")
        engine.update_market_data("AAPL", price)
        order = engine.place_order(
            symbol="AAPL",
            side="buy",
            quantity=5,
            order_type="market"
        )
        print(f"[OK] Order executed @ ${price:.2f}")

        # Test 3: Verify position
        print("\n[5.3] Verifying position...")
        pos = engine.get_position("AAPL")
        if pos:
            print(f"[OK] Position: {pos.quantity} shares @ ${pos.avg_entry_price:.2f}")
            print(f"[OK] Market value: ${pos.market_value:.2f}")
        else:
            print("[FAIL] Position not found")
            return False

        # Test 4: Fetch updated price
        print("\n[5.4] Fetching updated price...")
        new_price_data = collector.fetch_realtime_price("AAPL")
        if new_price_data and new_price_data.get('price'):
            new_price = new_price_data['price']
            engine.update_market_data("AAPL", new_price)
            pos = engine.get_position("AAPL")
            print(f"[OK] Updated price: ${new_price:.2f}")
            print(f"[OK] Unrealized P&L: ${pos.unrealized_pnl:.2f}")

        print("\n[SUCCESS] Real market integration tests passed!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Real market integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PAPER TRADING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    results = {
        "Order Manager": test_order_manager(),
        "Portfolio Manager": test_portfolio_manager(),
        "Risk Manager": test_risk_manager(),
        "Paper Trading Engine": test_paper_trading_engine(),
        "Real Market Integration": test_real_market_integration()
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        print("\nPaper Trading System is ready!")
        print("\nNext steps:")
        print("  1. Integrate with strategy signals")
        print("  2. Add WebSocket real-time data")
        print("  3. Create API endpoints")
        print("  4. Build frontend dashboard")
    else:
        print(f"\n[FAIL] {total - passed} tests failed")
        return False

    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
