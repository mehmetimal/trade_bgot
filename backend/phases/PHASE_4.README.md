# PHASE 4: Paper Trading Engine - Tamamlandı ✅

## 🎯 Tamamlanan İşler

### ✅ Task 4.1: Order Manager
- **paper_trading/order_manager.py** - Kapsamlı order yönetim sistemi:
  - Order Types: MARKET, LIMIT, STOP, STOP_LIMIT
  - Order Status tracking: PENDING, FILLED, CANCELLED, REJECTED
  - Automatic order execution simulation
  - Commission ve slippage calculation
  - Order validation ve risk checks

### ✅ Task 4.2: Portfolio Manager
- **paper_trading/portfolio.py** - Portfolio yönetim sistemi:
  - Position tracking (açık pozisyonlar)
  - Real-time P&L calculation (realized & unrealized)
  - Trade history tracking
  - Portfolio value calculation
  - Win rate ve trade statistics

### ✅ Task 4.3: Risk Manager
- **paper_trading/risk_manager.py** - Risk yönetim sistemi:
  - Position size calculation
  - Max position size limits (default: 20% per position)
  - Total exposure limits (default: 95% total)
  - Drawdown monitoring (max: 15%)
  - Daily loss limits (max: 5%)
  - Stop loss & take profit automation
  - Risk checks before order placement

### ✅ Task 4.4: Paper Trading Engine
- **paper_trading/engine.py** - Ana trading engine:
  - Integrates OrderManager, PortfolioManager, RiskManager
  - Real-time market data processing
  - Automatic order execution
  - Strategy signal integration ready
  - Portfolio tracking ve statistics
  - Risk-aware order placement

### ✅ Test Suite
- **tests/test_paper_trading.py** - Comprehensive tests:
  - OrderManager tests (5 test scenarios)
  - PortfolioManager tests (5 test scenarios)
  - RiskManager tests (6 test scenarios)
  - PaperTradingEngine integration tests
  - Real market data integration
  - **Result: 5/5 tests passed ✅**

## 📁 Proje Yapısı

```
backend/
├── paper_trading/
│   ├── __init__.py                 ✅ Module exports
│   ├── engine.py                   ✅ Main paper trading engine
│   ├── order_manager.py            ✅ Order management system
│   ├── portfolio.py                ✅ Portfolio tracking
│   └── risk_manager.py             ✅ Risk management
│
├── tests/
│   └── test_paper_trading.py       ✅ Comprehensive test suite
│
└── phases/
    ├── PHASE_3.README.md           📖 PHASE 3 docs
    └── PHASE_4.README.md           📖 This file
```

## 🚀 Hızlı Başlangıç

### 1. Test Paper Trading System

```bash
cd backend
uv run python tests/test_paper_trading.py
```

**Beklenen Çıktı:**
```
============================================================
PAPER TRADING SYSTEM - COMPREHENSIVE TEST SUITE
============================================================

[PASS] Order Manager
[PASS] Portfolio Manager
[PASS] Risk Manager
[PASS] Paper Trading Engine
[PASS] Real Market Integration

Total: 5/5 tests passed

[SUCCESS] ALL TESTS PASSED!
```

### 2. Basit Kullanım Örneği

```python
from paper_trading import PaperTradingEngine

# Initialize engine
engine = PaperTradingEngine(
    initial_capital=10000,
    enable_risk_management=True
)

# Place a market buy order
order = engine.place_order(
    symbol="AAPL",
    side="buy",
    quantity=10,
    order_type="market"
)

# Update market data (simulated or real-time)
engine.update_market_data("AAPL", 175.50)

# Check portfolio
summary = engine.get_portfolio_summary()
print(f"Portfolio Value: ${summary['portfolio_value']:.2f}")
print(f"Cash: ${summary['cash_balance']:.2f}")
print(f"P&L: ${summary['total_pnl']:.2f}")

# Place a sell order
sell_order = engine.place_order(
    symbol="AAPL",
    side="sell",
    quantity=10,
    order_type="market"
)

# Get status
status = engine.get_status()
print(f"Return: {status['return_pct']:.2f}%")
```

### 3. Real Market Data Integration

