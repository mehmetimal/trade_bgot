"""
Trading Bot API - Main FastAPI Application
"""
from fastapi import FastAPI, Request, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

# Import routes
from api.routes import backtest, paper_trading, strategies, auto_trading, optimization
from api.routes import market_data
from data.yahoo_finance_collector import YahooFinanceCollector
import asyncio
from api.security import api_key_auth
import time
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Trading Bot API starting up...")
    logger.info("📊 Initializing components...")

    try:
        from paper_trading.strategy_runner import create_strategy_runner
        from api.routes.paper_trading import engine
        from api.routes import auto_trading as auto_routes
        runner = create_strategy_runner(
            engine=engine,
            strategy_name="combined",
            symbols=None,
            update_interval=10,
            market="turkish"
        )
        await runner.start()
        auto_routes.strategy_runner = runner
        logger.info("🤖 Auto-trading started at startup with combined strategy (turkish market)")
    except Exception as e:
        logger.error(f"Failed to auto-start trading: {e}")

    try:
        from services.data_update_service import DataUpdateService
        data_service = DataUpdateService()
        asyncio.create_task(data_service.run_daily_update())
        logger.info("🗓️ Daily data update scheduler started")
    except Exception as e:
        logger.error(f"Failed to start data update scheduler: {e}")

    yield

    # Shutdown
    logger.info("📊 Trading Bot API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="Production-ready trading bot with backtest and paper trading capabilities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with audit trail"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s with status {response.status_code}"
    )

    # Audit logging
    try:
        from utils.audit_logger import get_audit_logger
        audit_logger = get_audit_logger()
        audit_logger.log_api_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            response_time=process_time,
            client_ip=request.client.host if request.client else "unknown",
            metadata={"user_agent": request.headers.get("user-agent", "unknown")}
        )
    except Exception as e:
        logger.warning(f"Failed to audit log request: {e}")

    response.headers["X-Process-Time"] = str(process_time)
    return response


rate_store = {}
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "10000"))  # Much higher for development
WINDOW_SEC = int(os.environ.get("WINDOW_SEC", "60"))

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    key = f"{ip}:{request.url.path}"
    now = time.time()
    bucket = rate_store.get(key, [])
    bucket = [t for t in bucket if now - t < WINDOW_SEC]
    if len(bucket) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
    bucket.append(now)
    rate_store[key] = bucket
    return await call_next(request)


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.get("/api/info")
async def api_info():
    """API information"""
    return {
        "api_version": "1.0.0",
        "endpoints": {
            "backtest": "/api/backtest/*",
            "paper_trading": "/api/paper-trading/*",
            "strategies": "/api/strategies/*",
            "websocket": "/ws/market-data"
        },
        "features": [
            "Backtesting with 163 parameters",
            "Paper trading simulation",
            "Risk management",
            "Real-time market data",
            "Strategy optimization"
        ]
    }


# Include routers (authentication disabled for development)
app.include_router(
    backtest.router,
    prefix="/api/backtest",
    tags=["Backtest"]
)

app.include_router(
    paper_trading.router,
    prefix="/api/paper-trading",
    tags=["Paper Trading"]
)

app.include_router(
    strategies.router,
    prefix="/api/strategies",
    tags=["Strategies"]
)

app.include_router(
    auto_trading.router,
    prefix="/api/auto-trading",
    tags=["Auto Trading"]
)

app.include_router(
    optimization.router,
    prefix="/api/optimization",
    tags=["Parameter Optimization"]
)

app.include_router(
    market_data.router,
    prefix="/api/market",
    tags=["Market Data"]
)

@app.websocket("/ws/portfolio")
async def portfolio_websocket(websocket: WebSocket):
    """Real-time portfolio updates via WebSocket"""
    await websocket.accept()
    logger.info("WebSocket client connected for portfolio updates")

    try:
        from api.routes.paper_trading import engine

        while True:
            # Send portfolio updates
            portfolio = engine.get_portfolio_summary()
            positions = engine.get_positions()

            await websocket.send_json({
                "type": "portfolio_update",
                "portfolio": portfolio,
                "positions": positions,
                "timestamp": time.time()
            })

            await asyncio.sleep(5)  # Update every 5 seconds
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket client disconnected")
        await websocket.close()


@app.websocket("/ws/market-data")
async def market_data_websocket(websocket: WebSocket):
    """Real-time market data via WebSocket"""
    await websocket.accept()
    collector = YahooFinanceCollector()
    logger.info("WebSocket client connected for market data")

    try:
        # Get symbols from query params or use defaults
        from data.turkish_symbols import get_all_symbols
        symbols = get_all_symbols()[:10]  # Limit to 10 symbols

        while True:
            market_data = []
            for symbol in symbols:
                try:
                    info = collector.fetch_realtime_price(symbol)
                    if info:
                        market_data.append(info)
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol}: {e}")

            await websocket.send_json({
                "type": "market_data",
                "data": market_data,
                "timestamp": time.time()
            })

            await asyncio.sleep(10)  # Update every 10 seconds
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket client disconnected")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
