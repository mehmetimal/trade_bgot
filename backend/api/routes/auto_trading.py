"""Auto Trading API Routes - Strategy-Driven Auto Trading"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Global strategy runner instance
strategy_runner = None


class StrategyConfig(BaseModel):
    strategy: str = "combined"
    symbols: Optional[List[str]] = None
    update_interval: int = 300  # 5 dakika - pozisyonlar daha uzun süre açık kalır
    market: str = "turkish"


@router.post("/start")
async def start_auto_trading(config: Optional[StrategyConfig] = None):
    """
    Start automated strategy-driven trading

    This is the CORE auto-trading feature:
    - Continuously monitors market data
    - Executes strategy on live data
    - Automatically places orders based on signals
    """
    global strategy_runner

    if strategy_runner and strategy_runner.running:
        raise HTTPException(status_code=400, detail="Auto-trading already running")

    try:
        # Import strategy runner
        from paper_trading.strategy_runner import create_strategy_runner
        from api.routes.paper_trading import engine

        # Create strategy runner
        strategy_runner = create_strategy_runner(
            engine=engine,
            strategy_name=config.strategy if config else "combined",
            symbols=config.symbols if config and config.symbols else None,
            update_interval=config.update_interval if config else 60,
            market=config.market if config else "turkish"
        )

        # Start the runner
        await strategy_runner.start()

        return {
            "status": "started",
            "message": "Auto-trading activated - Bot will execute trades based on strategy signals",
            "strategy": strategy_runner.strategy.__class__.__name__,
            "symbols": strategy_runner.symbols,
            "update_interval": strategy_runner.update_interval
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start auto-trading: {str(e)}")


@router.post("/stop")
async def stop_auto_trading():
    """Stop automated trading"""
    global strategy_runner

    if not strategy_runner or not strategy_runner.running:
        raise HTTPException(status_code=400, detail="Auto-trading not running")

    try:
        await strategy_runner.stop()
        return {
            "status": "stopped",
            "message": "Auto-trading deactivated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop auto-trading: {str(e)}")


@router.get("/status")
async def get_auto_trading_status():
    """Get auto-trading status and recent activity"""
    if not strategy_runner:
        return {
            "running": False,
            "strategy": None,
            "symbols": [],
            "update_interval": 0,
            "last_signals": {}
        }

    return strategy_runner.get_status()


@router.get("/signals")
async def get_recent_signals():
    """Get recent trading signals"""
    if not strategy_runner:
        return {"signals": []}

    return {
        "signals": strategy_runner.last_signals,
        "strategy": strategy_runner.strategy.__class__.__name__
    }


@router.put("/config")
async def update_config(config: StrategyConfig):
    """Update auto-trading configuration (requires restart)"""
    global strategy_runner

    if strategy_runner and strategy_runner.running:
        raise HTTPException(
            status_code=400,
            detail="Stop auto-trading before updating configuration"
        )

    return {
        "message": "Configuration will be applied on next start",
        "config": config.dict()
    }
