"""
Backtest API Endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from data.yahoo_finance_collector import YahooFinanceCollector
from backtest.engine import BacktestEngine
from strategies.simple_ma_strategy import SimpleMAStrategy, RSIMAStrategy
from database.db_manager import get_db_manager

router = APIRouter()

# In-memory storage for backtest results (in production, use Redis or database)
backtest_results = {}
backtest_status = {}


class BacktestRequest(BaseModel):
    """Backtest request model"""
    symbol: str = Field(..., description="Trading symbol (e.g., AAPL, BTC-USD)")
    strategy_name: str = Field(..., description="Strategy name (simple_ma, rsi_ma)")
    parameters: Dict = Field(..., description="Strategy parameters")
    period: str = Field(default="1y", description="Data period (1mo, 3mo, 6mo, 1y, 2y)")
    interval: str = Field(default="1d", description="Data interval (1d, 1h, 15m)")
    initial_capital: float = Field(default=10000, description="Initial capital")
    commission_pct: float = Field(default=0.001, description="Commission percentage")
    slippage_pct: float = Field(default=0.0005, description="Slippage percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "strategy_name": "simple_ma",
                "parameters": {
                    "ma_fast": 10,
                    "ma_slow": 30,
                    "stop_loss_pct": 0.02,
                    "take_profit_pct": 0.04
                },
                "period": "1y",
                "interval": "1d",
                "initial_capital": 10000
            }
        }


class BacktestResponse(BaseModel):
    """Backtest response model"""
    backtest_id: str
    status: str
    message: str


class BacktestResult(BaseModel):
    """Backtest result model"""
    backtest_id: str
    symbol: str
    strategy_name: str
    parameters: Dict
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    volatility: float
    created_at: str


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Run a backtest

    This endpoint starts a backtest in the background and returns immediately.
    Use the backtest_id to check status and retrieve results.
    """
    # Generate backtest ID
    backtest_id = f"BT-{uuid.uuid4().hex[:12].upper()}"

    # Initialize status
    backtest_status[backtest_id] = {
        "status": "running",
        "progress": 0,
        "started_at": datetime.now().isoformat()
    }

    # Run backtest in background
    background_tasks.add_task(
        _execute_backtest,
        backtest_id,
        request
    )

    return BacktestResponse(
        backtest_id=backtest_id,
        status="running",
        message=f"Backtest started. Use GET /api/backtest/status/{backtest_id} to check progress."
    )


@router.get("/status/{backtest_id}")
async def get_backtest_status(backtest_id: str):
    """Get backtest status"""
    if backtest_id not in backtest_status:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return backtest_status[backtest_id]


@router.get("/result/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(backtest_id: str):
    """Get backtest results"""
    if backtest_id not in backtest_results:
        # Check if still running
        if backtest_id in backtest_status:
            status = backtest_status[backtest_id]["status"]
            if status == "running":
                raise HTTPException(status_code=202, detail="Backtest still running")
            elif status == "failed":
                raise HTTPException(status_code=500, detail="Backtest failed")

        raise HTTPException(status_code=404, detail="Backtest not found")

    return backtest_results[backtest_id]


@router.get("/results", response_model=List[BacktestResult])
async def list_backtest_results(limit: int = 10):
    """List recent backtest results"""
    results = list(backtest_results.values())
    # Sort by created_at descending
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results[:limit]


@router.delete("/result/{backtest_id}")
async def delete_backtest_result(backtest_id: str):
    """Delete a backtest result"""
    if backtest_id in backtest_results:
        del backtest_results[backtest_id]

    if backtest_id in backtest_status:
        del backtest_status[backtest_id]

    return {"message": "Backtest result deleted", "backtest_id": backtest_id}


# Background task
async def _execute_backtest(backtest_id: str, request: BacktestRequest):
    """Execute backtest in background"""
    try:
        # Update status
        backtest_status[backtest_id]["status"] = "downloading_data"
        backtest_status[backtest_id]["progress"] = 10

        # Fetch data
        collector = YahooFinanceCollector()
        data = collector.fetch_historical_data(
            symbol=request.symbol,
            period=request.period,
            interval=request.interval
        )

        if data is None or len(data) < 50:
            backtest_status[backtest_id]["status"] = "failed"
            backtest_status[backtest_id]["error"] = "Insufficient data"
            return

        # Update status
        backtest_status[backtest_id]["status"] = "initializing_strategy"
        backtest_status[backtest_id]["progress"] = 30

        # Create strategy
        if request.strategy_name == "simple_ma":
            strategy = SimpleMAStrategy(parameters=request.parameters)
        elif request.strategy_name == "rsi_ma":
            strategy = RSIMAStrategy(parameters=request.parameters)
        else:
            backtest_status[backtest_id]["status"] = "failed"
            backtest_status[backtest_id]["error"] = f"Unknown strategy: {request.strategy_name}"
            return

        # Update status
        backtest_status[backtest_id]["status"] = "running_backtest"
        backtest_status[backtest_id]["progress"] = 50

        # Run backtest
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            commission_pct=request.commission_pct,
            slippage_pct=request.slippage_pct
        )

        result = engine.run_backtest(data, strategy, symbol=request.symbol)

        # Update status
        backtest_status[backtest_id]["status"] = "saving_results"
        backtest_status[backtest_id]["progress"] = 90

        # Save to database (optional)
        try:
            db = get_db_manager()

            # Save strategy
            strategy_id = db.save_strategy(
                name=f"{request.strategy_name}_{request.symbol}",
                parameters=request.parameters,
                description=f"Backtest on {request.symbol}"
            )

            # Save backtest result
            backtest_data = {
                'initial_capital': request.initial_capital,
                'final_value': result.total_return + request.initial_capital,
                'total_return': result.total_return,
                'total_return_pct': result.total_return_pct,
                'sharpe_ratio': result.sharpe_ratio,
                'sortino_ratio': result.sortino_ratio,
                'max_drawdown': result.max_drawdown,
                'max_drawdown_pct': result.max_drawdown_pct,
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'win_rate': result.win_rate,
                'avg_win': result.avg_win,
                'avg_loss': result.avg_loss,
                'profit_factor': result.profit_factor,
                'parameters': request.parameters,
                'trades': [t.to_dict() for t in result.trades]
            }

            db.save_backtest_result(
                strategy_id=strategy_id,
                symbol=request.symbol,
                timeframe=request.interval,
                start_date=data.index[0],
                end_date=data.index[-1],
                result=backtest_data
            )

        except Exception as e:
            print(f"Warning: Failed to save to database: {e}")

        # Store result
        backtest_results[backtest_id] = BacktestResult(
            backtest_id=backtest_id,
            symbol=request.symbol,
            strategy_name=request.strategy_name,
            parameters=request.parameters,
            total_return=result.total_return,
            total_return_pct=result.total_return_pct,
            sharpe_ratio=result.sharpe_ratio,
            sortino_ratio=result.sortino_ratio,
            calmar_ratio=result.calmar_ratio,
            max_drawdown=result.max_drawdown,
            max_drawdown_pct=result.max_drawdown_pct,
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            win_rate=result.win_rate,
            avg_win=result.avg_win,
            avg_loss=result.avg_loss,
            profit_factor=result.profit_factor,
            expectancy=result.expectancy,
            volatility=result.volatility,
            created_at=datetime.now().isoformat()
        )

        # Update status - completed
        backtest_status[backtest_id]["status"] = "completed"
        backtest_status[backtest_id]["progress"] = 100
        backtest_status[backtest_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        backtest_status[backtest_id]["status"] = "failed"
        backtest_status[backtest_id]["error"] = str(e)
        print(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()
