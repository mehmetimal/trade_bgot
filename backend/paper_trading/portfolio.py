"""
Portfolio Manager for Paper Trading
Tracks positions, cash, and P&L
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open position"""
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    market_value: float = 0.0
    cost_basis: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_price(self, current_price: float):
        """Update current price and recalculate metrics"""
        self.current_price = current_price
        self.market_value = self.quantity * current_price
        self.cost_basis = self.quantity * self.avg_entry_price
        self.unrealized_pnl = self.market_value - self.cost_basis
        self.unrealized_pnl_pct = (self.unrealized_pnl / self.cost_basis) * 100 if self.cost_basis > 0 else 0
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['opened_at'] = self.opened_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        return d


@dataclass
class ClosedTrade:
    """Represents a closed trade"""
    symbol: str
    quantity: float
    entry_price: float
    exit_price: float
    realized_pnl: float
    realized_pnl_pct: float
    commission: float
    opened_at: datetime
    closed_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['opened_at'] = self.opened_at.isoformat()
        d['closed_at'] = self.closed_at.isoformat()
        return d


class PortfolioManager:
    """
    Portfolio Management System
    - Tracks cash and positions
    - Calculates P&L
    - Manages trade history
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[ClosedTrade] = []
        self.total_commission_paid: float = 0.0
        self.created_at = datetime.now()

    def open_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        commission: float
    ) -> Position:
        """
        Open a new position or add to existing position

        Args:
            symbol: Trading symbol
            quantity: Quantity to buy (positive) or sell (negative)
            price: Execution price
            commission: Commission paid

        Returns:
            Position object
        """
        cost = abs(quantity * price) + commission

        # Check sufficient cash
        if cost > self.cash:
            raise ValueError(f"Insufficient cash: ${self.cash:.2f} < ${cost:.2f}")

        # Update cash
        self.cash -= cost
        self.total_commission_paid += commission

        if symbol in self.positions:
            # Add to existing position
            pos = self.positions[symbol]
            new_quantity = pos.quantity + quantity
            new_cost_basis = pos.cost_basis + (quantity * price)
            new_avg_price = new_cost_basis / new_quantity if new_quantity != 0 else 0

            pos.quantity = new_quantity
            pos.avg_entry_price = new_avg_price
            pos.cost_basis = new_cost_basis
            pos.update_price(price)

            logger.info(
                f"Added to position: {symbol} - "
                f"Quantity: {pos.quantity:.2f} @ Avg: ${pos.avg_entry_price:.2f}"
            )
        else:
            # Create new position
            pos = Position(
                symbol=symbol,
                quantity=quantity,
                avg_entry_price=price,
                current_price=price
            )
            pos.update_price(price)
            self.positions[symbol] = pos

            logger.info(
                f"Opened position: {symbol} - "
                f"{quantity:.2f} @ ${price:.2f}"
            )

        return pos

    def close_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        commission: float
    ) -> Optional[ClosedTrade]:
        """
        Close a position (full or partial)

        Args:
            symbol: Trading symbol
            quantity: Quantity to close
            price: Exit price
            commission: Commission paid

        Returns:
            ClosedTrade object if position closed, None otherwise
        """
        if symbol not in self.positions:
            raise ValueError(f"No position found for {symbol}")

        pos = self.positions[symbol]

        if quantity > pos.quantity:
            raise ValueError(
                f"Cannot close {quantity} shares, only {pos.quantity} available"
            )

        # Calculate realized P&L
        proceeds = quantity * price - commission
        cost_basis = quantity * pos.avg_entry_price
        realized_pnl = proceeds - cost_basis
        realized_pnl_pct = (realized_pnl / cost_basis) * 100 if cost_basis > 0 else 0

        # Update cash
        self.cash += proceeds
        self.total_commission_paid += commission

        # Create closed trade record
        trade = ClosedTrade(
            symbol=symbol,
            quantity=quantity,
            entry_price=pos.avg_entry_price,
            exit_price=price,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            commission=commission,
            opened_at=pos.opened_at,
            closed_at=datetime.now()
        )
        self.closed_trades.append(trade)

        # Update or remove position
        if quantity == pos.quantity:
            # Full close
            del self.positions[symbol]
            logger.info(
                f"Closed position: {symbol} - "
                f"{quantity:.2f} @ ${price:.2f} - P&L: ${realized_pnl:.2f}"
            )
        else:
            # Partial close
            pos.quantity -= quantity
            pos.cost_basis -= cost_basis
            pos.update_price(price)
            logger.info(
                f"Partially closed position: {symbol} - "
                f"{quantity:.2f} @ ${price:.2f} - Remaining: {pos.quantity:.2f}"
            )

        return trade

    def update_position_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions

        Args:
            prices: Dictionary of {symbol: current_price}
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value (cash + positions)"""
        positions_value = sum(
            pos.market_value for pos in self.positions.values()
        )
        return self.cash + positions_value

    def get_total_pnl(self) -> float:
        """Calculate total P&L (realized + unrealized)"""
        realized_pnl = sum(trade.realized_pnl for trade in self.closed_trades)
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        return realized_pnl + unrealized_pnl

    def get_realized_pnl(self) -> float:
        """Calculate total realized P&L"""
        return sum(trade.realized_pnl for trade in self.closed_trades)

    def get_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_return_pct(self) -> float:
        """Calculate total return percentage"""
        current_value = self.get_portfolio_value()
        return ((current_value - self.initial_capital) / self.initial_capital) * 100

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol"""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if position exists"""
        return symbol in self.positions

    def get_all_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())

    def get_closed_trades(self, symbol: Optional[str] = None) -> List[ClosedTrade]:
        """Get closed trades, optionally filtered by symbol"""
        if symbol:
            return [t for t in self.closed_trades if t.symbol == symbol]
        return self.closed_trades

    def get_statistics(self) -> Dict:
        """Get portfolio statistics"""
        total_value = self.get_portfolio_value()
        total_pnl = self.get_total_pnl()
        realized_pnl = self.get_realized_pnl()
        unrealized_pnl = self.get_unrealized_pnl()
        return_pct = self.get_return_pct()

        # Trade statistics
        winning_trades = [t for t in self.closed_trades if t.realized_pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.realized_pnl < 0]

        win_rate = (
            len(winning_trades) / len(self.closed_trades) * 100
            if self.closed_trades else 0
        )

        avg_win = (
            sum(t.realized_pnl for t in winning_trades) / len(winning_trades)
            if winning_trades else 0
        )

        avg_loss = (
            sum(t.realized_pnl for t in losing_trades) / len(losing_trades)
            if losing_trades else 0
        )

        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'return_pct': return_pct,
            'open_positions': len(self.positions),
            'total_trades': len(self.closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_commission': self.total_commission_paid
        }

    def get_summary(self) -> Dict:
        """Get portfolio summary"""
        stats = self.get_statistics()

        return {
            'portfolio_value': stats['total_value'],
            'cash_balance': stats['cash'],
            'total_pnl': stats['total_pnl'],
            'return_pct': stats['return_pct'],
            'open_positions': stats['open_positions'],
            'total_trades': stats['total_trades'],
            'win_rate': stats['win_rate']
        }


