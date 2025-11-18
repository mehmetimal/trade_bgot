# Trading Bot - Mevcut Yetenekler ve Geliştirme Planı

## 📊 Mevcut Yetenekler (Current Capabilities)

### ✅ 1. Veri Altyapısı (Data Infrastructure)
- **Yahoo Finance entegrasyonu**
  - Historik veri çekme (1d, 1wk, 1mo intervals)
  - Real-time fiyat verileri
  - OHLCV (Open, High, Low, Close, Volume) data
  - Desteklenen semboller: Stocks, Crypto, ETF

### ✅ 2. Backtest Engine
- **163 Parametre Sistemi**
  - Technical Indicators: 50+ parametre (MA, RSI, MACD, Bollinger, ATR)
  - Risk Management: 20+ parametre (position size, stop loss, take profit)
  - Entry/Exit Conditions: 30+ parametre
  - Position Sizing: 15+ parametre
  - Market Conditions: 28+ parametre

- **Backtest Özellikleri**
  - Realistic slippage simulation (0.05%)
  - Commission tracking (0.1%)
  - Stop loss & Take profit execution
  - Performance metrics:
    - Sharpe Ratio
    - Sortino Ratio
    - Calmar Ratio
    - Max Drawdown
    - Profit Factor
    - Win Rate
    - Expectancy
  - Equity curve generation
  - Trade logging ve analiz

- **Mevcut Stratejiler**
  - SimpleMAStrategy: Moving Average Crossover
  - RSIMAStrategy: RSI + MA Combination
  - Base Strategy Framework (custom strategy için)

### ✅ 3. Paper Trading Engine
- **Order Management**
  - Order Types: MARKET, LIMIT, STOP, STOP_LIMIT
  - Order Status: PENDING, FILLED, CANCELLED, REJECTED
  - Automatic order execution simulation
  - Commission ve slippage calculation

- **Portfolio Management**
  - Position tracking (açık pozisyonlar)
  - Real-time P&L calculation (realized & unrealized)
  - Trade history tracking
  - Portfolio value calculation
  - Win rate ve trade statistics

- **Risk Management**
  - Position size calculation
  - Max position size limits (default: 20%)
  - Total exposure limits (default: 95%)
  - Drawdown monitoring (max: 15%)
  - Daily loss limits (max: 5%)
  - Stop loss & take profit automation

### ✅ 4. Backend API (FastAPI)
- **REST API Endpoints**

  **Backtest:**
  - `POST /api/backtest/run` - Run backtest
  - `GET /api/backtest/status/{id}` - Check status
  - `GET /api/backtest/result/{id}` - Get results

  **Paper Trading:**
  - `GET /api/paper-trading/portfolio` - Portfolio summary
  - `GET /api/paper-trading/positions` - Open positions
  - `GET /api/paper-trading/orders` - Order history
  - `POST /api/paper-trading/orders` - Place order
  - `DELETE /api/paper-trading/orders/{id}` - Cancel order
  - `GET /api/paper-trading/status` - Engine status

  **Strategies:**
  - `GET /api/strategies/list` - List strategies
  - `GET /api/strategies/{name}` - Strategy details

- **WebSocket Support**
  - `ws://localhost:8000/ws/market-data` - Real-time market data stream (ALTYAPI HAZIR AMA KULLANILMIYOR)

### ✅ 5. Frontend Dashboard (React)
- **Portfolio Summary**
  - Total Value
  - Cash Balance
  - Total P&L
  - Return %

- **Open Positions Table**
  - Symbol, Quantity, Avg Price
  - Current Price
  - Unrealized P&L & %

- **Real-time Updates**
  - 5 saniyede bir otomatik güncelleme

### ✅ 6. Deployment
- **Docker Containerization**
  - Backend container (Python 3.13 + FastAPI)
  - Frontend container (React + Nginx)
  - Nginx reverse proxy
  - docker-compose orchestration
  - Port 85 (production)

---

## ❌ Eksik Özellikler (Missing Features)

### 1. Dashboard'dan Trade Yapma (Place Orders from UI)
**Mevcut Durum:** API endpoint var ama UI yok
**Eksikler:**
- Order placement formu (symbol, side, quantity, order type)
- Order türü seçimi (Market, Limit, Stop)
- Real-time order status gösterimi
- Order validation ve error handling

