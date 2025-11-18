"""
Strategy Runner - Continuously executes trading strategies
This is the CORE of the automated trading system
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd

from paper_trading.engine import PaperTradingEngine
from strategies.base_strategy import BaseStrategy
from strategies.simple_ma_strategy import SimpleMAStrategy, RSIMAStrategy
from strategies.combined_strategy import CombinedStrategy
from data.turkish_symbols import get_turkish_symbols
from data.yahoo_finance_collector import YahooFinanceCollector

logger = logging.getLogger(__name__)


class StrategyRunner:
    """
    Runs trading strategies continuously on live market data
    and automatically executes trades based on signals.

    This is the CORE automated trading component.
    """

    def __init__(
        self,
        engine: PaperTradingEngine,
        strategy: BaseStrategy,
        symbols: List[str],
        update_interval: int = 60,  # seconds
        data_period: str = "1mo",
        data_interval: str = "1h",
        use_optimized_params: bool = True  # NEW: Use auto-optimized parameters
    ):
        """
        Initialize Strategy Runner

        Args:
            engine: Paper trading engine for order execution
            strategy: Trading strategy instance
            symbols: List of symbols to trade
            update_interval: How often to check for signals (seconds)
            data_period: Historical data period for strategy
            data_interval: Data interval (1m, 5m, 1h, 1d)
        """
        self.engine = engine
        self.strategy = strategy
        self.symbols = symbols
        self.update_interval = update_interval
        self.data_period = data_period
        self.data_interval = data_interval

        self.collector = YahooFinanceCollector()
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.use_optimized_params = use_optimized_params

        # Track last signal to avoid duplicate orders
        self.last_signals: Dict[str, Dict] = {}

        # Optimized parameters per symbol (auto-loaded)
        self.optimized_params: Dict[str, Dict] = {}
        if use_optimized_params:
            self._load_optimized_params()

        logger.info(
            f"StrategyRunner initialized: "
            f"Strategy={strategy.__class__.__name__}, "
            f"Symbols={symbols}, "
            f"Interval={update_interval}s, "
            f"Optimized={use_optimized_params}"
        )

    def _load_optimized_params(self):
        """Load auto-optimized parameters from file"""
        try:
            import json
            import os
            filepath = "optimization_results.json"
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.optimized_params = json.load(f)
                logger.info(f"✅ Loaded optimized params for {len(self.optimized_params)} symbols")
            else:
                logger.warning(f"No optimization file found. Run optimization first!")
        except Exception as e:
            logger.error(f"Failed to load optimized params: {e}")

    async def start(self):
        """Start the strategy runner loop"""
        if self.running:
            logger.warning("StrategyRunner already running")
            return

        self.running = True
        logger.info("🚀 StrategyRunner STARTED - Auto-trading activated")
        self.task = asyncio.create_task(self._run_loop())

    async def stop(self):
        """Stop the strategy runner loop"""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 StrategyRunner STOPPED - Auto-trading deactivated")

    async def _run_loop(self):
        """Main strategy execution loop"""
        while self.running:
            try:
                await self._execute_strategies()
            except Exception as e:
                logger.error(f"Error in strategy loop: {e}", exc_info=True)

            # Wait for next update
            await asyncio.sleep(self.update_interval)

    async def _execute_strategies(self):
        """Execute strategies for all symbols"""
        logger.info(f"🔍 Checking signals at {datetime.now().strftime('%H:%M:%S')}")

        for symbol in self.symbols:
            try:
                await self._process_symbol(symbol)
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

        try:
            await self._check_arbitrage_opportunities()
        except Exception as e:
            logger.error(f"Arbitrage check error: {e}")

    async def _process_symbol(self, symbol: str):
        """Process a single symbol using OPTIMIZED parameters"""
        # 1. Fetch market data
        data = self._fetch_data(symbol)
        if data is None or len(data) < 50:
            logger.warning(f"{symbol}: Insufficient data")
            return

        # 2. Update current price in engine
        current_price = float(data.iloc[-1]['close'])
        self.engine.update_market_data(symbol, current_price)

        # 3. Get symbol-specific optimized parameters
        if self.use_optimized_params and symbol in self.optimized_params:
            # Use OPTIMIZED parameters for this symbol!
            strategy_params = self.optimized_params[symbol]
            # Create temporary strategy with optimized params
            strategy = self._create_strategy_with_params(strategy_params)
            logger.debug(f"{symbol}: Using optimized params: {strategy_params}")
        else:
            # Fall back to default strategy
            strategy = self.strategy

        # 4. Generate signals using (optimized) strategy
        signals = strategy.generate_signals(data)
        entry_signal = signals.entries.iloc[-1]
        exit_signal = signals.exits.iloc[-1]

        # 5. Get current position
        position = self.engine.get_position(symbol)

        # 6. Execute based on signals
        if entry_signal and not position:
            await self._execute_entry(symbol, current_price, data, strategy_params if self.use_optimized_params and symbol in self.optimized_params else self.strategy.parameters)
        elif exit_signal and position:
            await self._execute_exit(symbol, position)

        # 7. Check stop loss / take profit
        if position:
            self._check_exit_conditions(symbol, position, current_price)

    def _create_strategy_with_params(self, params: Dict):
        """Create strategy instance with specific parameters"""
        strategy_class = self.strategy.__class__
        return strategy_class(params)

    def _fetch_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch market data for symbol"""
        try:
            data = self.collector.fetch_historical_data(
                symbol=symbol,
                period=self.data_period,
                interval=self.data_interval
            )
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None

    async def _execute_entry(self, symbol: str, price: float, data: pd.DataFrame, params: Dict = None):
        """Execute entry order based on strategy signal with OPTIMIZED parameters"""
        try:
            # Calculate position size
            position_size = self._calculate_position_size(symbol, price)

            if position_size < 1:
                logger.info(f"{symbol}: Position size too small, skipping")
                return

            # Get strategy parameters (optimized or default)
            if params is None:
                params = self.strategy.parameters
            stop_loss_pct = params.get('stop_loss_pct', 0.02)
            take_profit_pct = params.get('take_profit_pct', 0.04)

            # Place buy order
            order = self.engine.place_order(
                symbol=symbol,
                side="buy",
                quantity=position_size,
                order_type="market",
                auto_stop_loss=True,
                stop_loss_pct=stop_loss_pct,
                auto_take_profit=True,
                take_profit_pct=take_profit_pct
            )

            # Log entry
            logger.info(
                f"✅ ENTRY SIGNAL: {symbol} "
                f"qty={position_size} @ ${price:.2f} "
                f"SL={stop_loss_pct*100:.1f}% TP={take_profit_pct*100:.1f}% "
                f"(order: {order.order_id[:8]})"
            )

            # Track signal
            self.last_signals[symbol] = {
                'type': 'entry',
                'time': datetime.now(),
                'price': price
            }

        except Exception as e:
            logger.error(f"Failed to execute entry for {symbol}: {e}")

    async def _execute_exit(self, symbol: str, position):
        """Execute exit order based on strategy signal"""
        try:
            # Place sell order
            order = self.engine.place_order(
                symbol=symbol,
                side="sell",
                quantity=position.quantity,
                order_type="market"
            )

            # Calculate P&L
            entry_price = position.avg_entry_price
            exit_price = position.current_price
            pnl = (exit_price - entry_price) * position.quantity
            pnl_pct = ((exit_price / entry_price) - 1) * 100

            # Log exit
            logger.info(
                f"✅ EXIT SIGNAL: {symbol} "
                f"qty={position.quantity} @ ${exit_price:.2f} "
                f"P&L=${pnl:.2f} ({pnl_pct:+.2f}%) "
                f"(order: {order.order_id[:8]})"
            )

            # Track signal
            self.last_signals[symbol] = {
                'type': 'exit',
                'time': datetime.now(),
                'price': exit_price,
                'pnl': pnl
            }

        except Exception as e:
            logger.error(f"Failed to execute exit for {symbol}: {e}")

    async def _check_arbitrage_opportunities(self):
        pairs = []
        if "TUR" in self.symbols:
            for s in self.symbols:
                if s.endswith('.IS'):
                    pairs.append((s, "TUR"))

        lookback = 50
        threshold = 2.0
        for a, b in pairs:
            da = self._fetch_data(a)
            db = self._fetch_data(b)
            if da is None or db is None:
                continue
            sa = da['close'].tail(lookback).reset_index(drop=True)
            sb = db['close'].tail(lookback).reset_index(drop=True)
            if len(sa) < lookback or len(sb) < lookback:
                continue
            ratio = sa / sb.reindex_like(sa)
            z = (ratio - ratio.mean()) / (ratio.std() if ratio.std() != 0 else 1)
            z_last = float(z.iloc[-1])
            pa = float(sa.iloc[-1])
            pb = float(sb.iloc[-1])
            if z_last > threshold:
                qa = self._calculate_position_size(a, pa)
                qb = self._calculate_position_size(b, pb)
                if qa > 0 and qb > 0:
                    self.engine.place_order(symbol=a, side="sell", quantity=qa, order_type="market")
                    self.engine.place_order(symbol=b, side="buy", quantity=qb, order_type="market")
                    self.last_signals[f"arb_{a}_{b}"] = {'type':'arbitrage','time':datetime.now(),'z':z_last}
            elif z_last < -threshold:
                qa = self._calculate_position_size(a, pa)
                qb = self._calculate_position_size(b, pb)
                if qa > 0 and qb > 0:
                    self.engine.place_order(symbol=a, side="buy", quantity=qa, order_type="market")
                    self.engine.place_order(symbol=b, side="sell", quantity=qb, order_type="market")
                    self.last_signals[f"arb_{a}_{b}"] = {'type':'arbitrage','time':datetime.now(),'z':z_last}

    def _check_exit_conditions(self, symbol: str, position, current_price: float):
        """Check if stop loss or take profit should be triggered"""
        entry_price = position.avg_entry_price

        # Calculate current P&L %
        pnl_pct = ((current_price / entry_price) - 1) * 100

        # Get strategy parameters
        params = self.strategy.parameters
        stop_loss_pct = params.get('stop_loss_pct', 0.02) * 100
        take_profit_pct = params.get('take_profit_pct', 0.04) * 100

        # Check stop loss
        if pnl_pct <= -stop_loss_pct:
            logger.warning(
                f"🛑 STOP LOSS triggered: {symbol} "
                f"P&L={pnl_pct:.2f}% (limit: -{stop_loss_pct:.2f}%)"
            )
            # Note: Order manager should handle this automatically
            # This is just logging

        # Check take profit
        elif pnl_pct >= take_profit_pct:
            logger.info(
                f"🎯 TAKE PROFIT triggered: {symbol} "
                f"P&L={pnl_pct:.2f}% (target: +{take_profit_pct:.2f}%)"
            )
            # Note: Order manager should handle this automatically

    def _calculate_position_size(self, symbol: str, price: float) -> int:
        """Calculate position size based on available capital and risk"""
        # Get portfolio info
        portfolio = self.engine.get_portfolio_summary()
        available_cash = portfolio['cash_balance']
        portfolio_value = portfolio['portfolio_value']

        # Use max 20% of portfolio per position
        max_position_value = portfolio_value * 0.20

        # Or max 95% of available cash
        max_cash_to_use = available_cash * 0.95

        # Take minimum
        position_value = min(max_position_value, max_cash_to_use)

        # Calculate quantity
        quantity = int(position_value / price)

        return quantity

    def get_status(self) -> dict:
        """Get strategy runner status"""
        return {
            'running': self.running,
            'strategy': self.strategy.__class__.__name__,
            'symbols': self.symbols,
            'update_interval': self.update_interval,
            'last_signals': self.last_signals,
            'portfolio': self.engine.get_portfolio_summary()
        }


def create_strategy_runner(
    engine: PaperTradingEngine,
    strategy_name: str = "simple_ma",
    symbols: List[str] = None,
    update_interval: int = 10,
    market: str = "turkish"
) -> StrategyRunner:
    """
    Factory function to create a StrategyRunner

    Args:
        engine: Paper trading engine
        strategy_name: Name of strategy to use
        symbols: List of symbols to trade
        update_interval: Update interval in seconds

    Returns:
        Configured StrategyRunner instance
    """
    if symbols is None:
        if market == "turkish":
            symbols = get_turkish_symbols()
        else:
            symbols = ["AAPL", "TSLA", "GOOGL"]

    # Create strategy
    if strategy_name == "simple_ma":
        strategy = SimpleMAStrategy({
            'ma_fast': 10,
            'ma_slow': 30,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })
    elif strategy_name == "rsi_ma":
        strategy = RSIMAStrategy({
            'ma_slow': 50,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.06
        })
    elif strategy_name == "combined":
        strategy = CombinedStrategy({
            'ma_fast': 10,
            'ma_slow': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bollinger_period': 20,
            'bollinger_std': 2.0,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    return StrategyRunner(
        engine=engine,
        strategy=strategy,
        symbols=symbols,
        update_interval=update_interval
    )