if __name__ == "__main__":
    # Test PortfolioManager
    print("=" * 60)
    print("PORTFOLIO MANAGER TEST")
    print("=" * 60)

    portfolio = PortfolioManager(initial_capital=10000)

    # Open position
    print("\n[TEST] Opening AAPL position...")
    portfolio.open_position("AAPL", 10, 175.50, commission=1.76)
    print(f"[OK] Cash: ${portfolio.cash:.2f}")

    # Update price
    print("\n[TEST] Updating price to $180.00...")
    portfolio.update_position_prices({"AAPL": 180.00})
    pos = portfolio.get_position("AAPL")
    print(f"[OK] Unrealized P&L: ${pos.unrealized_pnl:.2f}")

    # Close position
    print("\n[TEST] Closing AAPL position...")
    trade = portfolio.close_position("AAPL", 10, 180.00, commission=1.80)
    print(f"[OK] Realized P&L: ${trade.realized_pnl:.2f}")

    # Statistics
    stats = portfolio.get_statistics()
    print(f"\n[STATS]")
    print(f"  Portfolio Value: ${stats['total_value']:.2f}")
    print(f"  Total P&L: ${stats['total_pnl']:.2f}")
    print(f"  Return: {stats['return_pct']:.2f}%")
    print(f"  Total Trades: {stats['total_trades']}")

    print("=" * 60)
