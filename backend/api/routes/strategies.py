from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List

router = APIRouter()

class StrategyInfo(BaseModel):
    name: str
    description: str
    parameters: Dict

@router.get("/list", response_model=List[StrategyInfo])
async def list_strategies():
    return [
        {
            "name": "simple_ma",
            "description": "Moving Average Crossover Strategy",
            "parameters": {"ma_fast": 10, "ma_slow": 30, "stop_loss_pct": 0.02, "take_profit_pct": 0.04}
        },
        {
            "name": "rsi_ma",
            "description": "RSI + MA Strategy",
            "parameters": {"ma_slow": 50, "rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70}
        }
    ]

@router.get("/{name}")
async def get_strategy(name: str):
    strategies = await list_strategies()
    for s in strategies:
        if s["name"] == name:
            return s
    return {"error": "Strategy not found"}
