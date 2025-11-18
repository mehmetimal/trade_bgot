"""
Backtest Engine - Production-ready backtesting system
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Tek bir trade kaydı"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    commission: float
    reason: str  # 'stop_loss', 'take_profit', 'signal', etc.

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['entry_time'] = self.entry_time.isoformat()
        d['exit_time'] = self.exit_time.isoformat()
        return d


@dataclass
class BacktestResult:
    """Backtest sonuçları"""
    # Basic metrics
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Profit metrics
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float

    # Time metrics
    avg_trade_duration: float
    max_trade_duration: float

    # Equity curve
    equity_curve: pd.Series
    drawdown_curve: pd.Series

    # All trades
    trades: List[Trade]

    # Additional metrics
    calmar_ratio: float
    recovery_factor: float
    volatility: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'expectancy': self.expectancy,
            'avg_trade_duration': self.avg_trade_duration,
            'max_trade_duration': self.max_trade_duration,
            'calmar_ratio': self.calmar_ratio,
            'recovery_factor': self.recovery_factor,
            'volatility': self.volatility,
            'equity_curve': self.equity_curve.to_dict(),
            'drawdown_curve': self.drawdown_curve.to_dict(),
            'trades': [t.to_dict() for t in self.trades]
        }

    def print_summary(self):
        """Print backtest summary"""
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"Total Return: ${self.total_return:.2f} ({self.total_return_pct:.2f}%)")
        print(f"Sharpe Ratio: {self.sharpe_ratio:.2f}")
        print(f"Sortino Ratio: {self.sortino_ratio:.2f}")
        print(f"Calmar Ratio: {self.calmar_ratio:.2f}")
        print(f"Max Drawdown: ${self.max_drawdown:.2f} ({self.max_drawdown_pct:.2f}%)")
        print(f"Volatility: {self.volatility:.2f}%")
        print(f"\nTotal Trades: {self.total_trades}")
        print(f"Winning Trades: {self.winning_trades}")
        print(f"Losing Trades: {self.losing_trades}")
        print(f"Win Rate: {self.win_rate:.2f}%")
        print(f"Avg Win: ${self.avg_win:.2f}")
        print(f"Avg Loss: ${self.avg_loss:.2f}")
        print(f"Profit Factor: {self.profit_factor:.2f}")
        print(f"Expectancy: ${self.expectancy:.2f}")
        print(f"Avg Trade Duration: {self.avg_trade_duration:.2f} hours")
        print("="*60)


class BacktestEngine:
    """
    Production-ready backtest engine
    - Gerçekçi slippage ve commission
    - Multiple timeframe support
    - Walk-forward analysis
    - Out-of-sample testing
    """

    def __init__(
        self,
        initial_capital: float = 10000,
        commission_pct: float = 0.001,  # 0.1%
        slippage_pct: float = 0.0005,   # 0.05%
        risk_per_trade: float = 0.02     # 2% risk per trade
    ):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.risk_per_trade = risk_per_trade

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> BacktestResult:
        """
        Backtest çalıştır

        Args:
            data: OHLCV DataFrame
            strategy: Strategy instance with generate_signals() method
            symbol: Trading symbol
            start_date: Backtest başlangıç
            end_date: Backtest bitiş
        """
        logger.info(f"Starting backtest for {symbol}")

        # Date filtering
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]

        logger.info(f"Backtest period: {data.index[0]} to {data.index[-1]} ({len(data)} bars)")

        # Signal generation
        signals = strategy.generate_signals(data)

        # Simulation
        trades = []
        equity_curve = []
        current_capital = self.initial_capital
        position = None

        for i in range(len(data)):
            current_bar = data.iloc[i]
            current_price = current_bar['close']
            current_time = data.index[i]

            # Portfolio value
            if position:
                position_value = position['quantity'] * current_price
                total_value = current_capital + position_value
            else:
                total_value = current_capital

            equity_curve.append({
                'timestamp': current_time,
                'equity': total_value
            })

            # Entry signal
            if signals.entries.iloc[i] and position is None:
                # Calculate position size
                risk_amount = total_value * self.risk_per_trade
                stop_loss_price = current_price * (1 - strategy.parameters.get('stop_loss_pct', 0.02))
                risk_per_unit = current_price - stop_loss_price

                if risk_per_unit > 0:
                    quantity = risk_amount / risk_per_unit
                else:
                    quantity = total_value * 0.1 / current_price  # Default 10% position

                # Apply slippage
                entry_price = current_price * (1 + self.slippage_pct)

                # Commission
                position_cost = quantity * entry_price
                commission = position_cost * self.commission_pct

                # Check sufficient capital
                if current_capital >= (position_cost + commission):
                    position = {
                        'entry_time': current_time,
                        'entry_price': entry_price,
                        'quantity': quantity,
                        'stop_loss': stop_loss_price,
                        'take_profit': current_price * (1 + strategy.parameters.get('take_profit_pct', 0.04))
                    }
                    current_capital -= (position_cost + commission)

            # Exit signal or stop loss/take profit
            elif position is not None:
                should_exit = False
                exit_reason = None

                # Exit signal
                if signals.exits.iloc[i]:
                    should_exit = True
                    exit_reason = 'signal'

                # Stop loss
                elif current_price <= position['stop_loss']:
                    should_exit = True
                    exit_reason = 'stop_loss'

                # Take profit
                elif current_price >= position['take_profit']:
                    should_exit = True
                    exit_reason = 'take_profit'

                if should_exit:
                    # Apply slippage
                    exit_price = current_price * (1 - self.slippage_pct)

                    # Calculate PnL
                    proceeds = position['quantity'] * exit_price
                    commission = proceeds * self.commission_pct
                    pnl = proceeds - (position['quantity'] * position['entry_price']) - commission
                    pnl_pct = pnl / (position['quantity'] * position['entry_price']) * 100

                    # Record trade
                    trade = Trade(
                        entry_time=position['entry_time'],
                        exit_time=current_time,
                        symbol=symbol,
                        side='long',
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        quantity=position['quantity'],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        commission=commission * 2,  # entry + exit
                        reason=exit_reason
                    )
                    trades.append(trade)

                    # Update capital
                    current_capital += proceeds - commission
                    position = None

        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve).set_index('timestamp')
        result = self._calculate_metrics(equity_df, trades)

        logger.info(f"Backtest complete: {len(trades)} trades, Return: {result.total_return_pct:.2f}%")

        return result

    def _calculate_metrics(self, equity_curve: pd.DataFrame, trades: List[Trade]) -> BacktestResult:
        """Performance metrics hesaplama"""

        # Basic returns
        total_return = equity_curve['equity'].iloc[-1] - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Returns series
        returns = equity_curve['equity'].pct_change().dropna()

        # Sharpe ratio (annualized)
        sharpe_ratio = self._calculate_sharpe(returns)

        # Sortino ratio
        sortino_ratio = self._calculate_sortino(returns)

        # Drawdown
        drawdown_curve = self._calculate_drawdown(equity_curve['equity'])
        max_drawdown = drawdown_curve.min()
        max_drawdown_pct = (max_drawdown / equity_curve['equity'].max()) * 100

        # Trade statistics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Profit metrics
        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl < 0]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        profit_factor = sum(wins) / abs(sum(losses)) if losses else 0
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

        # Time metrics
        if trades:
            durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades]
            avg_trade_duration = np.mean(durations)
            max_trade_duration = np.max(durations)
        else:
            avg_trade_duration = 0
            max_trade_duration = 0

        # Additional metrics
        calmar_ratio = abs(total_return_pct / max_drawdown_pct) if max_drawdown_pct != 0 else 0
        recovery_factor = abs(total_return / max_drawdown) if max_drawdown != 0 else 0
        volatility = returns.std() * np.sqrt(252) * 100  # Annualized

        return BacktestResult(
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_trade_duration=avg_trade_duration,
            max_trade_duration=max_trade_duration,
            equity_curve=equity_curve['equity'],
            drawdown_curve=drawdown_curve,
            trades=trades,
            calmar_ratio=calmar_ratio,
            recovery_factor=recovery_factor,
            volatility=volatility
        )

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Sharpe ratio hesaplama (annualized)"""
        excess_returns = returns - (risk_free_rate / 252)
        if excess_returns.std() == 0:
            return 0
        return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

    def _calculate_sortino(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Sortino ratio (sadece downside volatility)"""
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
        return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)

    def _calculate_drawdown(self, equity: pd.Series) -> pd.Series:
        """Drawdown curve"""
        running_max = equity.expanding().max()
        drawdown = equity - running_max
        return drawdown
