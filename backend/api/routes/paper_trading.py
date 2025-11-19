from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from paper_trading.engine import PaperTradingEngine

router = APIRouter()
engine = PaperTradingEngine(initial_capital=10000)


class OrderRequest(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    order_type: str = "market"  # "market", "limit"
    price: Optional[float] = None

@router.get("/portfolio")
async def get_portfolio():
    return engine.get_portfolio_summary()

@router.get("/positions")
async def get_positions():
    return [p.to_dict() for p in engine.get_positions()]

@router.get("/orders")
async def get_orders(status: Optional[str] = None):
    orders = engine.get_orders(status)
    return [o.to_dict() for o in orders]

@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    ok = engine.cancel_order(order_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Order not found or cannot cancel")
    return {"status": "cancelled", "order_id": order_id}

@router.get("/status")
async def get_status():
    return engine.get_status()

@router.get("/trades")
async def get_trades(symbol: Optional[str] = None):
    """Get closed trades history"""
    trades = engine.get_closed_trades(symbol)
    return [t.to_dict() for t in trades]

@router.get("/trade-markers")
async def get_trade_markers(symbol: Optional[str] = None):
    """Return entry/exit markers for chart overlay"""
    trades = engine.get_closed_trades(symbol)
    markers = []
    for t in trades:
        td = t.to_dict()
        markers.append({
            "symbol": td.get("symbol"),
            "type": "entry",
            "t": td.get("opened_at"),
            "price": td.get("entry_price")
        })
        markers.append({
            "symbol": td.get("symbol"),
            "type": "exit",
            "t": td.get("closed_at"),
            "price": td.get("exit_price")
        })
    return markers


@router.post("/orders")
async def create_order(request: OrderRequest):
    """
    Create a new order (for testing/manual trading)
    """
    try:
        order = engine.place_order(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_type=request.order_type,
            price=request.price
        )

        return {
            "status": "success",
            "order": order.to_dict(),
            "message": f"Order placed: {request.side} {request.quantity} {request.symbol}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))