```python
from paper_trading import PaperTradingEngine
from data.yahoo_finance_collector import YahooFinanceCollector

# Initialize
engine = PaperTradingEngine(initial_capital=10000)
collector = YahooFinanceCollector()

# Fetch real-time price
price_data = collector.fetch_realtime_price("AAPL")
price = price_data['price']

# Update engine with real price
engine.update_market_data("AAPL", price)

# Place order
order = engine.place_order("AAPL", "buy", 5, "market")

# Fetch and update automatically
engine.fetch_and_update_prices(["AAPL", "GOOGL", "MSFT"])
```

## 📊 Özellikler

### 🎯 Order Management

**Order Types:**
- **MARKET**: Immediate execution at current price
- **LIMIT**: Execute only at specified price or better
- **STOP**: Trigger when price reaches stop level
- **STOP_LIMIT**: Combination of stop and limit

```python
from paper_trading.order_manager import OrderManager, OrderType, OrderSide

manager = OrderManager()

# Market order
market_order = manager.create_order(
    symbol="AAPL",
    side=OrderSide.BUY,
    quantity=10,
    order_type=OrderType.MARKET
)

# Limit order
limit_order = manager.create_order(
    symbol="AAPL",
    side=OrderSide.SELL,
    quantity=10,
    order_type=OrderType.LIMIT,
    price=180.00
)

# Process market data
executed = manager.process_market_data("AAPL", 175.50, datetime.now())
```

### 📈 Portfolio Management

**Features:**
- Position tracking
- Real-time P&L calculation
- Trade history
- Statistics

```python
from paper_trading.portfolio import PortfolioManager

portfolio = PortfolioManager(initial_capital=10000)

# Open position
position = portfolio.open_position(
    symbol="AAPL",
    quantity=10,
    price=175.50,
    commission=1.76
)

# Update prices
portfolio.update_position_prices({"AAPL": 180.00})

# Get unrealized P&L
pos = portfolio.get_position("AAPL")
print(f"Unrealized P&L: ${pos.unrealized_pnl:.2f}")

# Close position
trade = portfolio.close_position(
    symbol="AAPL",
    quantity=10,
    price=180.00,
    commission=1.80
)

# Statistics
stats = portfolio.get_statistics()
print(f"Win Rate: {stats['win_rate']:.2f}%")
print(f"Total P&L: ${stats['total_pnl']:.2f}")
```

### 🔧 Risk Management

**Risk Controls:**
- Position size limits
- Exposure limits
- Drawdown monitoring
- Daily loss limits
- Stop loss automation

```python
from paper_trading.risk_manager import RiskManager

risk_mgr = RiskManager(
    max_position_size_pct=0.2,      # Max 20% per position
    max_total_exposure_pct=0.95,    # Max 95% total
    max_drawdown_pct=0.15,          # Max 15% drawdown
    max_daily_loss_pct=0.05         # Max 5% daily loss
)

# Calculate optimal position size
quantity = risk_mgr.calculate_position_size(
    portfolio_value=10000,
    entry_price=100,
    stop_loss_price=98  # 2% stop
)

# Check order risk
allowed, reason = risk_mgr.check_order_risk(
    symbol="AAPL",
    quantity=quantity,
    price=100,
    portfolio_value=10000,
    current_positions={},
    side="buy"
)

# Calculate stop loss and take profit
sl_price = risk_mgr.calculate_stop_loss_price(100, "buy", 0.02)
tp_price = risk_mgr.calculate_take_profit_price(100, "buy", 0.04)

print(f"Entry: $100.00")
print(f"Stop Loss: ${sl_price:.2f}")
print(f"Take Profit: ${tp_price:.2f}")
```

## 📊 Test Sonuçları

### Test 1: Order Manager ✅
```
[OK] Market order created and filled
[OK] Limit order created and filled at correct price
[OK] Order execution logic working correctly
[OK] Commission: $2.66 (0.1% of notional)
```

### Test 2: Portfolio Manager ✅
```
[OK] Position opened: 10 shares @ $175.50
[OK] Unrealized P&L: $45.00 (2.56%)
[OK] Position closed: P&L: $43.20 (2.46%)
[OK] Return: 0.41%
```

