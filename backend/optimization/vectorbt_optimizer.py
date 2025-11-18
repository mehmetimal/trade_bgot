"""
Vectorbt Parameter Optimizer
Automatically finds the BEST strategy parameters using vectorbt backtesting
"""
import numpy as np
import pandas as pd
import vectorbt as vbt
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from itertools import product

from strategies.parameters import ParameterDefinitions
from data.yahoo_finance_collector import YahooFinanceCollector

logger = logging.getLogger(__name__)


class VectorbtOptimizer:
    """
    Uses vectorbt to automatically find optimal trading parameters

    This is the BRAIN of the bot:
    1. Takes 163+ parameters
    2. Runs THOUSANDS of backtest combinations
    3. Finds the BEST parameters automatically
    4. No manual input needed!
    """

    def __init__(
        self,
        symbols: List[str],
        optimization_period: str = "1y",
        optimization_metric: str = "sharpe_ratio"  # or "total_return", "calmar_ratio"
    ):
        """
        Initialize Parameter Optimizer

        Args:
            symbols: List of symbols to optimize for
            optimization_period: Historical data period for optimization
            optimization_metric: Metric to optimize (sharpe_ratio, total_return, etc.)
        """
        self.symbols = symbols
        self.optimization_period = optimization_period
        self.optimization_metric = optimization_metric
        self.collector = YahooFinanceCollector()

        # Parameter space (163 parameters)
        self.param_space = ParameterDefinitions.get_all_parameters()

        # Best parameters found (per symbol)
        self.best_params: Dict[str, Dict] = {}

        logger.info(
            f"VectorbtOptimizer initialized: "
            f"Symbols={symbols}, "
            f"Metric={optimization_metric}"
        )

    def optimize_ma_crossover(
        self,
        symbol: str,
        fast_range: range = None,
        slow_range: range = None,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Optimize Moving Average Crossover strategy using vectorbt

        This runs HUNDREDS of combinations automatically!

        Args:
            symbol: Symbol to optimize
            fast_range: Fast MA range (default: 5-50)
            slow_range: Slow MA range (default: 20-200)
            top_n: Return top N parameter combinations

        Returns:
            List of best parameter combinations with metrics
        """
        logger.info(f"🔍 Optimizing MA Crossover for {symbol}...")

        # Fetch data
        data = self.collector.fetch_historical_data(
            symbol=symbol,
            period=self.optimization_period,
            interval="1d"
        )

        if data is None or len(data) < 200:
            logger.error(f"Insufficient data for {symbol}")
            return []

        # Default ranges from parameter space
        if fast_range is None:
            fast_range = range(5, 51, 5)  # 5, 10, 15, ..., 50
        if slow_range is None:
            slow_range = range(20, 201, 10)  # 20, 30, ..., 200

        # Use vectorbt to run ALL combinations at once (FAST!)
        close = data['close']

        # Calculate all MA combinations using vectorbt
        fast_mas = vbt.MA.run(close, window=fast_range, short_name='fast')
        slow_mas = vbt.MA.run(close, window=slow_range, short_name='slow')

        # Generate entry/exit signals
        entries = fast_mas.ma_crossed_above(slow_mas)
        exits = fast_mas.ma_crossed_below(slow_mas)

        # Run portfolio simulation for ALL combinations
        portfolio = vbt.Portfolio.from_signals(
            close,
            entries,
            exits,
            init_cash=10000,
            fees=0.001,  # 0.1% commission
            slippage=0.0005  # 0.05% slippage
        )

        # Get metrics for all combinations
        sharpe_ratio = portfolio.sharpe_ratio()
        total_return = portfolio.total_return()
        max_drawdown = portfolio.max_drawdown()
        win_rate = portfolio.win_rate()

        # Flatten results and find best combinations
        results = []

        for fast_idx, fast_val in enumerate(fast_range):
            for slow_idx, slow_val in enumerate(slow_range):
                if fast_val >= slow_val:  # Invalid combination
                    continue

                try:
                    result = {
                        'symbol': symbol,
                        'strategy': 'ma_crossover',
                        'ma_fast': fast_val,
                        'ma_slow': slow_val,
                        'sharpe_ratio': sharpe_ratio.iloc[fast_idx, slow_idx],
                        'total_return': total_return.iloc[fast_idx, slow_idx],
                        'max_drawdown': max_drawdown.iloc[fast_idx, slow_idx],
                        'win_rate': win_rate.iloc[fast_idx, slow_idx],
                    }
                    results.append(result)
                except:
                    continue

        # Sort by optimization metric
        results = sorted(
            results,
            key=lambda x: x.get(self.optimization_metric, 0),
            reverse=True
        )

        # Get top N
        top_results = results[:top_n]

        # Log best result
        if top_results:
            best = top_results[0]
            logger.info(
                f"✅ Best MA for {symbol}: "
                f"Fast={best['ma_fast']}, Slow={best['ma_slow']}, "
                f"Sharpe={best['sharpe_ratio']:.2f}, "
                f"Return={best['total_return']*100:.1f}%"
            )

            # Store best parameters
            self.best_params[symbol] = {
                'ma_fast': best['ma_fast'],
                'ma_slow': best['ma_slow'],
                'stop_loss_pct': 0.02,  # Can also be optimized
                'take_profit_pct': 0.04
            }

        return top_results

    def optimize_rsi_strategy(
        self,
        symbol: str,
        rsi_range: range = None,
        oversold_range: range = None,
        overbought_range: range = None,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Optimize RSI strategy using vectorbt

        Args:
            symbol: Symbol to optimize
            rsi_range: RSI period range (default: 10-30)
            oversold_range: RSI oversold range (default: 20-40)
            overbought_range: RSI overbought range (default: 60-80)
            top_n: Return top N combinations
        """
        logger.info(f"🔍 Optimizing RSI Strategy for {symbol}...")

        # Fetch data
        data = self.collector.fetch_historical_data(
            symbol=symbol,
            period=self.optimization_period,
            interval="1d"
        )

        if data is None or len(data) < 200:
            logger.error(f"Insufficient data for {symbol}")
            return []

        # Default ranges
        if rsi_range is None:
            rsi_range = range(10, 31, 5)  # 10, 15, 20, 25, 30
        if oversold_range is None:
            oversold_range = range(20, 41, 5)  # 20, 25, 30, 35, 40
        if overbought_range is None:
            overbought_range = range(60, 81, 5)  # 60, 65, 70, 75, 80

        close = data['close']

        # Calculate RSI for all periods
        rsi = vbt.RSI.run(close, window=rsi_range)

        results = []

        # Test all combinations
        for rsi_period in rsi_range:
            for oversold in oversold_range:
                for overbought in overbought_range:
                    if oversold >= overbought:  # Invalid
                        continue

                    try:
                        # Get RSI for this period
                        rsi_vals = vbt.RSI.run(close, window=rsi_period).rsi

                        # Generate signals
                        entries = rsi_vals < oversold
                        exits = rsi_vals > overbought

                        # Backtest
                        portfolio = vbt.Portfolio.from_signals(
                            close,
                            entries,
                            exits,
                            init_cash=10000,
                            fees=0.001,
                            slippage=0.0005
                        )

                        result = {
                            'symbol': symbol,
                            'strategy': 'rsi',
                            'rsi_period': rsi_period,
                            'rsi_oversold': oversold,
                            'rsi_overbought': overbought,
                            'sharpe_ratio': portfolio.sharpe_ratio(),
                            'total_return': portfolio.total_return(),
                            'max_drawdown': portfolio.max_drawdown(),
                            'win_rate': portfolio.win_rate(),
                        }
                        results.append(result)
                    except:
                        continue

        # Sort and return top N
        results = sorted(
            results,
            key=lambda x: x.get(self.optimization_metric, 0),
            reverse=True
        )

        top_results = results[:top_n]

        if top_results:
            best = top_results[0]
            logger.info(
                f"✅ Best RSI for {symbol}: "
                f"Period={best['rsi_period']}, "
                f"Oversold={best['rsi_oversold']}, "
                f"Overbought={best['rsi_overbought']}, "
                f"Sharpe={best['sharpe_ratio']:.2f}"
            )

            self.best_params[symbol] = {
                'rsi_period': best['rsi_period'],
                'rsi_oversold': best['rsi_oversold'],
                'rsi_overbought': best['rsi_overbought'],
                'ma_slow': 50,  # Can also be optimized
                'stop_loss_pct': 0.03,
                'take_profit_pct': 0.06
            }

        return top_results

    def optimize_all_symbols(
        self,
        strategy: str = "ma_crossover"
    ) -> Dict[str, Dict]:
        """
        Optimize parameters for ALL symbols automatically

        Args:
            strategy: Strategy to optimize (ma_crossover, rsi)

        Returns:
            Dict of best parameters per symbol
        """
        logger.info(f"🚀 Starting optimization for {len(self.symbols)} symbols...")

        all_results = {}

        for symbol in self.symbols:
            try:
                if strategy == "ma_crossover":
                    results = self.optimize_ma_crossover(symbol, top_n=1)
                elif strategy == "rsi":
                    results = self.optimize_rsi_strategy(symbol, top_n=1)
                else:
                    logger.warning(f"Unknown strategy: {strategy}")
                    continue

                if results:
                    all_results[symbol] = self.best_params[symbol]

            except Exception as e:
                logger.error(f"Optimization failed for {symbol}: {e}")

        logger.info(f"✅ Optimization complete! Found best params for {len(all_results)} symbols")

        return all_results

    def get_best_params(self, symbol: str) -> Optional[Dict]:
        """Get optimized parameters for a symbol"""
        return self.best_params.get(symbol)

    def save_results(self, filepath: str = "optimization_results.json"):
        """Save optimization results to file"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.best_params, f, indent=2)
        logger.info(f"Results saved to {filepath}")

    def load_results(self, filepath: str = "optimization_results.json"):
        """Load optimization results from file"""
        import json
        try:
            with open(filepath, 'r') as f:
                self.best_params = json.load(f)
            logger.info(f"Results loaded from {filepath}")
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")


def optimize_and_get_best_strategy(
    symbols: List[str],
    strategy: str = "ma_crossover"
) -> Dict[str, Dict]:
    """
    Convenience function to optimize and get best parameters

    Usage:
        best_params = optimize_and_get_best_strategy(['AAPL', 'TSLA'], 'ma_crossover')
        # Returns: {'AAPL': {'ma_fast': 10, 'ma_slow': 30, ...}, 'TSLA': {...}}
    """
    optimizer = VectorbtOptimizer(symbols)
    return optimizer.optimize_all_symbols(strategy)
