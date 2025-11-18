"""
Paper Trading Engine - Main Engine
Integrates OrderManager, PortfolioManager, and RiskManager
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging

from paper_trading.order_manager import (
    OrderManager, Order, OrderType, OrderSide, OrderStatus
)
from paper_trading.portfolio import PortfolioManager, Position, ClosedTrade
from paper_trading.risk_manager import RiskManager
from data.yahoo_finance_collector import YahooFinanceCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """
    Paper Trading Engine
    - Manages virtual trading portfolio
    - Executes orders in paper trading mode
    - Integrates with real-time market data
    - Applies risk management rules
    """

    def __init__(
        self,
        initial_capital: float = 10000,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        enable_risk_management: bool = True,
        risk_config: Optional[Dict] = None
    ):
        """
        Initialize Paper Trading Engine

        Args:
            initial_capital: Starting capital
            commission_pct: Commission percentage (e.g., 0.001 = 0.1%)
            slippage_pct: Slippage percentage (e.g., 0.0005 = 0.05%)
            enable_risk_management: Enable risk checks
            risk_config: Risk management configuration
        """
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.enable_risk_management = enable_risk_management

        # Initialize managers
        self.order_manager = OrderManager(
            commission_pct=commission_pct,
            slippage_pct=slippage_pct
        )
        self.portfolio = PortfolioManager(initial_capital=initial_capital)

        if enable_risk_management:
            risk_config = risk_config or {}
            self.risk_manager = RiskManager(**risk_config)
        else:
            self.risk_manager = None

        # Market data
        self.market_data_collector = YahooFinanceCollector()
        self.current_prices: Dict[str, float] = {}

        # State
        self.is_running = False
        self.created_at = datetime.now()

        logger.info(
            f"Paper Trading Engine initialized - "
            f"Capital: ${initial_capital:.2f}"
        )

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        auto_stop_loss: bool = False,
        stop_loss_pct: float = 0.02,
        auto_take_profit: bool = False,
        take_profit_pct: float = 0.04
    ) -> Order:
        """
        Place an order

        Args:
            symbol: Trading symbol
            side: "buy" or "sell"
            quantity: Order quantity
            order_type: "market", "limit", "stop", "stop_limit"
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            auto_stop_loss: Automatically set stop loss
            stop_loss_pct: Stop loss percentage
            auto_take_profit: Automatically set take profit
            take_profit_pct: Take profit percentage

        Returns:
            Order object
        """
        # Convert strings to enums
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order_type_enum = OrderType[order_type.upper()]

        # Get current price for risk checks
        current_price = self._get_current_price(symbol)
        if current_price is None:
            raise ValueError(f"Cannot get price for {symbol}")

        # Risk management checks
        if self.enable_risk_management and order_side == OrderSide.BUY:
            allowed, reason = self.risk_manager.check_order_risk(
                symbol=symbol,
                quantity=quantity,
                price=price or current_price,
                portfolio_value=self.portfolio.get_portfolio_value(),
                current_positions=self.portfolio.positions,
                side=side.lower()
            )

            if not allowed:
                logger.warning(f"Order rejected: {reason}")
                raise ValueError(f"Risk violation: {reason}")

        # Create order
        order = self.order_manager.create_order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            order_type=order_type_enum,
            price=price,
            stop_price=stop_price
        )

        # Auto-process market orders
        if order_type_enum == OrderType.MARKET:
            self._process_symbol_orders(symbol, current_price, datetime.now())

        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        return self.order_manager.cancel_order(order_id)

    def update_market_data(self, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """
        Update market data for a symbol

        Args:
            symbol: Trading symbol
            price: Current price
            timestamp: Data timestamp (uses now if None)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.current_prices[symbol] = price

        # Update portfolio position prices
        self.portfolio.update_position_prices({symbol: price})

        # Process pending orders
        executed_orders = self._process_symbol_orders(symbol, price, timestamp)

        # Update risk tracking
        if self.enable_risk_management:
            self.risk_manager.update_drawdown(
                self.portfolio.get_portfolio_value()
            )

        return executed_orders

    def fetch_and_update_prices(self, symbols: Optional[List[str]] = None):
        """
        Fetch current prices from market and update

        Args:
            symbols: List of symbols to update (all if None)
        """
        if symbols is None:
            # Get symbols from open positions and pending orders
            position_symbols = list(self.portfolio.positions.keys())
            order_symbols = list(set(
                o.symbol for o in self.order_manager.get_pending_orders()
            ))
            symbols = list(set(position_symbols + order_symbols))

        if not symbols:
            return

        for symbol in symbols:
            try:
                price = self.market_data_collector.fetch_realtime_price(symbol)
                if price:
                    self.update_market_data(symbol, price)
            except Exception as e:
                logger.error(f"Failed to fetch price for {symbol}: {e}")

    def _process_symbol_orders(
        self,
        symbol: str,
        price: float,
        timestamp: datetime
    ) -> List[Order]:
        """Process pending orders for a symbol"""
        # Execute eligible orders
        executed_orders = self.order_manager.process_market_data(
            symbol, price, timestamp
        )

        # Update portfolio for executed orders
        for order in executed_orders:
            try:
                if order.side == OrderSide.BUY:
                    self.portfolio.open_position(
                        symbol=order.symbol,
                        quantity=order.filled_quantity,
                        price=order.avg_fill_price,
                        commission=order.commission
                    )
                else:  # SELL
                    self.portfolio.close_position(
                        symbol=order.symbol,
                        quantity=order.filled_quantity,
                        price=order.avg_fill_price,
                        commission=order.commission
                    )

                # Update risk tracking
                if self.enable_risk_management:
                    # Calculate trade P&L
                    if order.side == OrderSide.SELL:
                        trade_pnl = self.portfolio.get_closed_trades()[-1].realized_pnl
                        self.risk_manager.update_daily_pnl(trade_pnl)

            except Exception as e:
                logger.error(f"Failed to update portfolio for order {order.order_id}: {e}")

        return executed_orders

    def _get_current_price(self, symbol: str) -> Optional[float]:
        if symbol in self.current_prices:
            return self.current_prices[symbol]
        try:
            p = self.market_data_collector.fetch_realtime_price(symbol)
            if isinstance(p, dict):
                v = p.get("price")
            else:
                v = p
            if v is not None:
                self.current_prices[symbol] = float(v)
                return float(v)
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
        return None

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        return self.portfolio.get_summary()

    def get_portfolio_statistics(self) -> Dict:
        """Get detailed portfolio statistics"""
        return self.portfolio.get_statistics()

    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        return self.portfolio.get_all_positions()

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        return self.portfolio.get_position(symbol)

    def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get orders, optionally filtered by status"""
        if status == "pending":
            return self.order_manager.get_pending_orders()
        elif status == "filled":
            return self.order_manager.get_filled_orders()
        else:
            return self.order_manager.get_all_orders()

    def get_closed_trades(self, symbol: Optional[str] = None) -> List[ClosedTrade]:
        """Get closed trades"""
        return self.portfolio.get_closed_trades(symbol)

    def get_risk_metrics(self) -> Optional[Dict]:
        """Get risk metrics"""
        if self.enable_risk_management:
            return self.risk_manager.get_risk_metrics()
        return None

    def get_status(self) -> Dict:
        """Get engine status"""
        portfolio_stats = self.portfolio.get_statistics()
        order_stats = self.order_manager.get_statistics()

        status = {
            'is_running': self.is_running,
            'initial_capital': self.initial_capital,
            'current_value': portfolio_stats['total_value'],
            'cash': portfolio_stats['cash'],
            'total_pnl': portfolio_stats['total_pnl'],
            'return_pct': portfolio_stats['return_pct'],
            'open_positions': portfolio_stats['open_positions'],
            'total_trades': portfolio_stats['total_trades'],
            'pending_orders': order_stats['pending_orders'],
            'total_commission': portfolio_stats['total_commission'],
            'created_at': self.created_at.isoformat()
        }

        if self.enable_risk_management:
            risk_metrics = self.risk_manager.get_risk_metrics()
            status['risk_metrics'] = risk_metrics

        return status

    def reset(self):
        """Reset engine to initial state"""
        self.order_manager = OrderManager(
            commission_pct=self.commission_pct,
            slippage_pct=self.slippage_pct
        )
        self.portfolio = PortfolioManager(initial_capital=self.initial_capital)

        if self.enable_risk_management:
            self.risk_manager = RiskManager()

        self.current_prices = {}
        self.is_running = False

        logger.info("Paper Trading Engine reset")


if __name__ == "__main__":
    # Test Paper Trading Engine
    print("=" * 60)
    print("PAPER TRADING ENGINE TEST")
    print("=" * 60)

    # Initialize engine
    engine = PaperTradingEngine(
        initial_capital=10000,
        enable_risk_management=True
    )

    print(f"\n[OK] Engine initialized")
    print(f"[OK] Initial capital: ${engine.initial_capital:.2f}")

    # Place market order
    print("\n[TEST 1] Place market buy order for AAPL...")
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
        print(f"[FAIL] {e}")

    # Check portfolio
    print("\n[TEST 2] Check portfolio...")
    summary = engine.get_portfolio_summary()
    print(f"[OK] Portfolio value: ${summary['portfolio_value']:.2f}")
    print(f"[OK] Cash: ${summary['cash_balance']:.2f}")
    print(f"[OK] Open positions: {summary['open_positions']}")

    # Get status
    print("\n[TEST 3] Get engine status...")
    status = engine.get_status()
    print(f"[STATS]")
    print(f"  Total Value: ${status['current_value']:.2f}")
    print(f"  P&L: ${status['total_pnl']:.2f}")
    print(f"  Return: {status['return_pct']:.2f}%")
    print(f"  Trades: {status['total_trades']}")

    print("=" * 60)