### Test 3: Risk Manager ✅
```
[OK] Position size calculation: 20 shares ($2000, 20% of portfolio)
[OK] Risk check passed for valid orders
[OK] Oversized orders rejected (500% > 20% limit)
[OK] Drawdown tracking: 10.0%
[OK] Daily P&L tracking: $70.00
```

### Test 4: Paper Trading Engine ✅
```
[OK] Engine initialized: $10,000 capital
[OK] Market order placed and filled
[OK] Portfolio value updated correctly
[OK] P&L calculated: $41.42 (0.40% return)
[OK] Risk metrics tracked
```

### Test 5: Real Market Integration ✅
```
[OK] Real-time price fetched: $267.46
[OK] Order executed at market price
[OK] Position verified: 5 shares @ $267.59
[OK] Real-time P&L tracking working
```

## 🎓 Kullanım Senaryoları

### Scenario 1: Basic Trading

```python
from paper_trading import PaperTradingEngine

engine = PaperTradingEngine(initial_capital=10000)

# Buy
engine.update_market_data("AAPL", 175.00)
buy_order = engine.place_order("AAPL", "buy", 10, "market")

# Wait for price movement
engine.update_market_data("AAPL", 180.00)

# Sell
sell_order = engine.place_order("AAPL", "sell", 10, "market")

# Check results
status = engine.get_status()
print(f"Total P&L: ${status['total_pnl']:.2f}")
```

### Scenario 2: Limit Orders

```python
# Place limit sell order
engine.update_market_data("AAPL", 175.00)
engine.place_order("AAPL", "buy", 10, "market")

# Set limit sell @ $180
limit_order = engine.place_order(
    symbol="AAPL",
    side="sell",
    quantity=10,
    order_type="limit",
    price=180.00
)

# Update price (below limit - won't fill)
engine.update_market_data("AAPL", 178.00)
print("Order still pending...")

# Update price (above limit - will fill)
engine.update_market_data("AAPL", 180.50)
print("Order filled!")
```

### Scenario 3: Risk Management

```python
engine = PaperTradingEngine(
    initial_capital=10000,
    enable_risk_management=True,
    risk_config={
        'max_position_size_pct': 0.15,  # Max 15% per position
        'max_drawdown_pct': 0.10,       # Max 10% drawdown
        'max_daily_loss_pct': 0.03      # Max 3% daily loss
    }
)

# Valid order (within limits)
try:
    engine.place_order("AAPL", "buy", 5, "market")
    print("Order accepted")
except ValueError as e:
    print(f"Order rejected: {e}")

# Invalid order (too large)
try:
    engine.place_order("AAPL", "buy", 100, "market")
except ValueError as e:
    print(f"Order rejected: {e}")
    # Output: "Order rejected: Risk violation: Position size 500.0% exceeds limit 15.0%"
```

### Scenario 4: Strategy Integration

```python
from strategies.simple_ma_strategy import SimpleMAStrategy
from data.yahoo_finance_collector import YahooFinanceCollector

# Initialize
collector = YahooFinanceCollector()
engine = PaperTradingEngine(initial_capital=10000)
strategy = SimpleMAStrategy({
    'ma_fast': 10,
    'ma_slow': 30,
    'stop_loss_pct': 0.02,
    'take_profit_pct': 0.04
})

# Get historical data
data = collector.fetch_historical_data("AAPL", period="1mo", interval="1d")

# Generate signals
signals = strategy.generate_signals(data)

# Execute signals (simple example)
for i in range(len(data)):
    current_price = data.iloc[i]['close']

    # Update market data
    engine.update_market_data("AAPL", current_price)

    # Entry signal
    if signals.entries.iloc[i] and not engine.get_position("AAPL"):
        engine.place_order("AAPL", "buy", 10, "market")

    # Exit signal
    elif signals.exits.iloc[i] and engine.get_position("AAPL"):
        engine.place_order("AAPL", "sell", 10, "market")

# Results
status = engine.get_status()
print(f"Final P&L: ${status['total_pnl']:.2f}")
print(f"Return: {status['return_pct']:.2f}%")
```

## 🐛 Troubleshooting

### Issue: Order not executing
```python
# Check pending orders
pending = engine.get_orders(status="pending")
print(f"Pending orders: {len(pending)}")

# Make sure to update market data
engine.update_market_data("AAPL", current_price)
```