### 2. Aktif Strateji Gösterimi (Active Strategy Display)
**Mevcut Durum:** Strategy listesi API'de var ama kullanımda yok
**Eksikler:**
- Hangi stratejinin aktif olduğunu gösterme
- Strateji parametrelerini gösterme
- Strateji performans metriklerini gösterme
- Multiple strategy desteği

### 3. Canlı Veri Akışı (Live Data Stream)
**Mevcut Durum:** WebSocket altyapısı var ama kullanılmıyor
**Eksikler:**
- WebSocket client implementasyonu
- Real-time price updates (5 sn yerine instant)
- Live chart integration
- Market data subscription management

### 4. Kendi Stratejilerini Import Etme (Custom Strategy Import)
**Mevcut Durum:** Base strategy framework var ama upload yok
**Eksikler:**
- Strategy file upload endpoint
- Strategy validation
- Dynamic strategy loading
- Strategy versioning
- Strategy marketplace/library

### 5. Dashboard'dan Strateji Değiştirme (Modify Strategies from UI)
**Mevcut Durum:** Hiç yok
**Eksikler:**
- Strategy parameter editor
- Real-time parameter validation
- Strategy backtesting from UI
- Parameter optimization tool
- Strategy comparison tool

### 6. Trade History & Analytics
**Mevcut Durum:** Backend'de var ama UI yok
**Eksikler:**
- Closed trades table
- Trade performance analytics
- Win/Loss ratio charts
- Profit/Loss distribution
- Trade duration analysis

### 7. Risk Management Dashboard
**Mevcut Durum:** Backend'de var ama UI yok
**Eksikler:**
- Current risk metrics display
- Drawdown chart
- Position sizing calculator
- Risk parameter editor

### 8. Real-time Charts
**Mevcut Durum:** Hiç yok
**Eksikler:**
- Price charts (candlestick, line)
- Technical indicator overlays
- Entry/Exit points visualization
- Equity curve chart

---

## 🎯 Geliştirme Planı (Development Plan)

## PHASE 10: Dashboard Trading Features

### Task 10.1: Order Placement UI ⭐ HIGH PRIORITY
**Açıklama:** Dashboard'dan order yerleştirme formu

**Subtasks:**
- [ ] 10.1.1: Order Form Component oluştur
  - Symbol input (autocomplete with search)
  - Side selector (Buy/Sell buttons)
  - Quantity input (numeric validation)
  - Order type selector (Market, Limit, Stop, Stop-Limit)
  - Price input (limit/stop orders için)
  - Estimated cost/proceeds calculator

- [ ] 10.1.2: Order Validation
  - Client-side validation (min/max quantity, price format)
  - Balance check before submit
  - Risk check integration
  - Confirmation dialog

- [ ] 10.1.3: Order Execution Feedback
  - Loading state while order processing
  - Success/Error notifications
  - Order confirmation message
  - Auto-refresh positions after order

- [ ] 10.1.4: Quick Trade Buttons
  - Quick buy/sell from positions table
  - Close position button
  - Market order shortcut

**Dosyalar:**
- `frontend/src/components/OrderForm.jsx` (YENİ)
- `frontend/src/components/OrderButton.jsx` (YENİ)
- `frontend/src/components/Dashboard.jsx` (GÜNCELLE)
- `frontend/src/services/api.js` (MEVCUT - placeOrder fonksiyonu var)

**API Endpoints:** ✅ HAZIR
- `POST /api/paper-trading/orders`

**Tahmini Süre:** 4-6 saat

---

### Task 10.2: Active Orders & Trade History ⭐ HIGH PRIORITY
**Açıklama:** Pending orders ve trade history görüntüleme

**Subtasks:**
- [ ] 10.2.1: Active Orders Table
  - Pending orders listesi
  - Order details (symbol, type, quantity, price)
  - Order status (pending, partial fill)
  - Cancel order button
  - Auto-refresh every 2 seconds

- [ ] 10.2.2: Trade History Table
  - Completed trades listesi
  - Trade details (entry/exit price, P&L, duration)
  - Filter by symbol, date range
  - Pagination (10-20 trades per page)
  - Export to CSV functionality

- [ ] 10.2.3: Order Details Modal
  - Click trade to view details
  - Full order information
  - Execution timeline
  - Related trades (for same symbol)

