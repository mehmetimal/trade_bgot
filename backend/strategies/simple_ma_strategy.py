"""
Simple Moving Average Crossover Strategy
Buy when fast MA crosses above slow MA
Sell when fast MA crosses below slow MA
"""
import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal


class SimpleMAStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy

    Required Parameters:
        - ma_fast: Fast MA period (e.g., 10)
        - ma_slow: Slow MA period (e.g., 30)
        - stop_loss_pct: Stop loss percentage (e.g., 0.02 for 2%)
        - take_profit_pct: Take profit percentage (e.g., 0.04 for 4%)
    """

    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.validate_parameters()

    def get_required_parameters(self) -> list:
        """Required parameters for this strategy"""
        return ['ma_fast', 'ma_slow', 'stop_loss_pct', 'take_profit_pct']

    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate MA crossover signals

        Entry: Fast MA crosses above Slow MA (golden cross)
        Exit: Fast MA crosses below Slow MA (death cross)
        """
        # Calculate indicators
        df = self.calculate_indicators(data)

        # Initialize signals
        entries = pd.Series(False, index=df.index)
        exits = pd.Series(False, index=df.index)

        # Generate crossover signals
        # Golden Cross: Fast MA crosses above Slow MA
        fast_above_slow = (df['ma_fast'] > df['ma_slow']).fillna(False)
        fast_above_slow_prev = fast_above_slow.shift(1).fillna(False)

        # Entry: Crossover from below to above
        entries = (~fast_above_slow_prev) & fast_above_slow

        # Exit: Crossover from above to below
        exits = fast_above_slow_prev & (~fast_above_slow)

        return Signal(entries=entries, exits=exits)

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MA indicators"""
        df = super().calculate_indicators(data)

        # Ensure MAs are calculated
        if 'ma_fast' not in df.columns:
            df['ma_fast'] = df['close'].rolling(
                window=self.parameters['ma_fast']
            ).mean()

        if 'ma_slow' not in df.columns:
            df['ma_slow'] = df['close'].rolling(
                window=self.parameters['ma_slow']
            ).mean()

        return df


# Alternative: RSI + MA Strategy
class RSIMAStrategy(BaseStrategy):
    """
    RSI + Moving Average Strategy

    Entry: RSI oversold AND price above MA
    Exit: RSI overbought OR price below MA
    """

    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.validate_parameters()

    def get_required_parameters(self) -> list:
        return [
            'ma_slow', 'rsi_period', 'rsi_oversold',
            'rsi_overbought', 'stop_loss_pct', 'take_profit_pct'
        ]

    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """Generate RSI + MA signals"""
        df = self.calculate_indicators(data)

        # Entry: RSI oversold AND price above MA
        entries = (
            (df['rsi'] < self.parameters['rsi_oversold']) &
            (df['close'] > df['ma_slow'])
        )

        # Exit: RSI overbought OR price below MA
        exits = (
            (df['rsi'] > self.parameters['rsi_overbought']) |
            (df['close'] < df['ma_slow'])
        )

        return Signal(entries=entries, exits=exits)


if __name__ == "__main__":
    # Test strategy
    print("="*60)
    print("SIMPLE MA STRATEGY TEST")
    print("="*60)

    # Create strategy
    strategy = SimpleMAStrategy(parameters={
        'ma_fast': 10,
        'ma_slow': 30,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04
    })

    print(f"\nStrategy: {strategy.name}")
    print(f"Parameters: {strategy.parameters}")
    print(f"Required params: {strategy.get_required_parameters()}")
    print("="*60)
