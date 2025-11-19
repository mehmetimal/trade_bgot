#!/usr/bin/env python
"""
Create test position for demo
"""
import sys
sys.path.insert(0, '/app')

from paper_trading.engine import PaperTradingEngine
from datetime import datetime

# Engine oluştur
print("Creating Paper Trading Engine...")
engine = PaperTradingEngine(initial_capital=10000)

# THYAO.IS için market order
print("Creating BUY order for THYAO.IS...")
order = engine.place_order(
    symbol='THYAO.IS',
    side='buy',
    quantity=100,
    order_type='market'
)

print(f"\n✅ Order created successfully!")
print(f"   Order ID: {order.order_id}")
print(f"   Symbol: {order.symbol}")
print(f"   Side: {order.side.value}")
print(f"   Quantity: {order.quantity}")
print(f"   Status: {order.status.value}")

# Pozisyonları kontrol et
print("\n📊 Current Positions:")
positions = engine.get_positions()
print(f"   Total positions: {len(positions)}")

for pos in positions:
    print(f"   - {pos.symbol}: {pos.quantity} shares @ ${pos.avg_entry_price:.2f}")
    print(f"     Current P&L: ${pos.unrealized_pnl:.2f}")

print("\n✨ Test position created successfully!")
