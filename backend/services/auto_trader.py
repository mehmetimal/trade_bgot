"""
Auto Trading Service - Automatically trades based on strategy signals
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from data.yahoo_finance_collector import YahooFinanceCollector
from strategies.simple_ma_strategy import SimpleMAStrategy, RSIMAStrategy
from paper_trading.engine import PaperTradingEngine

logger = logging.getLogger(__name__)


class AutoTrader:
    """Automatic trading service that executes trades based on strategy signals"""

    def __init__(
        self,
        engine: PaperTradingEngine,
        strategy_name: str = "simple_ma",
        symbols: list = None,
        check_interval: int = 60,  # seconds
    ):
        self.engine = engine
        self.strategy_name = strategy_name
        self.symbols = symbols or ["AAPL", "TSLA", "GOOGL"]
        self.check_interval = check_interval
        self.collector = YahooFinanceCollector()
        self.running = False
        self.task: Optional[asyncio.Task] = None

        # Initialize strategy
        self.strategy = self._create_strategy(strategy_name)
        logger.info(f"AutoTrader initialized with strategy: {strategy_name}")
        logger.info(f"Watching symbols: {self.symbols}")

    def _create_strategy(self, name: str):
        """Create strategy instance"""
        if name == "simple_ma":
            return SimpleMAStrategy({
                'ma_fast': 10,
                'ma_slow': 30,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04
            })
        elif name == "rsi_ma":
            return RSIMAStrategy({
                'ma_slow': 50,
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'stop_loss_pct': 0.03,
                'take_profit_pct': 0.06
            })
        else:
            raise ValueError(f"Unknown strategy: {name}")

    async def start(self):
        """Start the auto-trading loop"""
        if self.running:
            logger.warning("AutoTrader already running")
            return

        self.running = True
        logger.info("🤖 AutoTrader started")
        self.task = asyncio.create_task(self._trading_loop())

    async def stop(self):
        """Stop the auto-trading loop"""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 AutoTrader stopped")

    async def _trading_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                await self._check_and_trade()
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def _check_and_trade(self):
        """Check signals and execute trades"""
        logger.info("🔍 Checking signals...")

        for symbol in self.symbols:
            try:
                # Fetch recent data
                data = self.collector.fetch_historical_data(
                    symbol,
                    period="1mo",
                    interval="1h"  # Hourly data for faster signals
                )

                if data is None or len(data) < 50:
                    logger.warning(f"Insufficient data for {symbol}")
                    continue

                # Update current price in engine
                current_price = float(data.iloc[-1]['close'])
                self.engine.update_market_data(symbol, current_price)

                # Generate signals
                signals = self.strategy.generate_signals(data)

                # Get current position
                position = self.engine.get_position(symbol)

                # Check entry signal
                if signals.entries.iloc[-1] and not position:
                    await self._execute_entry(symbol, current_price)

                # Check exit signal
                elif signals.exits.iloc[-1] and position:
                    await self._execute_exit(symbol, position)

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

    async def _execute_entry(self, symbol: str, price: float):
        """Execute entry order"""
        try:
            # Calculate position size (simple: use 10% of portfolio)
            portfolio_value = self.engine.get_portfolio_summary()['portfolio_value']
            cash = self.engine.get_portfolio_summary()['cash_balance']

            if cash < portfolio_value * 0.1:
                logger.warning(f"Insufficient cash for {symbol} entry")
                return

            # Calculate quantity
            position_value = portfolio_value * 0.1
            quantity = int(position_value / price)

            if quantity < 1:
                logger.warning(f"Position too small for {symbol}")
                return

            # Place market buy order
            order = self.engine.place_order(
                symbol=symbol,
                side="buy",
                quantity=quantity,
                order_type="market"
            )

            logger.info(
                f"✅ BUY SIGNAL EXECUTED: {symbol} "
                f"qty={quantity} @ ${price:.2f} "
                f"(order_id: {order.order_id})"
            )

        except Exception as e:
            logger.error(f"Failed to execute entry for {symbol}: {e}")

    async def _execute_exit(self, symbol: str, position):
        """Execute exit order"""
        try:
            # Place market sell order for entire position
            order = self.engine.place_order(
                symbol=symbol,
                side="sell",
                quantity=position.quantity,
                order_type="market"
            )

            logger.info(
                f"✅ SELL SIGNAL EXECUTED: {symbol} "
                f"qty={position.quantity} @ ${position.current_price:.2f} "
                f"(order_id: {order.order_id})"
            )

        except Exception as e:
            logger.error(f"Failed to execute exit for {symbol}: {e}")

    def get_status(self) -> dict:
        """Get auto-trader status"""
        return {
            "running": self.running,
            "strategy": self.strategy_name,
            "symbols": self.symbols,
            "check_interval": self.check_interval,
            "portfolio": self.engine.get_portfolio_summary()
        }
