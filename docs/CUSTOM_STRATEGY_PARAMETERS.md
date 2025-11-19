# Kendi Parametrelerinizi Combined Strategy'ye Entegre Etme

Bu doküman, kendi trading parametrelerinizi Combined Strategy'ye nasıl entegre edeceğinizi açıklar.

## İçindekiler
1. [Combined Strategy Parametreleri](#combined-strategy-parametreleri)
2. [Parametreleri Değiştirme Yöntemleri](#parametreleri-değiştirme-yöntemleri)
3. [API Üzerinden Parametre Gönderme](#api-üzerinden-parametre-gönderme)
4. [Auto-Trading Parametrelerini Ayarlama](#auto-trading-parametrelerini-ayarlama)

---

## Combined Strategy Parametreleri

Combined Strategy aşağıdaki parametreleri kullanır:

### Moving Average (MA) Parametreleri
- **ma_fast**: Hızlı MA periyodu (default: 10)
- **ma_slow**: Yavaş MA periyodu (default: 30)

### RSI Parametreleri
- **rsi_period**: RSI hesaplama periyodu (default: 14)
- **rsi_oversold**: Aşırı satım seviyesi (default: 30)
- **rsi_overbought**: Aşırı alım seviyesi (default: 70)

### Bollinger Bands Parametreleri
- **bollinger_period**: Bollinger Bands periyodu (default: 20)
- **bollinger_std**: Standart sapma çarpanı (default: 2.0)

### MACD Parametreleri
- **macd_fast**: MACD hızlı EMA (default: 12)
- **macd_slow**: MACD yavaş EMA (default: 26)
- **macd_signal**: MACD sinyal hattı (default: 9)

### Risk Yönetimi
- **stop_loss_pct**: Stop loss yüzdesi (default: 2.0)
- **take_profit_pct**: Take profit yüzdesi (default: 5.0)

---

## Parametreleri Değiştirme Yöntemleri

### Yöntem 1: Backend Kodunda Doğrudan Değiştirme

En basit yöntem, `backend/api/routes/market_data.py` dosyasındaki parametreleri düzenlemektir:

```python
# backend/api/routes/market_data.py dosyasında

params = {
    'ma_fast': 20,           # Değiştir: Hızlı MA'yı 20'ye çıkar
    'ma_slow': 50,           # Değiştir: Yavaş MA'yı 50'ye çıkar
    'rsi_period': 14,
    'rsi_oversold': 35,      # Değiştir: Daha az hassas
    'rsi_overbought': 65,    # Değiştir: Daha az hassas
    'bollinger_period': 20,
    'bollinger_std': 2.5,    # Değiştir: Daha geniş bantlar
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'stop_loss_pct': 3.0,    # Değiştir: %3 stop loss
    'take_profit_pct': 10.0  # Değiştir: %10 take profit
}
strategy = CombinedStrategy(params)
```

**Değişikliği Uygulamak İçin**:
```bash
# Backend'i restart et
docker-compose restart backend

# Veya rebuild et (kod değişikliği kesin yüklensin)
docker-compose build backend && docker-compose up -d backend
```

### Yöntem 2: Environment Variables ile

`.env` dosyasında parametreleri tanımlayabilirsiniz:

```env
# .env dosyasına ekle
STRATEGY_MA_FAST=15
STRATEGY_MA_SLOW=40
STRATEGY_RSI_OVERSOLD=35
STRATEGY_RSI_OVERBOUGHT=65
STRATEGY_STOP_LOSS=3.0
STRATEGY_TAKE_PROFIT=8.0
```

Sonra `backend/api/routes/market_data.py` dosyasını şöyle güncelleyin:

```python
import os

params = {
    'ma_fast': int(os.getenv('STRATEGY_MA_FAST', '10')),
    'ma_slow': int(os.getenv('STRATEGY_MA_SLOW', '30')),
    'rsi_period': int(os.getenv('STRATEGY_RSI_PERIOD', '14')),
    'rsi_oversold': float(os.getenv('STRATEGY_RSI_OVERSOLD', '30')),
    'rsi_overbought': float(os.getenv('STRATEGY_RSI_OVERBOUGHT', '70')),
    'bollinger_period': int(os.getenv('STRATEGY_BOLLINGER_PERIOD', '20')),
    'bollinger_std': float(os.getenv('STRATEGY_BOLLINGER_STD', '2.0')),
    'macd_fast': int(os.getenv('STRATEGY_MACD_FAST', '12')),
    'macd_slow': int(os.getenv('STRATEGY_MACD_SLOW', '26')),
    'macd_signal': int(os.getenv('STRATEGY_MACD_SIGNAL', '9')),
    'stop_loss_pct': float(os.getenv('STRATEGY_STOP_LOSS', '2.0')),
    'take_profit_pct': float(os.getenv('STRATEGY_TAKE_PROFIT', '5.0'))
}
```

### Yöntem 3: ParameterDefinitions Kullanma

`backend/strategies/parameters.py` dosyasını düzenleyerek merkezi bir parametre yönetimi yapabilirsiniz:

```python
# backend/strategies/parameters.py

class ParameterDefinitions:

    @staticmethod
    def get_combined_strategy_parameters() -> Dict[str, Any]:
        """Combined Strategy için özel parametreler"""
        return {
            'ma_fast': 10,
            'ma_slow': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bollinger_period': 20,
            'bollinger_std': 2.0,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 5.0
        }
```

Sonra `market_data.py` dosyasında:

```python
from strategies.parameters import ParameterDefinitions

params = ParameterDefinitions.get_combined_strategy_parameters()
strategy = CombinedStrategy(params)
```

---

## API Üzerinden Parametre Gönderme

### Yeni Endpoint Ekle

`backend/api/routes/market_data.py` dosyasına yeni endpoint ekleyin:

```python
from fastapi import Query
from typing import Optional

@router.get("/position-analysis-custom/{symbol}")
async def get_position_analysis_custom(
    symbol: str,
    lookback_candles: int = 100,
    # Custom parameters
    ma_fast: Optional[int] = Query(10, description="Fast MA period"),
    ma_slow: Optional[int] = Query(30, description="Slow MA period"),
    rsi_oversold: Optional[float] = Query(30.0, description="RSI oversold level"),
    rsi_overbought: Optional[float] = Query(70.0, description="RSI overbought level")
):
    """Özel parametrelerle pozisyon analizi"""

    # Custom parameters kullan
    params = {
        'ma_fast': ma_fast,
        'ma_slow': ma_slow,
        'rsi_period': 14,
        'rsi_oversold': rsi_oversold,
        'rsi_overbought': rsi_overbought,
        'bollinger_period': 20,
        'bollinger_std': 2.0,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'stop_loss_pct': 2.0,
        'take_profit_pct': 5.0
    }

    strategy = CombinedStrategy(params)
    # ... rest of the analysis logic
```

**Kullanım**:
```bash
curl "http://localhost:85/api/market/position-analysis-custom/THYAO.IS?ma_fast=15&ma_slow=45&rsi_oversold=35&rsi_overbought=65"
```

---

## Auto-Trading Parametrelerini Ayarlama

Auto-trading başlatırken parametreleri gönderebilmek için `backend/api/routes/auto_trading.py` dosyasını güncelleyin:

### 1. StartRequest Modelini Güncelle

```python
class StartRequest(BaseModel):
    symbols: Optional[List[str]] = None
    strategy: str = "combined"

    # Strategy parametreleri ekle
    ma_fast: Optional[int] = 10
    ma_slow: Optional[int] = 30
    rsi_oversold: Optional[float] = 30.0
    rsi_overbought: Optional[float] = 70.0
    stop_loss_pct: Optional[float] = 2.0
    take_profit_pct: Optional[float] = 5.0
```

### 2. Start Endpoint'ini Güncelle

```python
@router.post("/start")
async def start_auto_trading(request: StartRequest):
    """Start auto-trading with custom parameters"""

    # Parameters oluştur
    params = {
        'ma_fast': request.ma_fast,
        'ma_slow': request.ma_slow,
        'rsi_period': 14,
        'rsi_oversold': request.rsi_oversold,
        'rsi_overbought': request.rsi_overbought,
        'bollinger_period': 20,
        'bollinger_std': 2.0,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'stop_loss_pct': request.stop_loss_pct,
        'take_profit_pct': request.take_profit_pct
    }

    # Strategy'yi parametrelerle başlat
    strategy = CombinedStrategy(params)
    # ... auto-trading başlatma kodu
```

### 3. Frontend'den Kullanım

```javascript
// Frontend: AutoTradingControl.jsx

const startAutoTrading = async () => {
  const response = await fetch('/api/auto-trading/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbols: ['THYAO.IS', 'GARAN.IS'],
      strategy: 'combined',
      ma_fast: 15,
      ma_slow: 45,
      rsi_oversold: 35,
      rsi_overbought: 65,
      stop_loss_pct: 3.0,
      take_profit_pct: 10.0
    })
  });
};
```

---

## Örnek Kullanım Senaryoları

### Senaryo 1: Daha Konservatif Strateji

```python
params = {
    'ma_fast': 20,          # Daha uzun MA = daha az sinyal
    'ma_slow': 50,          # Daha uzun MA = daha az sinyal
    'rsi_period': 14,
    'rsi_oversold': 25,     # Daha düşük = daha az alım sinyali
    'rsi_overbought': 75,   # Daha yüksek = daha az satım sinyali
    'bollinger_period': 20,
    'bollinger_std': 2.5,   # Daha geniş bantlar = daha az sinyal
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'stop_loss_pct': 1.5,   # Daha sıkı stop loss
    'take_profit_pct': 15.0 # Daha gevşek take profit
}
```

### Senaryo 2: Daha Agresif Strateji

```python
params = {
    'ma_fast': 5,           # Daha kısa MA = daha çok sinyal
    'ma_slow': 15,          # Daha kısa MA = daha çok sinyal
    'rsi_period': 7,        # Daha kısa RSI = daha hassas
    'rsi_oversold': 35,     # Daha yüksek = daha çok alım sinyali
    'rsi_overbought': 65,   # Daha düşük = daha çok satım sinyali
    'bollinger_period': 10,
    'bollinger_std': 1.5,   # Daha dar bantlar = daha çok sinyal
    'macd_fast': 8,
    'macd_slow': 17,
    'macd_signal': 9,
    'stop_loss_pct': 3.0,   # Daha gevşek stop loss
    'take_profit_pct': 5.0  # Daha sıkı take profit
}
```

### Senaryo 3: Scalping (Kısa Vadeli)

```python
params = {
    'ma_fast': 3,
    'ma_slow': 8,
    'rsi_period': 5,
    'rsi_oversold': 40,
    'rsi_overbought': 60,
    'bollinger_period': 10,
    'bollinger_std': 1.5,
    'macd_fast': 5,
    'macd_slow': 13,
    'macd_signal': 5,
    'stop_loss_pct': 0.5,   # Çok sıkı stop loss
    'take_profit_pct': 1.0  # Çok sıkı take profit
}
```

---

## Test ve Optimizasyon

### Parametreleri Test Etme

```python
# backend/test_strategy_params.py

from strategies.combined_strategy import CombinedStrategy
from data.yahoo_finance_collector import YahooFinanceCollector
import pandas as pd

# Farklı parametre setlerini test et
param_sets = [
    {'ma_fast': 10, 'ma_slow': 30, 'name': 'Default'},
    {'ma_fast': 15, 'ma_slow': 45, 'name': 'Conservative'},
    {'ma_fast': 5, 'ma_slow': 15, 'name': 'Aggressive'},
]

collector = YahooFinanceCollector()
data = collector.get_ohlcv('THYAO.IS', '1d', '1y')

for param_set in param_sets:
    params = {
        'ma_fast': param_set['ma_fast'],
        'ma_slow': param_set['ma_slow'],
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'bollinger_period': 20,
        'bollinger_std': 2.0,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'stop_loss_pct': 2.0,
        'take_profit_pct': 5.0
    }

    strategy = CombinedStrategy(params)
    signals = strategy.generate_signals(data)

    print(f"\n{param_set['name']} Strategy:")
    print(f"  Buy Signals: {signals.entry}")
    print(f"  Sell Signals: {signals.exit}")
```

### VectorBT ile Optimizasyon

```python
# backend/optimization/optimize_custom_params.py

from optimization.vectorbt_optimizer import VectorBTOptimizer
import vectorbt as vbt

optimizer = VectorBTOptimizer()

# Parametre aralıklarını tanımla
ma_fast_range = range(5, 20, 5)     # [5, 10, 15]
ma_slow_range = range(20, 60, 10)   # [20, 30, 40, 50]
rsi_oversold_range = [25, 30, 35]
rsi_overbought_range = [65, 70, 75]

# En iyi parametreleri bul
results = optimizer.optimize_combined_strategy(
    symbol='THYAO.IS',
    ma_fast_range=ma_fast_range,
    ma_slow_range=ma_slow_range,
    rsi_oversold_range=rsi_oversold_range,
    rsi_overbought_range=rsi_overbought_range,
    top_n=5
)

print("En İyi 5 Parametre Seti:")
for i, result in enumerate(results, 1):
    print(f"\n{i}. Set:")
    print(f"   MA Fast: {result['ma_fast']}, MA Slow: {result['ma_slow']}")
    print(f"   RSI Oversold: {result['rsi_oversold']}, RSI Overbought: {result['rsi_overbought']}")
    print(f"   Total Return: {result['total_return']:.2%}")
    print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
```

---

## Notlar ve İpuçları

1. **Overfitting'den Kaçının**: Parametreleri geçmiş verilere çok fazla uydurursanız, gelecekte kötü performans gösterebilir.

2. **Backtesting Yapın**: Parametrelerişi değiştirdikten sonra mutlaka backtest yapın.

3. **Forward Testing**: Canlı trading yapmadan önce paper trading ile test edin.

4. **Parametre Sınırları**: Çok aşırı değerler kullanmayın (örn: ma_fast=1, ma_slow=100).

5. **Market Koşulları**: Trending marketlerde uzun MA'lar, ranging marketlerde kısa MA'lar daha iyi çalışır.

6. **Risk Yönetimi**: Stop loss ve take profit değerlerini piyasa volatilitesine göre ayarlayın.

7. **Kayıt Tutun**: Hangi parametrelerin hangi koşullarda çalıştığını not edin.

---

## Sorun Giderme

### Hata: "KeyError: 'bollinger_period'"

Eğer bu hatayı alıyorsanız, CombinedStrategy'ye gönderilen parametrelerde eksiklik var demektir.

**Çözüm**: Tüm gerekli parametrelerin gönderildiğinden emin olun:
```python
required_params = [
    'ma_fast', 'ma_slow',
    'rsi_period', 'rsi_oversold', 'rsi_overbought',
    'bollinger_period', 'bollinger_std',
    'macd_fast', 'macd_slow', 'macd_signal',
    'stop_loss_pct', 'take_profit_pct'
]
```

### Pozisyonlar Hemen Kapanıyor

Auto-trading açıkken stratejiniz çok sık exit sinyali üretiyor olabilir.

**Çözümler**:
1. Auto-trading'i kapatın: `curl -X POST http://localhost:85/api/auto-trading/stop`
2. Exit kriterlerini gevşetin (örn: RSI overbought seviyesini 70'ten 75'e çıkarın)
3. Take profit seviyesini artırın (örn: %5'ten %10'a)

### Çok Az Sinyal Üretiyor

Parametreleriniz çok konservatif olabilir.

**Çözümler**:
1. MA periyotlarını kısaltın
2. RSI seviyelerini daraltın (örn: 30-70 yerine 35-65)
3. Bollinger Bands genişliğini azaltın (std: 2.0'dan 1.5'e)

---

## Kaynaklar

- [Technical Analysis Library Documentation](https://technical-analysis-library-in-python.readthedocs.io/)
- [VectorBT Documentation](https://vectorbt.dev/)
- [Trading Strategy Best Practices](https://www.investopedia.com/trading-strategies-4689645)

---

**Son Güncelleme**: 2025-11-19
**Versiyon**: 1.0.0
