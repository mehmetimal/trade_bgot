"""
Database Manager for Trading Bot
Handles all database operations
"""
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
import logging
import os

from database.models import Base, OHLCV, Strategy, BacktestResult, PaperTrade, PaperPosition, Portfolio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database operations manager"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection

        Args:
            connection_string: PostgreSQL connection string
                              If None, uses SQLite (data/trading_bot.db)
        """
        if connection_string is None:
            # Default to SQLite for development
            os.makedirs('data', exist_ok=True)
            connection_string = 'sqlite:///data/trading_bot.db'

        self.engine = create_engine(connection_string, echo=False)
        self.Session = sessionmaker(bind=self.engine)

        logger.info(f"Database connection established: {connection_string}")

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        logger.info("All tables created successfully")

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(self.engine)
        logger.warning("All tables dropped")

    # OHLCV Data Operations
    def insert_ohlcv_data(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        source: str = 'yahoo'
    ) -> int:
        """
        Insert OHLCV data into database

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 1h, 1d, etc.)
            data: DataFrame with columns: open, high, low, close, volume
            source: Data source name

        Returns:
            Number of rows inserted
        """
        session = self.Session()
        inserted_count = 0

        try:
            for timestamp, row in data.iterrows():
                # Check if data already exists
                existing = session.query(OHLCV).filter(
                    and_(
                        OHLCV.symbol == symbol,
                        OHLCV.timeframe == timeframe,
                        OHLCV.timestamp == timestamp
                    )
                ).first()

                if existing is None:
                    ohlcv = OHLCV(
                        symbol=symbol,
                        timestamp=timestamp,
                        timeframe=timeframe,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=float(row['volume']),
                        source=source
                    )
                    session.add(ohlcv)
                    inserted_count += 1

            session.commit()
            logger.info(f"Inserted {inserted_count} rows for {symbol} ({timeframe})")
            return inserted_count

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting OHLCV data: {e}")
            raise
        finally:
            session.close()

    def get_ohlcv_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Retrieve OHLCV data from database

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with OHLCV data
        """
        session = self.Session()

        try:
            query = session.query(OHLCV).filter(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe
            )

            if start_date:
                query = query.filter(OHLCV.timestamp >= start_date)
            if end_date:
                query = query.filter(OHLCV.timestamp <= end_date)

            results = query.order_by(OHLCV.timestamp).all()

            if not results:
                logger.warning(f"No data found for {symbol} ({timeframe})")
                return pd.DataFrame()

            # Convert to DataFrame
            data = pd.DataFrame([
                {
                    'timestamp': r.timestamp,
                    'open': r.open,
                    'high': r.high,
                    'low': r.low,
                    'close': r.close,
                    'volume': r.volume
                }
                for r in results
            ])

            data.set_index('timestamp', inplace=True)
            logger.info(f"Retrieved {len(data)} rows for {symbol} ({timeframe})")
            return data

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving OHLCV data: {e}")
            raise
        finally:
            session.close()

    def get_available_symbols(self, timeframe: Optional[str] = None) -> List[str]:
        """Get list of available symbols in database"""
        session = self.Session()

        try:
            query = session.query(OHLCV.symbol).distinct()

            if timeframe:
                query = query.filter(OHLCV.timeframe == timeframe)

            symbols = [r[0] for r in query.all()]
            return symbols

        finally:
            session.close()

    # Strategy Operations
    def save_strategy(self, name: str, parameters: Dict, description: str = "") -> int:
        """Save strategy configuration"""
        session = self.Session()

        try:
            # Check if strategy exists
            existing = session.query(Strategy).filter(Strategy.name == name).first()

            if existing:
                existing.parameters = parameters
                existing.description = description
                existing.updated_at = datetime.now()
            else:
                strategy = Strategy(
                    name=name,
                    description=description,
                    parameters=parameters
                )
                session.add(strategy)

            session.commit()

            strategy_id = existing.id if existing else strategy.id
            logger.info(f"Strategy '{name}' saved with ID {strategy_id}")
            return strategy_id

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error saving strategy: {e}")
            raise
        finally:
            session.close()

    def get_strategy(self, name: str) -> Optional[Dict]:
        """Get strategy by name"""
        session = self.Session()

        try:
            strategy = session.query(Strategy).filter(Strategy.name == name).first()

            if strategy:
                return {
                    'id': strategy.id,
                    'name': strategy.name,
                    'description': strategy.description,
                    'parameters': strategy.parameters,
                    'is_active': strategy.is_active
                }
            return None

        finally:
            session.close()

    # Backtest Results Operations
    def save_backtest_result(
        self,
        strategy_id: int,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        result: Dict
    ) -> int:
        """Save backtest result"""
        session = self.Session()

        try:
            backtest = BacktestResult(
                strategy_id=strategy_id,
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_capital=result.get('initial_capital', 10000),
                final_value=result.get('final_value'),
                total_return=result.get('total_return'),
                total_return_pct=result.get('total_return_pct'),
                sharpe_ratio=result.get('sharpe_ratio'),
                sortino_ratio=result.get('sortino_ratio'),
                max_drawdown=result.get('max_drawdown'),
                max_drawdown_pct=result.get('max_drawdown_pct'),
                total_trades=result.get('total_trades'),
                winning_trades=result.get('winning_trades'),
                losing_trades=result.get('losing_trades'),
                win_rate=result.get('win_rate'),
                avg_win=result.get('avg_win'),
                avg_loss=result.get('avg_loss'),
                profit_factor=result.get('profit_factor'),
                parameters=result.get('parameters'),
                trades=result.get('trades'),
                equity_curve=result.get('equity_curve')
            )

            session.add(backtest)
            session.commit()

            logger.info(f"Backtest result saved with ID {backtest.id}")
            return backtest.id

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error saving backtest result: {e}")
            raise
        finally:
            session.close()

    def get_backtest_results(
        self,
        strategy_id: Optional[int] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get backtest results with optional filtering"""
        session = self.Session()

        try:
            query = session.query(BacktestResult)

            if strategy_id:
                query = query.filter(BacktestResult.strategy_id == strategy_id)
            if symbol:
                query = query.filter(BacktestResult.symbol == symbol)

            results = query.order_by(BacktestResult.created_at.desc()).limit(limit).all()

            return [
                {
                    'id': r.id,
                    'strategy_id': r.strategy_id,
                    'symbol': r.symbol,
                    'timeframe': r.timeframe,
                    'total_return_pct': r.total_return_pct,
                    'sharpe_ratio': r.sharpe_ratio,
                    'max_drawdown_pct': r.max_drawdown_pct,
                    'win_rate': r.win_rate,
                    'total_trades': r.total_trades,
                    'created_at': r.created_at
                }
                for r in results
            ]

        finally:
            session.close()

    # Data Statistics
    def get_data_statistics(self) -> Dict:
        """Get database statistics"""
        session = self.Session()

        try:
            stats = {
                'total_ohlcv_rows': session.query(OHLCV).count(),
                'total_symbols': session.query(OHLCV.symbol).distinct().count(),
                'total_strategies': session.query(Strategy).count(),
                'total_backtest_results': session.query(BacktestResult).count(),
                'total_paper_trades': session.query(PaperTrade).count(),
            }

            return stats

        finally:
            session.close()


# Singleton instance
_db_manager = None


def get_db_manager(connection_string: Optional[str] = None) -> DatabaseManager:
    """Get or create database manager instance"""
    global _db_manager

    if _db_manager is None:
        _db_manager = DatabaseManager(connection_string)

    return _db_manager
