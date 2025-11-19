"""
Order Management System for Paper Trading
Handles order creation, tracking, and execution simulation
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    commission: float = 0.0
    slippage: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['side'] = self.side.value
        d['order_type'] = self.order_type.value
        d['status'] = self.status.value
        d['created_at'] = self.created_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        if self.filled_at:
            d['filled_at'] = self.filled_at.isoformat()
        return d


class OrderManager:
    """
    Order Management System
    - Creates and tracks orders
    - Simulates order execution
    - Manages order lifecycle
    """

    def __init__(
        self,
        commission_pct: float = 0.001,  # 0.1%
        slippage_pct: float = 0.0005     # 0.05%
    ):
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.orders: Dict[str, Order] = {}
        self.pending_orders: List[str] = []

    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """
        Create a new order

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            order_type: MARKET, LIMIT, STOP, STOP_LIMIT
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Order object
        """
        # Validation
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and price is None:
            raise ValueError("Limit orders require a price")

        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and stop_price is None:
            raise ValueError("Stop orders require a stop price")

        # Create order
        order = Order(
            order_id=self._generate_order_id(),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )

        self.orders[order.order_id] = order
        self.pending_orders.append(order.order_id)

        logger.info(f"Order created: {order.order_id} - {side.value} {quantity} {symbol}")

        # Audit logging
        try:
            from utils.audit_logger import get_audit_logger
            audit_logger = get_audit_logger()
            audit_logger.log_trade(
                action=f"ORDER_CREATED_{side.value.upper()}",
                symbol=symbol,
                quantity=quantity,
                price=price or 0,
                order_type=order_type.value,
                metadata={
                    "order_id": order.order_id,
                    "stop_price": stop_price
                }
            )
        except Exception as e:
            logger.warning(f"Failed to audit log order creation: {e}")

        return order

    def process_market_data(
        self,
        symbol: str,
        current_price: float,
        timestamp: datetime
    ) -> List[Order]:
        """
        Process market data and execute eligible orders

        Args:
            symbol: Trading symbol
            current_price: Current market price
            timestamp: Current timestamp

        Returns:
            List of executed orders
        """
        executed_orders = []

        # Process pending orders for this symbol
        pending_to_remove = []

        for order_id in self.pending_orders:
            order = self.orders[order_id]

            # Skip if not for this symbol
            if order.symbol != symbol:
                continue

            # Check if order should be filled
            if self._should_fill_order(order, current_price):
                filled_order = self._execute_order(order, current_price, timestamp)
                executed_orders.append(filled_order)
                pending_to_remove.append(order_id)

        # Remove filled orders from pending list
        for order_id in pending_to_remove:
            self.pending_orders.remove(order_id)

        return executed_orders

    def _should_fill_order(self, order: Order, current_price: float) -> bool:
        """Check if order should be filled at current price"""

        if order.order_type == OrderType.MARKET:
            return True

        elif order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                # Buy limit: fill if price <= limit price
                return current_price <= order.price
            else:
                # Sell limit: fill if price >= limit price
                return current_price >= order.price

        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY:
                # Buy stop: fill if price >= stop price
                return current_price >= order.stop_price
            else:
                # Sell stop: fill if price <= stop price
                return current_price <= order.stop_price

        elif order.order_type == OrderType.STOP_LIMIT:
            # First check if stop is triggered
            stop_triggered = False
            if order.side == OrderSide.BUY:
                stop_triggered = current_price >= order.stop_price
            else:
                stop_triggered = current_price <= order.stop_price

            # Then check limit condition
            if stop_triggered:
                if order.side == OrderSide.BUY:
                    return current_price <= order.price
                else:
                    return current_price >= order.price

        return False

    def _execute_order(
        self,
        order: Order,
        fill_price: float,
        timestamp: datetime
    ) -> Order:
        """Execute an order"""

        # Apply slippage
        if order.side == OrderSide.BUY:
            actual_fill_price = fill_price * (1 + self.slippage_pct)
        else:
            actual_fill_price = fill_price * (1 - self.slippage_pct)

        # Calculate commission
        notional_value = order.quantity * actual_fill_price
        commission = notional_value * self.commission_pct

        # Update order
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.avg_fill_price = actual_fill_price
        order.filled_at = timestamp
        order.updated_at = timestamp
        order.commission = commission
        order.slippage = abs(actual_fill_price - fill_price) * order.quantity

        logger.info(
            f"Order filled: {order.order_id} - "
            f"{order.side.value} {order.quantity} {order.symbol} @ ${actual_fill_price:.2f}"
        )

        # Audit logging
        try:
            from utils.audit_logger import get_audit_logger
            audit_logger = get_audit_logger()
            audit_logger.log_trade(
                action=f"ORDER_FILLED_{order.side.value.upper()}",
                symbol=order.symbol,
                quantity=order.quantity,
                price=actual_fill_price,
                order_type=order.order_type.value,
                metadata={
                    "order_id": order.order_id,
                    "commission": commission,
                    "slippage": order.slippage,
                    "notional_value": notional_value,
                    "fill_timestamp": timestamp.isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to audit log order execution: {e}")

        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        if order_id not in self.orders:
            logger.warning(f"Order not found: {order_id}")
            return False

        order = self.orders[order_id]

        if order.status != OrderStatus.PENDING:
            logger.warning(f"Cannot cancel order in status: {order.status.value}")
            return False

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()

        if order_id in self.pending_orders:
            self.pending_orders.remove(order_id)

        logger.info(f"Order cancelled: {order_id}")
        return True

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all pending orders, optionally filtered by symbol"""
        pending = [self.orders[oid] for oid in self.pending_orders]

        if symbol:
            pending = [o for o in pending if o.symbol == symbol]

        return pending

    def get_filled_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all filled orders, optionally filtered by symbol"""
        filled = [
            o for o in self.orders.values()
            if o.status == OrderStatus.FILLED
        ]

        if symbol:
            filled = [o for o in filled if o.symbol == symbol]

        return filled

    def get_all_orders(self) -> List[Order]:
        """Get all orders"""
        return list(self.orders.values())

    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        return f"ORD-{uuid.uuid4().hex[:12].upper()}"

    def get_statistics(self) -> Dict:
        """Get order statistics"""
        total_orders = len(self.orders)
        filled_orders = len([o for o in self.orders.values() if o.status == OrderStatus.FILLED])
        pending_orders = len(self.pending_orders)
        cancelled_orders = len([o for o in self.orders.values() if o.status == OrderStatus.CANCELLED])

        total_commission = sum(
            o.commission for o in self.orders.values()
            if o.status == OrderStatus.FILLED
        )

        total_slippage = sum(
            o.slippage for o in self.orders.values()
            if o.status == OrderStatus.FILLED
        )

        return {
            'total_orders': total_orders,
            'filled_orders': filled_orders,
            'pending_orders': pending_orders,
            'cancelled_orders': cancelled_orders,
            'total_commission': total_commission,
            'total_slippage': total_slippage
        }


if __name__ == "__main__":
    # Test OrderManager
    print("=" * 60)
    print("ORDER MANAGER TEST")
    print("=" * 60)

    manager = OrderManager()

    # Create market order
    order1 = manager.create_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=10,
        order_type=OrderType.MARKET
    )
    print(f"\n[OK] Market order created: {order1.order_id}")

    # Create limit order
    order2 = manager.create_order(
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=5,
        order_type=OrderType.LIMIT,
        price=180.0
    )
    print(f"[OK] Limit order created: {order2.order_id}")

    # Simulate market data
    print("\n[INFO] Processing market data @ $175.50")
    executed = manager.process_market_data("AAPL", 175.50, datetime.now())
    print(f"[OK] {len(executed)} orders executed")

    # Check statistics
    stats = manager.get_statistics()
    print(f"\n[STATS]")
    print(f"  Total Orders: {stats['total_orders']}")
    print(f"  Filled: {stats['filled_orders']}")
    print(f"  Pending: {stats['pending_orders']}")
    print(f"  Total Commission: ${stats['total_commission']:.2f}")

    print("=" * 60)
