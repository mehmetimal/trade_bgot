"""
Risk Management System for Paper Trading
Controls position sizes, exposure, and risk limits
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskViolation(Exception):
    """Exception raised when risk limit is violated"""
    pass


class RiskManager:
    """
    Risk Management System
    - Position sizing
    - Exposure limits
    - Drawdown monitoring
    - Daily loss limits
    - Stop loss automation
    """

    def __init__(
        self,
        max_position_size_pct: float = 0.2,      # Max 20% per position
        max_total_exposure_pct: float = 0.95,    # Max 95% total exposure
        max_drawdown_pct: float = 0.15,          # Max 15% drawdown
        max_daily_loss_pct: float = 0.05,        # Max 5% daily loss
        max_loss_per_trade_pct: float = 0.02,    # Max 2% loss per trade
        enable_stop_loss: bool = True,
        enable_daily_limit: bool = True
    ):
        self.max_position_size_pct = max_position_size_pct
        self.max_total_exposure_pct = max_total_exposure_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_loss_per_trade_pct = max_loss_per_trade_pct
        self.enable_stop_loss = enable_stop_loss
        self.enable_daily_limit = enable_daily_limit

        # Tracking
        self.daily_pnl: Dict[str, float] = {}  # {date: pnl}
        self.peak_portfolio_value: float = 0.0
        self.current_drawdown_pct: float = 0.0

    def check_order_risk(
        self,
        symbol: str,
        quantity: float,
        price: float,
        portfolio_value: float,
        current_positions: Dict,
        side: str = "buy"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if order violates risk limits

        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            side: "buy" or "sell"

        Returns:
            (allowed: bool, reason: str)
        """
        # Calculate order value
        order_value = quantity * price

        # Check 1: Position size limit
        position_size_pct = (order_value / portfolio_value) * 100
        if position_size_pct > self.max_position_size_pct * 100:
            reason = (
                f"Position size {position_size_pct:.1f}% exceeds "
                f"limit {self.max_position_size_pct * 100:.1f}%"
            )
            logger.warning(f"Risk violation: {reason}")
            return False, reason

        # Check 2: Total exposure limit
        if side == "buy":
            current_exposure = sum(
                pos.market_value for pos in current_positions.values()
            )
            new_exposure_pct = ((current_exposure + order_value) / portfolio_value) * 100

            if new_exposure_pct > self.max_total_exposure_pct * 100:
                reason = (
                    f"Total exposure {new_exposure_pct:.1f}% exceeds "
                    f"limit {self.max_total_exposure_pct * 100:.1f}%"
                )
                logger.warning(f"Risk violation: {reason}")
                return False, reason

        # Check 3: Daily loss limit
        if self.enable_daily_limit:
            today = datetime.now().date().isoformat()
            daily_loss = self.daily_pnl.get(today, 0.0)

            if daily_loss < 0:
                daily_loss_pct = abs(daily_loss / portfolio_value) * 100
                if daily_loss_pct > self.max_daily_loss_pct * 100:
                    reason = (
                        f"Daily loss {daily_loss_pct:.1f}% exceeds "
                        f"limit {self.max_daily_loss_pct * 100:.1f}%"
                    )
                    logger.warning(f"Risk violation: {reason}")
                    return False, reason

        # All checks passed
        return True, None

    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade_pct: Optional[float] = None
    ) -> float:
        """
        Calculate optimal position size based on risk parameters

        Args:
            portfolio_value: Current portfolio value
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_per_trade_pct: Risk percentage (uses default if None)

        Returns:
            Position size (quantity)
        """
        if risk_per_trade_pct is None:
            risk_per_trade_pct = self.max_loss_per_trade_pct

        # Risk amount in dollars
        risk_amount = portfolio_value * risk_per_trade_pct

        # Risk per share
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            # No stop loss defined, use max position size limit
            max_position_value = portfolio_value * self.max_position_size_pct
            return max_position_value / entry_price

        # Position size
        position_size = risk_amount / risk_per_share

        # Apply maximum position size limit
        max_position_value = portfolio_value * self.max_position_size_pct
        max_quantity = max_position_value / entry_price

        return min(position_size, max_quantity)

    def update_drawdown(self, current_portfolio_value: float):
        """
        Update drawdown tracking

        Args:
            current_portfolio_value: Current portfolio value
        """
        # Update peak
        if current_portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_portfolio_value

        # Calculate drawdown
        if self.peak_portfolio_value > 0:
            drawdown = self.peak_portfolio_value - current_portfolio_value
            self.current_drawdown_pct = (drawdown / self.peak_portfolio_value) * 100
        else:
            self.current_drawdown_pct = 0.0

    def check_drawdown_limit(self) -> Tuple[bool, Optional[str]]:
        """
        Check if current drawdown exceeds limit

        Returns:
            (within_limit: bool, reason: str)
        """
        if self.current_drawdown_pct > self.max_drawdown_pct * 100:
            reason = (
                f"Drawdown {self.current_drawdown_pct:.1f}% exceeds "
                f"limit {self.max_drawdown_pct * 100:.1f}%"
            )
            logger.warning(f"Risk violation: {reason}")
            return False, reason

        return True, None

    def update_daily_pnl(self, pnl: float, date: Optional[str] = None):
        """
        Update daily P&L tracking

        Args:
            pnl: P&L for the trade
            date: Date string (YYYY-MM-DD), uses today if None
        """
        if date is None:
            date = datetime.now().date().isoformat()

        if date not in self.daily_pnl:
            self.daily_pnl[date] = 0.0

        self.daily_pnl[date] += pnl

    def get_daily_pnl(self, date: Optional[str] = None) -> float:
        """Get P&L for a specific date"""
        if date is None:
            date = datetime.now().date().isoformat()

        return self.daily_pnl.get(date, 0.0)

    def calculate_stop_loss_price(
        self,
        entry_price: float,
        side: str = "buy",
        stop_loss_pct: float = 0.02
    ) -> float:
        """
        Calculate stop loss price

        Args:
            entry_price: Entry price
            side: "buy" or "sell"
            stop_loss_pct: Stop loss percentage (e.g., 0.02 for 2%)

        Returns:
            Stop loss price
        """
        if side == "buy":
            # For long positions, stop loss is below entry
            return entry_price * (1 - stop_loss_pct)
        else:
            # For short positions, stop loss is above entry
            return entry_price * (1 + stop_loss_pct)

    def calculate_take_profit_price(
        self,
        entry_price: float,
        side: str = "buy",
        take_profit_pct: float = 0.04
    ) -> float:
        """
        Calculate take profit price

        Args:
            entry_price: Entry price
            side: "buy" or "sell"
            take_profit_pct: Take profit percentage (e.g., 0.04 for 4%)

        Returns:
            Take profit price
        """
        if side == "buy":
            # For long positions, take profit is above entry
            return entry_price * (1 + take_profit_pct)
        else:
            # For short positions, take profit is below entry
            return entry_price * (1 - take_profit_pct)

    def should_close_position(
        self,
        current_price: float,
        entry_price: float,
        stop_loss_price: Optional[float],
        take_profit_price: Optional[float],
        side: str = "buy"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if position should be closed based on risk rules

        Args:
            current_price: Current market price
            entry_price: Entry price
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
            side: "buy" or "sell"

        Returns:
            (should_close: bool, reason: str)
        """
        if side == "buy":
            # Long position
            if stop_loss_price and current_price <= stop_loss_price:
                return True, "stop_loss"

            if take_profit_price and current_price >= take_profit_price:
                return True, "take_profit"

        else:
            # Short position
            if stop_loss_price and current_price >= stop_loss_price:
                return True, "stop_loss"

            if take_profit_price and current_price <= take_profit_price:
                return True, "take_profit"

        return False, None

    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        today = datetime.now().date().isoformat()
        daily_pnl = self.get_daily_pnl(today)

        return {
            'current_drawdown_pct': self.current_drawdown_pct,
            'max_drawdown_pct': self.max_drawdown_pct * 100,
            'peak_portfolio_value': self.peak_portfolio_value,
            'daily_pnl': daily_pnl,
            'max_daily_loss_pct': self.max_daily_loss_pct * 100,
            'max_position_size_pct': self.max_position_size_pct * 100,
            'max_total_exposure_pct': self.max_total_exposure_pct * 100
        }

    def reset_daily_limits(self):
        """Reset daily limits (call at start of new trading day)"""
        # Clean up old daily P&L records (keep last 30 days)
        cutoff_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        self.daily_pnl = {
            date: pnl for date, pnl in self.daily_pnl.items()
            if date >= cutoff_date
        }

        logger.info("Daily limits reset")


if __name__ == "__main__":
    # Test RiskManager
    print("=" * 60)
    print("RISK MANAGER TEST")
    print("=" * 60)

    risk_mgr = RiskManager()

    # Test 1: Position size calculation
    print("\n[TEST 1] Calculate position size...")
    portfolio_value = 10000
    entry_price = 100
    stop_loss_price = 98  # 2% stop loss

    quantity = risk_mgr.calculate_position_size(
        portfolio_value, entry_price, stop_loss_price
    )
    print(f"[OK] Position size: {quantity:.2f} shares")
    print(f"[OK] Position value: ${quantity * entry_price:.2f}")

    # Test 2: Check order risk
    print("\n[TEST 2] Check order risk...")
    allowed, reason = risk_mgr.check_order_risk(
        symbol="AAPL",
        quantity=quantity,
        price=entry_price,
        portfolio_value=portfolio_value,
        current_positions={},
        side="buy"
    )
    print(f"[OK] Order allowed: {allowed}")

    # Test 3: Stop loss calculation
    print("\n[TEST 3] Calculate stop loss and take profit...")
    stop_loss = risk_mgr.calculate_stop_loss_price(entry_price, side="buy", stop_loss_pct=0.02)
    take_profit = risk_mgr.calculate_take_profit_price(entry_price, side="buy", take_profit_pct=0.04)
    print(f"[OK] Entry: ${entry_price:.2f}")
    print(f"[OK] Stop Loss: ${stop_loss:.2f}")
    print(f"[OK] Take Profit: ${take_profit:.2f}")

    # Test 4: Drawdown tracking
    print("\n[TEST 4] Drawdown tracking...")
    risk_mgr.update_drawdown(10000)  # Initial
    risk_mgr.update_drawdown(9500)   # -5% drawdown
    print(f"[OK] Current drawdown: {risk_mgr.current_drawdown_pct:.2f}%")

    within_limit, reason = risk_mgr.check_drawdown_limit()
    print(f"[OK] Within limit: {within_limit}")

    # Test 5: Daily P&L tracking
    print("\n[TEST 5] Daily P&L tracking...")
    risk_mgr.update_daily_pnl(100)   # +$100
    risk_mgr.update_daily_pnl(-50)   # -$50
    daily_pnl = risk_mgr.get_daily_pnl()
    print(f"[OK] Today's P&L: ${daily_pnl:.2f}")

    # Test 6: Risk metrics
    print("\n[TEST 6] Risk metrics...")
    metrics = risk_mgr.get_risk_metrics()
    print(f"[METRICS]")
    print(f"  Drawdown: {metrics['current_drawdown_pct']:.2f}%")
    print(f"  Daily P&L: ${metrics['daily_pnl']:.2f}")
    print(f"  Max Position Size: {metrics['max_position_size_pct']:.1f}%")

    print("=" * 60)