**Dosyalar:**
- `frontend/src/components/ActiveOrders.jsx` (YENİ)
- `frontend/src/components/TradeHistory.jsx` (YENİ)
- `frontend/src/components/OrderDetailsModal.jsx` (YENİ)
- `frontend/src/components/Dashboard.jsx` (GÜNCELLE)

**API Endpoints:**
- ✅ `GET /api/paper-trading/orders` (MEVCUT)
- ❌ `GET /api/paper-trading/trades` (YENİ - EKLENECEK)

**Backend Değişiklik:**
- `backend/api/routes/paper_trading.py` (GÜNCELLE - trades endpoint ekle)

**Tahmini Süre:** 5-7 saat

---

## PHASE 11: Strategy Management

### Task 11.1: Active Strategy Display ⭐ MEDIUM PRIORITY
**Açıklama:** Aktif stratejinin gösterilmesi ve detayları

**Subtasks:**
- [ ] 11.1.1: Strategy Info Panel
  - Active strategy name
  - Strategy description
  - Current parameters
  - Strategy status (active/paused)
  - Performance since activation (P&L, trades)

- [ ] 11.1.2: Strategy Selector
  - Dropdown/list of available strategies
  - Switch between strategies
  - Confirmation before switch
  - Strategy comparison preview

- [ ] 11.1.3: Strategy Performance Metrics
  - Win rate for active strategy
  - Average profit per trade
  - Best/Worst trade
  - Current drawdown
  - Sharpe ratio (real-time)

**Dosyalar:**
- `frontend/src/components/StrategyPanel.jsx` (YENİ)
- `frontend/src/components/StrategySelector.jsx` (YENİ)
- `frontend/src/components/Dashboard.jsx` (GÜNCELLE)

**API Endpoints:**
- ✅ `GET /api/strategies/list` (MEVCUT)
- ❌ `GET /api/paper-trading/active-strategy` (YENİ)
- ❌ `POST /api/paper-trading/set-strategy` (YENİ)

**Backend Değişiklik:**
- `backend/api/routes/paper_trading.py` (GÜNCELLE)
- `backend/paper_trading/engine.py` (GÜNCELLE - strategy tracking ekle)

**Tahmini Süre:** 6-8 saat

---

### Task 11.2: Strategy Parameter Editor ⭐ HIGH PRIORITY
**Açıklama:** Dashboard'dan strateji parametrelerini düzenleme

**Subtasks:**
- [ ] 11.2.1: Parameter Editor Component
  - Dynamic form based on strategy parameters
  - Input validation (min/max, type checking)
  - Parameter descriptions/tooltips
  - Real-time validation feedback
  - Reset to defaults button

- [ ] 11.2.2: Parameter Presets
  - Save parameter configurations
  - Load saved presets
  - Preset management (CRUD)
  - Import/Export presets as JSON

- [ ] 11.2.3: Parameter Optimization Helper
  - Suggest optimal parameter ranges
  - Quick backtest with new parameters
  - Parameter impact visualization
  - A/B testing between parameter sets

- [ ] 11.2.4: Live Parameter Update
  - Apply parameters without restart
  - Validation before apply
  - Rollback on error
  - Parameter change history

**Dosyalar:**
- `frontend/src/components/ParameterEditor.jsx` (YENİ)
- `frontend/src/components/ParameterPresets.jsx` (YENİ)
- `frontend/src/components/StrategyPanel.jsx` (GÜNCELLE)

**API Endpoints:**
- ❌ `GET /api/strategies/{name}/parameters` (YENİ)
- ❌ `PUT /api/strategies/active/parameters` (YENİ)
- ❌ `GET /api/strategies/presets` (YENİ)
- ❌ `POST /api/strategies/presets` (YENİ)

**Backend Değişiklik:**
- `backend/api/routes/strategies.py` (GÜNCELLE)
- `backend/strategies/parameters.py` (GÜNCELLE - validation logic)
- `backend/paper_trading/engine.py` (GÜNCELLE - dynamic parameter update)

**Tahmini Süre:** 8-10 saat

---

### Task 11.3: Custom Strategy Upload ⭐ MEDIUM PRIORITY
**Açıklama:** Kendi stratejilerini import etme

**Subtasks:**
- [ ] 11.3.1: Strategy Upload UI
  - File upload component (drag & drop)
  - Python file validation
  - Strategy preview before upload
  - Upload progress indicator

