# Trading Bot - Sorun Giderme Kılavuzu

**Son Güncelleme**: 2025-11-19

## İçindekiler
1. [OHLCV API Boş Dönüyor](#ohlcv-api-boş-dönüyor)
2. [Frontend'de Mumlar Gelmiyor](#frontendde-mumlar-gelmiyor)
3. [Pozisyonlar Hemen Kapanıyor](#pozisyonlar-hemen-kapanıyor)
4. [Backend Kod Değişiklikleri Yüklenmiyor](#backend-kod-değişiklikleri-yüklenmiyor)
5. [502 Bad Gateway Hataları](#502-bad-gateway-hataları)

---

## OHLCV API Boş Dönüyor

### Semptomlar
```bash
curl "http://localhost:85/api/market/ohlcv?symbol=THYAO.IS&interval=1m&period=7d"
# Sonuç: []
```

Frontend'de chart boş görünüyor.

### Olası Sebepler ve Çözümler

#### 1. Backend Kod Değişiklikleri Yüklenmemiş

**Kontrol Et**:
```bash
docker logs trading_bot-backend-1 2>&1 | grep "Error fetching OHLCV"
```

Eğer error log'u görmüyorsan, exception handling kodun yüklenmemiş demektir.

**Çözüm - Backend'i Rebuild Et**:
```bash
# Stop all services
docker-compose down

# Rebuild backend
docker-compose build backend

# Start all services
docker-compose up -d

# Wait for backend to be ready (60 seconds)
sleep 60

# Test
curl "http://localhost:85/api/market/ohlcv?symbol=THYAO.IS&interval=1d&period=30d"
```

#### 2. YahooFinanceCollector Çalışmıyor

**Test Et**:
```bash
docker exec trading_bot-backend-1 python -c "
import sys
sys.path.insert(0, '/app')
from data.yahoo_finance_collector import YahooFinanceCollector

collector = YahooFinanceCollector()
df = collector.fetch_historical_data('THYAO.IS', period='30d', interval='1d', use_cache=False)
print(f'Data shape: {df.shape if df is not None else None}')
"
```

**Beklenen Çıktı**:
```
Data shape: (30, 5)
```

Eğer `None` veya error geliyorsa:
- Internet bağlantısını kontrol et
- Yahoo Finance API limitlerine takılmış olabilirsin (1 saat bekle)
- Symbol adını kontrol et (THYAO.IS doğru mu?)

#### 3. Cache Sorunu

**Cache'i Temizle**:
```bash
docker exec trading_bot-backend-1 rm -rf /tmp/yfinance_cache/*
```

#### 4. Interval Kısıtlamaları

Yahoo Finance bazı interval'lar için period kısıtlamaları koyar:

| Interval | Max Period |
|----------|-----------|
| 1m       | 7d        |
| 5m       | 60d       |
| 15m      | 60d       |
| 1h       | 2y        |
| 1d       | unlimited |

**Yanlış**:
```bash
curl "http://localhost:85/api/market/ohlcv?symbol=THYAO.IS&interval=1m&period=30d"
# Period çok uzun, otomatik olarak 7d'ye düşürülür
```

**Doğru**:
```bash
curl "http://localhost:85/api/market/ohlcv?symbol=THYAO.IS&interval=1m&period=7d"
```

---

## Frontend'de Mumlar Gelmiyor

### Semptomlar
- Trade markers API'de data var
- Ama chart'ta mumlar görünmüyor
- Console'da error yok

### Çözüm Adımları

#### 1. OHLCV API'yi Kontrol Et

Browser DevTools -> Network tab:
```
Request: http://localhost:85/api/market/ohlcv?symbol=THYAO.IS&interval=1m&period=7d
Response: [] veya [...data...]
```

Eğer `[]` boş dönüyorsa, yukarıdaki "OHLCV API Boş Dönüyor" bölümüne git.

#### 2. Frontend Console Hatalarını Kontrol Et

Browser Console (F12):
```javascript
// Şu tarz hatalar olabilir:
Cannot read property 'map' of undefined
Uncaught TypeError: data is null
```

**Çözüm**: Frontend'i rebuild et
```bash
cd frontend
npm install
npm run build
```

#### 3. ChartPanel Component'i Kontrol Et

`frontend/src/components/ChartPanel.jsx` dosyasında:
```javascript
const safePeriod = (interval === '1m') ? '7d' :
                   (interval === '5m' || interval === '15m') ? '60d' :
                   period;
```

Bu kod interval'a göre otomatik period ayarı yapıyor.

#### 4. API Response Format'ını Kontrol Et

OHLCV endpoint şu formatta dönmeli:
```json
[
  {
    "t": "2025-11-19T10:00:00",
    "o": 267.5,
    "h": 268.0,
    "l": 267.0,
    "c": 267.75,
    "v": 1000000
  }
]
```

Eğer farklı format dönüyorsa, `backend/api/routes/market_data.py:53-62` satırlarını kontrol et.

---

## Pozisyonlar Hemen Kapanıyor

### Semptomlar
```bash
curl "http://localhost:85/api/paper-trading/trades?symbol=THYAO.IS"
# Sonuç:
[
  {
    "opened_at": "2025-11-19T07:28:29",
    "closed_at": "2025-11-19T07:28:40",  # 11 saniye sonra kapanmış!
    ...
  }
]
```

### Sebep

Auto-trading her `update_interval` saniyede strategy'yi çalıştırıyor ve exit sinyali bulunca satıyor.

**Mevcut Ayar**:
```python
# backend/api/routes/auto_trading.py:15
update_interval: int = 10  # Her 10 saniyede check ediyor!
```

### Çözümler

#### Çözüm 1: Update Interval'ı Artır

`backend/api/routes/auto_trading.py` dosyasında:
```python
class StrategyConfig(BaseModel):
    strategy: str = "combined"
    symbols: Optional[List[str]] = None
    update_interval: int = 300  # 5 dakika (önerilen)
    market: str = "turkish"
```

**Değişiklikten sonra**:
```bash
docker-compose restart backend
```

#### Çözüm 2: Auto-Trading'i Durdur

Manuel test yaparken auto-trading'i kapat:
```bash
# Auto-trading'i durdur
curl -X POST http://localhost:85/api/auto-trading/stop

# Pozisyon aç
curl -X POST http://localhost:85/api/paper-trading/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"THYAO.IS","side":"buy","quantity":5,"order_type":"market"}'

# Artık pozisyon kapanmayacak!
```

#### Çözüm 3: Minimum Holding Period Ekle

`backend/paper_trading/strategy_runner.py` dosyasına minimum holding period ekle:

```python
class StrategyRunner:
    def __init__(self, ..., min_holding_seconds: int = 300):
        self.min_holding_seconds = min_holding_seconds

    async def _check_exit_conditions(self, position):
        # Pozisyon minimum tutma süresinden önce satılmasın
        holding_time = (datetime.now() - position.opened_at).total_seconds()
        if holding_time < self.min_holding_seconds:
            return False  # Henüz satma

        # Normal exit logic...
```

#### Çözüm 4: Exit Kriterlerini Gevşet

Custom parametrelerle exit kriterlerini daha az hassas yap:

```python
params = {
    'ma_fast': 10,
    'ma_slow': 30,
    'rsi_period': 14,
    'rsi_oversold': 25,      # Daha düşük
    'rsi_overbought': 75,    # Daha yüksek (75'in üstünde sat)
    'bollinger_period': 20,
    'bollinger_std': 2.5,    # Daha geniş bantlar
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'stop_loss_pct': 3.0,    # Daha gevşek stop loss
    'take_profit_pct': 15.0  # Daha yüksek take profit
}
```

---

## Backend Kod Değişiklikleri Yüklenmiyor

### Semptomlar
- Backend'de kod değişikliği yaptın
- `docker-compose restart backend` çalıştırdın
- Ama değişiklik yansımadı

### Sebep

Docker volume mount cache sorunu veya kod henüz yeniden yüklenmemiş.

### Çözüm

**Her zaman build et ve yeniden başlat**:
```bash
# 1. Stop
docker-compose down

# 2. Rebuild
docker-compose build backend

# 3. Start
docker-compose up -d

# 4. Bekle (backend'in başlaması için)
sleep 60

# 5. Test
curl http://localhost:85/api/auto-trading/status
```

**Alternatif - Force Rebuild**:
```bash
docker-compose build --no-cache backend
docker-compose up -d backend
```

**Kontrol Et**:
```bash
# Backend log'larını kontrol et
docker logs trading_bot-backend-1 --tail 50

# "Application startup complete" mesajını ara
docker logs trading_bot-backend-1 2>&1 | grep "startup complete"
```

---

## 502 Bad Gateway Hataları

### Semptomlar
```bash
curl http://localhost:85/api/auto-trading/status
# <html><title>502 Bad Gateway</title></html>
```

### Olası Sebepler

#### 1. Backend Henüz Başlamadı

**Kontrol Et**:
```bash
docker logs trading_bot-backend-1 2>&1 | grep "Uvicorn running"
```

**Çözüm**: Bekle (30-60 saniye), sonra tekrar dene.

#### 2. Backend Crash Oldu

**Kontrol Et**:
```bash
docker ps --filter name=backend
# STATUS: Up X minutes (iyi)
# STATUS: Restarting (kötü - sürekli crash oluyor)
```

**Log'ları İncele**:
```bash
docker logs trading_bot-backend-1 --tail 100
```

**Yaygın Hatalar**:
- `ModuleNotFoundError`: requirements.txt'i kontrol et
- `NameError`: Import eksik
- `SyntaxError`: Kod hatası var

#### 3. Port Çakışması

**Kontrol Et**:
```bash
# Port 8000'i kim kullanıyor?
netstat -ano | findstr :8000

# Windows'ta:
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
```

**Çözüm**: Çakışan process'i kapat veya docker-compose.yml'de portu değiştir.

#### 4. Nginx Konfigürasyon Hatası

**Kontrol Et**:
```bash
docker exec trading_bot-nginx-1 nginx -t
```

**Nginx Log'larını İncele**:
```bash
docker logs trading_bot-nginx-1 --tail 50
```

---

## Hızlı Sorun Giderme Checklist

Backend çalışmıyorsa sırayla:

```bash
# 1. Container'ları kontrol et
docker-compose ps

# 2. Backend log'larını kontrol et
docker logs trading_bot-backend-1 --tail 100

# 3. Backend'in başladığını kontrol et
docker logs trading_bot-backend-1 2>&1 | grep "startup complete"

# 4. Test endpoint
curl http://localhost:85/api/auto-trading/status

# 5. Hala çalışmıyorsa: full restart
docker-compose down
docker-compose build backend
docker-compose up -d
sleep 60
curl http://localhost:85/api/auto-trading/status
```

---

## Debug Mode

Daha fazla log görmek için:

`backend/api/main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Environment variable ile:
```bash
# .env dosyasına ekle
LOG_LEVEL=DEBUG
```

```bash
# Geçici olarak
docker-compose up backend  # -d olmadan, direkt log'ları göreceksin
```

---

## Yaygın Hatalar ve Hızlı Çözümler

| Hata | Çözüm |
|------|-------|
| `[]` boş OHLCV | Backend rebuild et |
| Pozisyonlar hemen kapanıyor | Auto-trading'i durdur veya `update_interval=300` yap |
| 502 Bad Gateway | 60 saniye bekle veya `docker-compose restart backend` |
| Frontend'de chart yok | Backend OHLCV API'sini kontrol et |
| Code değişikliği yansımadı | `docker-compose build backend` çalıştır |
| `ModuleNotFoundError` | `docker-compose build --no-cache backend` |

---

## Log Dosyaları

Sistem şu dosyalara log yazıyor:

```
backend/logs/
├── trades.log        # Trade işlemleri
├── api_requests.log  # API istekleri
├── orders.log        # Order işlemleri
└── positions.log     # Pozisyon değişiklikleri
```

**İncele**:
```bash
docker exec trading_bot-backend-1 tail -f /app/logs/trades.log
docker exec trading_bot-backend-1 tail -f /app/logs/api_requests.log
```

---

## Performans Sorunları

### API Yavaş Yanıt Veriyor

**Kontrol Et**:
```bash
# Backend log'larında response time'ları kontrol et
docker logs trading_bot-backend-1 2>&1 | grep "completed in"

# Örnek:
# INFO:api.main:GET /api/market/ohlcv completed in 1.627s
```

**Çözümler**:
1. Cache kullan (zaten aktif olmalı)
2. Data period'unu kısalt (500d yerine 60d)
3. Interval'ı büyüt (1m yerine 1h)

### Docker Container CPU/Memory Kullanımı

**Kontrol Et**:
```bash
docker stats trading_bot-backend-1
```

**Limit Koy** (`docker-compose.yml`):
```yaml
services:
  backend:
    ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

---

## Yardım Al

Eğer sorun çözülmezse:

1. **Log'ları Topla**:
```bash
docker logs trading_bot-backend-1 > backend.log 2>&1
docker logs trading_bot-nginx-1 > nginx.log 2>&1
docker logs trading_bot-frontend-1 > frontend.log 2>&1
```

2. **Sistem Bilgilerini Topla**:
```bash
docker-compose ps > docker_status.txt
docker --version >> docker_status.txt
```

3. **İssue Aç**: GitHub'da detaylı açıklama ile issue aç

---

**Son Not**: Herhangi bir kod değişikliğinden sonra **mutlaka** `docker-compose build` çalıştır!

```bash
# Altın Kural:
docker-compose build backend && docker-compose up -d backend
```
