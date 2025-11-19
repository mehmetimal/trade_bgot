"""
Optimization API Routes - Automatic Parameter Optimization
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Global optimization status
optimization_status = {
    "running": False,
    "progress": 0,
    "current_symbol": None,
    "results": {}
}


class OptimizationRequest(BaseModel):
    symbols: List[str] = ["AAPL", "TSLA", "GOOGL"]
    strategy: str = "combined"  # or "ma_crossover", "rsi"
    optimization_metric: str = "sharpe_ratio"  # or "total_return", "calmar_ratio"
    optimization_period: str = "1y"  # Historical data period


@router.post("/run")
async def run_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Run parameter optimization using vectorbt

    This finds the BEST parameters automatically!
    - Runs THOUSANDS of backtests
    - Finds optimal parameters for each symbol
    - Saves results for auto-trading

    No manual input needed - fully automated!
    """
    global optimization_status

    if optimization_status["running"]:
        raise HTTPException(
            status_code=400,
            detail="Optimization already running"
        )

    # Start optimization in background
    background_tasks.add_task(
        _run_optimization_background,
        request.symbols,
        request.strategy,
        request.optimization_metric,
        request.optimization_period
    )

    return {
        "status": "started",
        "message": f"Optimization started for {len(request.symbols)} symbols",
        "symbols": request.symbols,
        "strategy": request.strategy,
        "metric": request.optimization_metric
    }


async def _run_optimization_background(
    symbols: List[str],
    strategy: str,
    metric: str,
    period: str
):
    """Background task to run optimization"""
    global optimization_status

    optimization_status["running"] = True
    optimization_status["progress"] = 0
    optimization_status["results"] = {}

    try:
        from optimization.vectorbt_optimizer import VectorbtOptimizer

        logger.info(f"🚀 Starting optimization: {strategy} for {symbols}")

        optimizer = VectorbtOptimizer(
            symbols=symbols,
            optimization_period=period,
            optimization_metric=metric
        )

        # Optimize all symbols
        total = len(symbols)
        for i, symbol in enumerate(symbols):
            optimization_status["current_symbol"] = symbol
            optimization_status["progress"] = int((i / total) * 100)

            try:
                if strategy == "ma_crossover":
                    results = optimizer.optimize_ma_crossover(symbol, top_n=1)
                elif strategy == "rsi":
                    results = optimizer.optimize_rsi_strategy(symbol, top_n=1)
                elif strategy == "combined":
                    results = optimizer.optimize_combined_strategy(symbol, top_n=1)
                else:
                    logger.error(f"Unknown strategy: {strategy}")
                    continue

                if results:
                    optimization_status["results"][symbol] = results[0]

            except Exception as e:
                logger.error(f"Optimization failed for {symbol}: {e}")

        # Save results
        optimizer.save_results("optimization_results.json")

        optimization_status["progress"] = 100
        optimization_status["current_symbol"] = None

        logger.info(f"✅ Optimization complete! Results saved.")

    except Exception as e:
        logger.error(f"Optimization error: {e}", exc_info=True)
    finally:
        optimization_status["running"] = False


@router.get("/status")
async def get_optimization_status():
    """Get current optimization status"""
    return optimization_status


@router.get("/results")
async def get_optimization_results():
    """Get optimization results"""
    try:
        import json
        import os

        filepath = "optimization_results.json"
        if not os.path.exists(filepath):
            return {"results": {}, "message": "No optimization results found"}

        with open(filepath, 'r') as f:
            results = json.load(f)

        return {
            "results": results,
            "count": len(results),
            "message": f"Found optimized parameters for {len(results)} symbols"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")


@router.get("/results/{symbol}")
async def get_symbol_optimization(symbol: str):
    """Get optimization results for specific symbol"""
    try:
        import json
        import os

        filepath = "optimization_results.json"
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="No optimization results found")

        with open(filepath, 'r') as f:
            results = json.load(f)

        if symbol not in results:
            raise HTTPException(
                status_code=404,
                detail=f"No optimization results for {symbol}"
            )

        return {
            "symbol": symbol,
            "parameters": results[symbol],
            "message": f"Optimized parameters for {symbol}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/results")
async def clear_optimization_results():
    """Clear optimization results"""
    try:
        import os

        filepath = "optimization_results.json"
        if os.path.exists(filepath):
            os.remove(filepath)
            return {"message": "Optimization results cleared"}
        else:
            return {"message": "No results to clear"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