### Issue: Risk violation
```python
# Check risk metrics
risk_metrics = engine.get_risk_metrics()
print(f"Current drawdown: {risk_metrics['current_drawdown_pct']:.2f}%")
print(f"Daily P&L: ${risk_metrics['daily_pnl']:.2f}")

# Adjust risk parameters
engine.risk_manager.max_position_size_pct = 0.30  # Increase to 30%
```

### Issue: Position not found
```python
# List all positions
positions = engine.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.quantity} @ ${pos.avg_entry_price:.2f}")

# Check if position exists
has_aapl = engine.portfolio.has_position("AAPL")
print(f"Has AAPL position: {has_aapl}")
```

## 📊 API Reference

### PaperTradingEngine

**Initialize:**
```python
engine = PaperTradingEngine(
    initial_capital=10000,
    commission_pct=0.001,
    slippage_pct=0.0005,
    enable_risk_management=True,
    risk_config={}
)
```

**Methods:**
- `place_order(symbol, side, quantity, order_type, price, stop_price)` - Place an order
- `cancel_order(order_id)` - Cancel pending order
- `update_market_data(symbol, price, timestamp)` - Update market data
- `fetch_and_update_prices(symbols)` - Fetch real-time prices
- `get_portfolio_summary()` - Get portfolio summary
- `get_positions()` - Get all positions
- `get_position(symbol)` - Get specific position
- `get_orders(status)` - Get orders by status
- `get_closed_trades(symbol)` - Get trade history
- `get_status()` - Get engine status

### OrderManager

**Methods:**
- `create_order(symbol, side, quantity, order_type, price, stop_price)` - Create order
- `process_market_data(symbol, price, timestamp)` - Process market data
- `cancel_order(order_id)` - Cancel order
- `get_pending_orders(symbol)` - Get pending orders
- `get_filled_orders(symbol)` - Get filled orders

### PortfolioManager

**Methods:**
- `open_position(symbol, quantity, price, commission)` - Open position
- `close_position(symbol, quantity, price, commission)` - Close position
- `update_position_prices(prices)` - Update prices
- `get_portfolio_value()` - Get total portfolio value
- `get_total_pnl()` - Get total P&L
- `get_statistics()` - Get portfolio statistics

### RiskManager

**Methods:**
- `check_order_risk(symbol, quantity, price, portfolio_value, ...)` - Check risk
- `calculate_position_size(portfolio_value, entry_price, stop_loss_price)` - Calculate size
- `calculate_stop_loss_price(entry_price, side, stop_loss_pct)` - Calculate SL
- `calculate_take_profit_price(entry_price, side, take_profit_pct)` - Calculate TP
- `update_drawdown(portfolio_value)` - Update drawdown
- `get_risk_metrics()` - Get risk metrics

## ✅ Acceptance Criteria - Tamamlandı

- ✅ Order Manager implement edildi (MARKET, LIMIT, STOP, STOP_LIMIT)
- ✅ Portfolio Manager çalışıyor (positions, P&L tracking)
- ✅ Risk Manager fonksiyonel (position limits, drawdown, daily loss)
- ✅ Paper Trading Engine production-ready
- ✅ Real-time market data entegrasyonu çalışıyor
- ✅ Slippage ve commission simülasyonu gerçekçi
- ✅ Test suite passing (5/5 tests)
- ✅ Strategy integration ready

## 🎯 Sonraki Adımlar (PHASE 5)

PHASE 4 tamamlandı! Şimdi PHASE 5'e geçebiliriz:

1. **FastAPI Backend** (api/main.py)
   - REST API endpoints
   - WebSocket for real-time data
   - Authentication

2. **Real-time Data Pipeline** (api/websocket.py)
   - Market data streaming
   - Client subscription management

3. **API Integration** (api/routes/)
   - Backtest endpoints
   - Paper trading endpoints
   - Strategy endpoints
   - Portfolio endpoints

```bash
# Hazır olduğunda PHASE 5'e geç
python tests/test_paper_trading.py  # Önce PHASE 4'ü doğrula
# Sonra PHASE 5'e başla
```

---

**PHASE 4 Status:** ✅ **COMPLETE & TESTED**
**Estimated Time:** ~4 saat
**Next:** PHASE 5 - Backend API (FastAPI)
