import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal

class CombinedStrategy(BaseStrategy):
    def __init__(self, parameters: dict):
        super().__init__(parameters)

    def get_required_parameters(self) -> list:
        return [
            'ma_fast','ma_slow',
            'rsi_period','rsi_oversold','rsi_overbought',
            'bollinger_period','bollinger_std',
            'macd_fast','macd_slow','macd_signal',
            'stop_loss_pct','take_profit_pct'
        ]

    def generate_signals(self, data: pd.DataFrame) -> Signal:
        df = self.calculate_indicators(data)

        upper, mid, lower = self._calculate_bollinger_bands(
            df['close'],
            self.parameters['bollinger_period'],
            float(self.parameters['bollinger_std'])
        )
        macd_line, signal_line, hist = self._calculate_macd(
            df['close'],
            int(self.parameters['macd_fast']),
            int(self.parameters['macd_slow']),
            int(self.parameters['macd_signal'])
        )

        ma_fast = df['ma_fast'] if 'ma_fast' in df else df['close'].rolling(self.parameters['ma_fast']).mean()
        ma_slow = df['ma_slow'] if 'ma_slow' in df else df['close'].rolling(self.parameters['ma_slow']).mean()

        rsi = df['rsi']

        buy_cond_ma = (ma_fast > ma_slow)
        buy_cond_rsi = (rsi < self.parameters['rsi_oversold'])
        buy_cond_bb = (df['close'] < lower)
        buy_cond_macd = (macd_line > signal_line)

        sell_cond_ma = (ma_fast < ma_slow)
        sell_cond_rsi = (rsi > self.parameters['rsi_overbought'])
        sell_cond_bb = (df['close'] > upper)
        sell_cond_macd = (macd_line < signal_line)

        entries = (buy_cond_ma & buy_cond_macd & (buy_cond_rsi | buy_cond_bb)).fillna(False)
        exits = (sell_cond_ma | sell_cond_macd | sell_cond_rsi | sell_cond_bb).fillna(False)

        return Signal(entries=entries, exits=exits)