- [ ] 11.3.2: Strategy Validation Backend
  - Python syntax validation
  - BaseStrategy inheritance check
  - Required methods validation
  - Parameter validation
  - Security checks (no malicious code)

- [ ] 11.3.3: Strategy Library
  - List uploaded strategies
  - Strategy metadata (name, description, author)
  - Delete/Archive strategies
  - Version management
  - Strategy testing environment

- [ ] 11.3.4: Strategy Template Generator
  - Generate base strategy template
  - Example strategy templates
  - Parameter definition helper
  - Documentation generator

**Dosyalar:**
- `frontend/src/components/StrategyUpload.jsx` (YENİ)
- `frontend/src/components/StrategyLibrary.jsx` (YENİ)
- `backend/api/routes/strategies.py` (GÜNCELLE)
- `backend/strategies/loader.py` (YENİ - dynamic strategy loading)
- `backend/strategies/validator.py` (YENİ - strategy validation)

**API Endpoints:**
- ❌ `POST /api/strategies/upload` (YENİ - multipart/form-data)
- ❌ `GET /api/strategies/user` (YENİ - user uploaded strategies)
- ❌ `DELETE /api/strategies/{id}` (YENİ)
- ❌ `POST /api/strategies/validate` (YENİ - validate before upload)

**Backend Değişiklik:**
- Dynamic strategy import system
- Strategy storage (file system or DB)
- Sandbox environment for strategy execution

**Güvenlik Önlemleri:**
- Code sandboxing
- Resource limits (CPU, memory)
- Network access restrictions
- Dangerous function blacklist

**Tahmini Süre:** 12-15 saat

---

## PHASE 12: Real-time Data & WebSocket

### Task 12.1: WebSocket Integration ⭐ HIGH PRIORITY
**Açıklama:** Real-time veri akışı implementasyonu

**Subtasks:**
- [ ] 12.1.1: WebSocket Client Setup
  - WebSocket connection manager
  - Auto-reconnect on disconnect
  - Connection status indicator
  - Error handling & logging

- [ ] 12.1.2: Market Data Subscription
  - Subscribe to symbols
  - Unsubscribe from symbols
  - Multiple symbol support
  - Subscription management UI

- [ ] 12.1.3: Real-time Price Updates
  - Update position prices instantly
  - Update portfolio value
  - Price change indicators (up/down arrows)
  - Flash animation on price change

- [ ] 12.1.4: WebSocket Message Types
  - Price updates
  - Order fills
  - Position updates
  - Risk alerts
  - Strategy signals

**Dosyalar:**
- `frontend/src/services/websocket.js` (YENİ)
- `frontend/src/hooks/useWebSocket.js` (YENİ)
- `frontend/src/components/Dashboard.jsx` (GÜNCELLE)
- `backend/api/main.py` (GÜNCELLE - WebSocket logic)

**WebSocket Endpoints:**
- ✅ `ws://localhost:8000/ws/market-data` (ALTYAPI VAR)
- Kullanımı aktif hale getir

**Backend Değişiklik:**
- WebSocket message broadcasting
- Client subscription tracking
- Real-time data fetching from Yahoo Finance

**Tahmini Süre:** 6-8 saat

---

### Task 12.2: Live Price Charts ⭐ MEDIUM PRIORITY
**Açıklama:** Real-time fiyat grafikleri

**Subtasks:**
- [ ] 12.2.1: Chart Library Integration
  - TradingView Lightweight Charts veya Chart.js
  - Candlestick chart component
  - Line chart component
  - Chart configuration

- [ ] 12.2.2: Real-time Chart Updates
  - WebSocket'ten gelen data ile chart update
  - Smooth animation
  - Auto-scroll (follow price)
  - Zoom & pan controls

- [ ] 12.2.3: Technical Indicators on Chart
  - MA overlays
  - RSI sub-chart
  - MACD sub-chart
  - Bollinger Bands
  - Volume bars

- [ ] 12.2.4: Entry/Exit Markers
  - Show trade entry points
  - Show trade exit points
  - P&L labels
  - Trade duration

**Dosyalar:**
- `frontend/src/components/PriceChart.jsx` (YENİ)
- `frontend/src/components/IndicatorChart.jsx` (YENİ)
- `frontend/src/utils/chartHelpers.js` (YENİ)

**Dependencies:**
- `npm install lightweight-charts` veya `chart.js react-chartjs-2`

**API Endpoints:**
- ✅ `GET /api/data/historical/{symbol}` (YENİ - historical data for chart)

