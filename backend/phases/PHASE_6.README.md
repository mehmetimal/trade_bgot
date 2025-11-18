# PHASE 6: API & Backend (FastAPI) - Tamamlandı ✅

## 🎯 Tamamlanan İşler

### ✅ Task 6.1: FastAPI Backend
- REST API endpointleri: Backtest, Paper Trading, Strategies
- WebSocket market-data yayını (AAPL, 2sn aralık)
- Global exception handler ve CORS middleware
- Swagger/Redoc dokümantasyonu (`/docs`, `/redoc`)

### ✅ Task 6.2: Real-time Data Pipeline
- WebSocket endpoint ile canlı fiyat yayını
- Basit broadcast ve client yönetimi yapısı (örnek)

### ✅ Task 6.3: Paper Trading API
- Portföy özeti, pozisyonlar ve emirler endpointleri
- Emir yerleştirme ve iptal işlemleri
- Engine durum ve risk metrikleri uçları

### ⏳ Task 6.4: Rate Limiting ve Güvenlik (Planlandı)
- API key/JWT tabanlı kimlik doğrulama
- Rate limiting (global ve per-endpoint)

---

## 📁 İlgili Dosyalar
- `backend/api/main.py` (FastAPI ana uygulama)
- `backend/api/routes/backtest.py` (Backtest rotaları)
- `backend/api/routes/paper_trading.py` (Paper trading rotaları)
- `backend/api/routes/strategies.py` (Strateji rotaları)
- `backend/api/security.py` (API key auth)
- `backend/.env` (lokal geliştirme env - gitignore)
- `backend/.env.example` (örnek env dosyası)

---

## 🔌 Endpoints

- `GET /api/info` → API bilgisi (`backend/api/main.py:106`)
- `GET /api/backtest/*` → Backtest API (`backend/api/routes/backtest.py:1`)
- `GET /api/paper-trading/portfolio` → Portföy özeti (`backend/api/routes/paper_trading.py:17`)
- `GET /api/paper-trading/positions` → Açık pozisyonlar (`backend/api/routes/paper_trading.py:21`)
- `GET /api/paper-trading/orders?status=` → Emirler (`backend/api/routes/paper_trading.py:25`)
- `POST /api/paper-trading/orders` → Emir yerleştir (`backend/api/routes/paper_trading.py:30`)
- `DELETE /api/paper-trading/orders/{order_id}` → Emir iptal (`backend/api/routes/paper_trading.py:45`)
- `GET /api/paper-trading/status` → Engine durumu (`backend/api/routes/paper_trading.py:52`)
- `GET /api/strategies/list` → Strateji listesi (`backend/api/routes/strategies.py:5`)
- `GET /api/strategies/defaults/{strategy_name}` → Varsayılan parametreler (`backend/api/routes/strategies.py:12`)
- `WS /ws/market-data` → Canlı fiyat yayını (`backend/api/main.py:146`)

---

## 🚀 Hızlı Başlangıç

```bash
cd backend
uv run uvicorn api.main:app --reload
```

Test örnekleri:
- `GET http://127.0.0.1:8000/api/info`
- `POST http://127.0.0.1:8000/api/paper-trading/orders`
  Body: `{ "symbol":"AAPL", "side":"buy", "quantity":5, "order_type":"market" }`
- `WS ws://127.0.0.1:8000/ws/market-data`

---

## 📚 Örnek İstek/Response

### Info
```json
{
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
```

### Strategies
`GET /api/strategies/list`
```json
[
  {"name":"simple_ma","label":"Simple MA"},
  {"name":"rsi_ma","label":"RSI + MA"}
]
```

`GET /api/strategies/defaults/simple_ma`
```json
{
  "ma_fast": 10,
  "ma_slow": 30,
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.04
}
```

### Paper Trading
`POST /api/paper-trading/orders`
```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 5,
  "order_type": "market"
}
```

Response
```json
{
  "order_id": "ORD-6251C838AF41",
  "symbol": "AAPL",
  "side": "buy",
  "order_type": "market",
  "quantity": 5.0,
  "price": null,
  "stop_price": null,
  "status": "filled",
  "filled_quantity": 5.0,
  "avg_fill_price": 267.59373,
  "created_at": "2025-11-18T16:46:31.024156",
  "updated_at": "2025-11-18T16:46:31.024381",
  "filled_at": "2025-11-18T16:46:31.024381",
  "commission": 1.33796865,
  "slippage": 0.66865
}
```

`GET /api/paper-trading/orders`
```json
[
  {
    "order_id": "ORD-6251C838AF41",
    "symbol": "AAPL",
    "side": "buy",
    "order_type": "market",
    "quantity": 5.0,
    "status": "filled"
  }
]
```

`POST /api/paper-trading/orders` (pending örneği)
```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 1,
  "order_type": "limit",
  "price": 1.0
}
```

`GET /api/paper-trading/orders?status=pending`
```json
[
  {
    "order_id": "ORD-A37591523261",
    "symbol": "AAPL",
    "side": "buy",
    "order_type": "limit",
    "quantity": 1.0,
    "price": 1.0,
    "status": "pending"
  }
]
```

`DELETE /api/paper-trading/orders/{order_id}`
```json
{
  "status": "cancelled",
  "order_id": "ORD-A37591523261"
}
```

`GET /api/paper-trading/portfolio`
```json
{
  "portfolio_value": 10000,
  "cash_balance": 10000,
  "total_pnl": 0,
  "return_pct": 0.0,
  "open_positions": 0,
  "total_trades": 0,
  "win_rate": 0
}
```

### Backtest
`POST /api/backtest/run`
```json
{
  "symbol": "AAPL",
  "strategy_name": "simple_ma",
  "parameters": {"ma_fast":10, "ma_slow":30, "stop_loss_pct":0.02, "take_profit_pct":0.04},
  "period": "1y",
  "interval": "1d",
  "initial_capital": 10000
}
```

Response
```json
{
  "backtest_id": "BT-82C131A81F36",
  "status": "running",
  "message": "Backtest started. Use GET /api/backtest/status/BT-82C131A81F36 to check progress."
}
```

`GET /api/backtest/status/{backtest_id}`
```json
{
  "status": "completed",
  "progress": 100,
  "started_at": "2025-11-18T16:46:43.530446",
  "completed_at": "2025-11-18T16:46:43.658191"
}
```

### WebSocket
`WS /ws/market-data`
```json
{"symbol":"AAPL","last":267.46}
```

### Authentication
- Header: `x-api-key: dev-key`
- Korunan yollar: `/api/backtest/*`, `/api/paper-trading/*`, `/api/strategies/*`
- Yanlış anahtar örneği (401):
```json
{"detail":"Unauthorized"}
```

Env yapılandırması:
- Dosya: `backend/.env`
```
API_KEY=dev-key
RATE_LIMIT=20
WINDOW_SEC=60
```
- Yükleme: `dotenv` otomatik yüklenir (`backend/api/main.py`)

### Rate Limiting
- Limit: 20 istek/60sn, IP+path bazlı
- Aşımda cevap (429):
```json
{"detail":"Too Many Requests"}
```


## ✅ Acceptance Criteria
- Backtest endpointleri sonuç döndürüyor
- Paper trading endpointleri portföy/pozisyon/emir bilgisi sağlıyor
- WebSocket canlı veri yayınını sağlıyor
- Global exception ve CORS yapılandırması aktif
- Dokümantasyon `/docs` altında erişilebilir

---