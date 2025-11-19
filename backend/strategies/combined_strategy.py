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

    def get_detailed_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Her mum için detaylı sinyal bilgilerini döndürür
        Hangi kuralların aktif olduğunu, korelasyonları gösterir
        """
        df = self.calculate_indicators(data).copy()

        # Bollinger Bands
        upper, mid, lower = self._calculate_bollinger_bands(
            df['close'],
            self.parameters['bollinger_period'],
            float(self.parameters['bollinger_std'])
        )
        df['bb_upper'] = upper
        df['bb_mid'] = mid
        df['bb_lower'] = lower

        # MACD
        macd_line, signal_line, hist = self._calculate_macd(
            df['close'],
            int(self.parameters['macd_fast']),
            int(self.parameters['macd_slow']),
            int(self.parameters['macd_signal'])
        )
        df['macd_line'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_hist'] = hist

        # Moving Averages
        ma_fast = df['ma_fast'] if 'ma_fast' in df else df['close'].rolling(self.parameters['ma_fast']).mean()
        ma_slow = df['ma_slow'] if 'ma_slow' in df else df['close'].rolling(self.parameters['ma_slow']).mean()
        df['ma_fast_val'] = ma_fast
        df['ma_slow_val'] = ma_slow

        # RSI
        rsi = df['rsi']

        # Buy Conditions
        df['buy_ma'] = (ma_fast > ma_slow)
        df['buy_rsi'] = (rsi < self.parameters['rsi_oversold'])
        df['buy_bb'] = (df['close'] < lower)
        df['buy_macd'] = (macd_line > signal_line)

        # Sell Conditions
        df['sell_ma'] = (ma_fast < ma_slow)
        df['sell_rsi'] = (rsi > self.parameters['rsi_overbought'])
        df['sell_bb'] = (df['close'] > upper)
        df['sell_macd'] = (macd_line < signal_line)

        # Final Signals
        df['entry_signal'] = (df['buy_ma'] & df['buy_macd'] & (df['buy_rsi'] | df['buy_bb'])).fillna(False)
        df['exit_signal'] = (df['sell_ma'] | df['sell_macd'] | df['sell_rsi'] | df['sell_bb']).fillna(False)

        # Signal Strength (0-1)
        df['buy_strength'] = (
            df['buy_ma'].astype(int) * 0.3 +
            df['buy_macd'].astype(int) * 0.3 +
            df['buy_rsi'].astype(int) * 0.2 +
            df['buy_bb'].astype(int) * 0.2
        )

        df['sell_strength'] = (
            df['sell_ma'].astype(int) * 0.25 +
            df['sell_macd'].astype(int) * 0.25 +
            df['sell_rsi'].astype(int) * 0.25 +
            df['sell_bb'].astype(int) * 0.25
        )

        # Rule explanations
        df['buy_rules'] = df.apply(lambda row: self._get_buy_rules(row), axis=1)
        df['sell_rules'] = df.apply(lambda row: self._get_sell_rules(row), axis=1)

        return df

    def _get_buy_rules(self, row) -> str:
        """Her mum için aktif olan alım kurallarını döndürür"""
        rules = []
        if row.get('buy_ma', False):
            rules.append(f"MA Cross (Fast:{row.get('ma_fast_val', 0):.2f} > Slow:{row.get('ma_slow_val', 0):.2f})")
        if row.get('buy_macd', False):
            rules.append(f"MACD Bullish (Line:{row.get('macd_line', 0):.2f} > Signal:{row.get('macd_signal', 0):.2f})")
        if row.get('buy_rsi', False):
            rules.append(f"RSI Oversold ({row.get('rsi', 0):.1f} < {self.parameters['rsi_oversold']})")
        if row.get('buy_bb', False):
            rules.append(f"Price Below BB (Close:{row.get('close', 0):.2f} < Lower:{row.get('bb_lower', 0):.2f})")
        return " | ".join(rules) if rules else "No Buy Signal"

    def _get_sell_rules(self, row) -> str:
        """Her mum için aktif olan satım kurallarını döndürür"""
        rules = []
        if row.get('sell_ma', False):
            rules.append(f"MA Cross (Fast:{row.get('ma_fast_val', 0):.2f} < Slow:{row.get('ma_slow_val', 0):.2f})")
        if row.get('sell_macd', False):
            rules.append(f"MACD Bearish (Line:{row.get('macd_line', 0):.2f} < Signal:{row.get('macd_signal', 0):.2f})")
        if row.get('sell_rsi', False):
            rules.append(f"RSI Overbought ({row.get('rsi', 0):.1f} > {self.parameters['rsi_overbought']})")
        if row.get('sell_bb', False):
            rules.append(f"Price Above BB (Close:{row.get('close', 0):.2f} > Upper:{row.get('bb_upper', 0):.2f})")
        return " | ".join(rules) if rules else "No Sell Signal"