**Backend Değişiklik:**
- `backend/api/routes/data.py` (YENİ - data endpoints)
- Historical data caching

**Tahmini Süre:** 10-12 saat

---

## PHASE 13: Analytics & Reporting

### Task 13.1: Trade Analytics Dashboard ⭐ MEDIUM PRIORITY
**Açıklama:** Trade performans analizi ve raporlama

**Subtasks:**
- [ ] 13.1.1: Performance Metrics Cards
  - Total trades
  - Win rate
  - Profit factor
  - Average win/loss
  - Best/Worst trade
  - Sharpe ratio

- [ ] 13.1.2: P&L Charts
  - Equity curve (portfolio value over time)
  - P&L distribution histogram
  - Win/Loss ratio pie chart
  - Monthly P&L bar chart

- [ ] 13.1.3: Trade Statistics Table
  - Trade by symbol summary
  - Trade by strategy summary
  - Trade by time of day analysis
  - Trade duration statistics

- [ ] 13.1.4: Export & Reporting
  - Export trades to CSV/Excel
  - Generate PDF report
  - Email report functionality
  - Scheduled reports

**Dosyalar:**
- `frontend/src/components/Analytics.jsx` (YENİ)
- `frontend/src/components/EquityCurve.jsx` (YENİ)
- `frontend/src/components/PerformanceMetrics.jsx` (YENİ)
- `frontend/src/utils/reportGenerator.js` (YENİ)

**API Endpoints:**
- ❌ `GET /api/analytics/performance` (YENİ)
- ❌ `GET /api/analytics/equity-curve` (YENİ)
- ❌ `GET /api/analytics/trades-summary` (YENİ)
- ❌ `POST /api/analytics/export` (YENİ)

**Backend Değişiklik:**
- `backend/api/routes/analytics.py` (YENİ)
- Analytics calculation service
- Report generation (PDF library)

**Tahmini Süre:** 8-10 saat

---

### Task 13.2: Risk Dashboard ⭐ HIGH PRIORITY
**Açıklama:** Risk metrikleri görüntüleme ve yönetim

**Subtasks:**
- [ ] 13.2.1: Risk Metrics Display
  - Current drawdown
  - Max drawdown
  - Daily P&L
  - Position exposure
  - Portfolio concentration
  - VaR (Value at Risk)

- [ ] 13.2.2: Drawdown Chart
  - Drawdown over time
  - Max drawdown marker
  - Recovery periods
  - Underwater chart

- [ ] 13.2.3: Risk Parameter Editor
  - Edit max position size
  - Edit max drawdown limit
  - Edit daily loss limit
  - Edit total exposure limit
  - Apply/Save changes

- [ ] 13.2.4: Risk Alerts
  - Real-time risk warnings
  - Alert when approaching limits
  - Alert history
  - Alert settings

**Dosyalar:**
- `frontend/src/components/RiskDashboard.jsx` (YENİ)
- `frontend/src/components/DrawdownChart.jsx` (YENİ)
- `frontend/src/components/RiskAlerts.jsx` (YENİ)

**API Endpoints:**
- ❌ `GET /api/risk/metrics` (YENİ)
- ❌ `GET /api/risk/parameters` (YENİ)
- ❌ `PUT /api/risk/parameters` (YENİ)
- ❌ `GET /api/risk/alerts` (YENİ)

**Backend Değişiklik:**
- `backend/api/routes/risk.py` (YENİ)
- `backend/paper_trading/risk_manager.py` (GÜNCELLE - risk alerts)

**Tahmini Süre:** 7-9 saat

---

## PHASE 14: Backtest UI

### Task 14.1: Backtest Configuration UI ⭐ MEDIUM PRIORITY
**Açıklama:** Dashboard'dan backtest çalıştırma

**Subtasks:**
- [ ] 14.1.1: Backtest Form
  - Symbol selection
  - Date range picker
  - Strategy selector
  - Parameter configuration
  - Initial capital input
  - Commission/Slippage settings

- [ ] 14.1.2: Backtest Execution
  - Submit backtest
  - Progress indicator
  - Cancel backtest
  - Multiple backtest queue

- [ ] 14.1.3: Backtest Results Display
  - Performance metrics
  - Equity curve
  - Trade list
  - Drawdown chart
  - Monthly returns

