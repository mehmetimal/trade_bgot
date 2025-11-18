"""
Base Strategy Class
Abstract base class for all trading strategies
"""
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Signal:
    """Trading signal"""
    entries: pd.Series  # Boolean series for entry signals
    exits: pd.Series    # Boolean series for exit signals
    positions: Optional[pd.Series] = None  # Position sizes (optional)


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies

    All strategies must implement:
    - generate_signals(): Signal generation logic
    """

    def __init__(self, parameters: Dict):
        """
        Initialize strategy with parameters

        Args:
            parameters: Dictionary of strategy parameters
        """
        self.parameters = parameters
        self.name = self.__class__.__name__
        self.signals = None

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signals from data

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume

        Returns:
            Signal object with entries and exits
        """
        pass

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators
        Override this in child classes to add custom indicators

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        df = data.copy()

        # Add basic indicators if parameters exist
        if 'ma_fast' in self.parameters:
            df['ma_fast'] = df['close'].rolling(
                window=self.parameters['ma_fast']
            ).mean()

        if 'ma_slow' in self.parameters:
            df['ma_slow'] = df['close'].rolling(
                window=self.parameters['ma_slow']
            ).mean()

        if 'rsi_period' in self.parameters:
            df['rsi'] = self._calculate_rsi(
                df['close'],
                self.parameters['rsi_period']
            )

        if 'atr_period' in self.parameters:
            df['atr'] = self._calculate_atr(
                df,
                self.parameters['atr_period']
            )

        return df

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _calculate_atr(data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def _calculate_bollinger_bands(
        prices: pd.Series,
        period: int,
        std_dev: float
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band, sma, lower_band

    @staticmethod
    def _calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def validate_parameters(self) -> bool:
        """
        Validate strategy parameters
        Override in child classes for custom validation

        Returns:
            True if parameters are valid
        """
        required_params = self.get_required_parameters()

        for param in required_params:
            if param not in self.parameters:
                raise ValueError(f"Missing required parameter: {param}")

        return True

    @abstractmethod
    def get_required_parameters(self) -> list:
        """
        Get list of required parameters
        Must be implemented by child classes

        Returns:
            List of required parameter names
        """
        pass

    def get_parameter_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'required_params': self.get_required_parameters()
        }

    def __repr__(self):
        return f"{self.name}({self.parameters})"
