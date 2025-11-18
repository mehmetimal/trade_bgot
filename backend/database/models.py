"""
Database models for Trading Bot
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class OHLCV(Base):
    """Historical OHLCV data table"""
    __tablename__ = 'ohlcv_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    source = Column(String(20), default='yahoo')  # yahoo, binance, etc.
    created_at = Column(DateTime, default=datetime.now)

    # Composite index for fast queries
    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )

    def __repr__(self):
        return f"<OHLCV {self.symbol} {self.timestamp} {self.timeframe}>"


class Strategy(Base):
    """Trading strategy configurations"""
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    parameters = Column(JSON, nullable=False)  # Strategy parameters as JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Strategy {self.name}>"


class BacktestResult(Base):
    """Backtest results storage"""
    __tablename__ = 'backtest_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Performance metrics
    initial_capital = Column(Float, nullable=False)
    final_value = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float)
    max_drawdown_pct = Column(Float)

    # Trade statistics
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    profit_factor = Column(Float)

    # Additional data
    parameters = Column(JSON)  # Strategy parameters used
    trades = Column(JSON)  # List of all trades
    equity_curve = Column(JSON)  # Equity curve data

    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<BacktestResult {self.symbol} {self.start_date}>"


class PaperTrade(Base):
    """Paper trading orders"""
    __tablename__ = 'paper_trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(50), nullable=False, index=True)
    order_id = Column(String(50), unique=True, nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy/sell
    order_type = Column(String(20), nullable=False)  # market/limit/stop_loss
    quantity = Column(Float, nullable=False)
    price = Column(Float)  # For limit orders
    stop_price = Column(Float)  # For stop orders

    # Execution details
    status = Column(String(20), default='pending')  # pending/filled/cancelled/rejected
    filled_quantity = Column(Float, default=0)
    avg_fill_price = Column(Float)
    commission = Column(Float, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    filled_at = Column(DateTime)

    def __repr__(self):
        return f"<PaperTrade {self.order_id} {self.symbol} {self.side}>"


class PaperPosition(Base):
    """Paper trading positions"""
    __tablename__ = 'paper_positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(50), nullable=False, index=True)
    position_id = Column(String(50), unique=True, nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # long/short
    quantity = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)

    # P&L tracking
    realized_pnl = Column(Float, default=0)
    unrealized_pnl = Column(Float, default=0)

    # Status
    is_open = Column(Boolean, default=True)

    # Timestamps
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)

    def __repr__(self):
        return f"<PaperPosition {self.symbol} {self.quantity}>"


class Portfolio(Base):
    """Paper trading portfolio"""
    __tablename__ = 'portfolios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))

    # Capital tracking
    initial_balance = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)

    # Performance
    total_pnl = Column(Float, default=0)
    total_return_pct = Column(Float, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Portfolio {self.portfolio_id}>"


class PerformanceMetrics(Base):
    """Daily performance metrics snapshot"""
    __tablename__ = 'performance_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(50), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)

    # Portfolio values
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=False)

    # Daily metrics
    daily_pnl = Column(Float)
    daily_return_pct = Column(Float)

    # Cumulative metrics
    cumulative_pnl = Column(Float)
    cumulative_return_pct = Column(Float)

    # Risk metrics
    sharpe_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    volatility = Column(Float)

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_portfolio_date', 'portfolio_id', 'date'),
    )

    def __repr__(self):
        return f"<PerformanceMetrics {self.portfolio_id} {self.date}>"