- [ ] 14.1.4: Backtest History
  - Past backtests list
  - Backtest comparison
  - Save/Load backtest results
  - Share backtest link

**Dosyalar:**
- `frontend/src/components/BacktestForm.jsx` (YENİ)
- `frontend/src/components/BacktestResults.jsx` (YENİ)
- `frontend/src/components/BacktestHistory.jsx` (YENİ)

**API Endpoints:**
- ✅ `POST /api/backtest/run` (MEVCUT)
- ✅ `GET /api/backtest/status/{id}` (MEVCUT)
- ✅ `GET /api/backtest/result/{id}` (MEVCUT)
- ❌ `GET /api/backtest/history` (YENİ)

**Backend Değişiklik:**
- Backtest result storage
- Backtest history tracking

**Tahmini Süre:** 8-10 saat

---

## 📅 Öncelik Sıralaması ve Tahmini Toplam Süre

### 🔥 HIGH PRIORITY (PHASE 10 + 11.2 + 12.1 + 13.2)
1. **Task 10.1:** Order Placement UI - 4-6 saat
2. **Task 10.2:** Active Orders & Trade History - 5-7 saat
3. **Task 11.2:** Strategy Parameter Editor - 8-10 saat
4. **Task 12.1:** WebSocket Integration - 6-8 saat
5. **Task 13.2:** Risk Dashboard - 7-9 saat

**Toplam High Priority:** ~35-40 saat (1 hafta full-time)

---

### ⚡ MEDIUM PRIORITY (PHASE 11.1 + 11.3 + 12.2 + 13.1 + 14.1)
6. **Task 11.1:** Active Strategy Display - 6-8 saat
7. **Task 11.3:** Custom Strategy Upload - 12-15 saat
8. **Task 12.2:** Live Price Charts - 10-12 saat
9. **Task 13.1:** Trade Analytics Dashboard - 8-10 saat
10. **Task 14.1:** Backtest Configuration UI - 8-10 saat

**Toplam Medium Priority:** ~44-55 saat (1.5 hafta full-time)

---

### 📊 TOPLAM PROJE SÜRESİ
**High + Medium:** ~80-95 saat (2.5-3 hafta full-time)

---

## 🛠️ Teknoloji Stack Eklemeleri

### Frontend (Yeni Kütüphaneler)
```json
{
  "dependencies": {
    "lightweight-charts": "^4.0.0",  // Veya "chart.js" + "react-chartjs-2"
    "react-dropzone": "^14.0.0",     // File upload
    "date-fns": "^2.30.0",            // Date formatting
    "recharts": "^2.5.0",             // Analytics charts
    "react-toastify": "^9.1.0",       // Notifications
    "react-modal": "^3.16.0",         // Modals
    "react-select": "^5.7.0"          // Better select inputs
  }
}
```

### Backend (Yeni Dependencies)
```toml
[project]
dependencies = [
    "python-multipart",  # File upload
    "reportlab",         # PDF generation
    "openpyxl",          # Excel export
    "jinja2",            # Template rendering
    "celery",            # Background tasks (optional)
    "redis"              # Caching & WebSocket (optional)
]
```

---

## 🎯 Hızlı Başlangıç Önerisi

**İlk 1 hafta için önerilen task sırası:**

1. **Gün 1-2:** Task 10.1 - Order Placement UI (Dashboard'dan işlem yapmak)
2. **Gün 3:** Task 10.2 - Active Orders & Trade History (İşlem geçmişi)
3. **Gün 4-5:** Task 12.1 - WebSocket Integration (Canlı veri)
4. **Gün 6-7:** Task 11.2 - Strategy Parameter Editor (Strateji düzenleme)

Bu 1 haftalık çalışma sonunda kullanıcılar:
- ✅ Dashboard'dan order verebilir
- ✅ Canlı veri akışı görebilir
- ✅ İşlem geçmişini inceleyebilir
- ✅ Strateji parametrelerini değiştirebilir

---

## 📌 Notlar

- Tüm backend endpoints için authentication/authorization eklenebilir (JWT tokens)
- Database olarak SQLite yerine PostgreSQL kullanılabilir (production için)
- Rate limiting eklenebilir (API güvenliği için)
- Logging ve monitoring sistemi eklenebilir (Prometheus, Grafana)
- Unit test coverage artırılabilir (pytest)
- CI/CD pipeline kurulabilir (GitHub Actions)
