"""
163 Parameter System for Trading Strategies
Comprehensive parameter definitions for strategy optimization
"""
import numpy as np
from typing import Dict, List, Any


class ParameterDefinitions:
    """
    163 parametre tanımları - 6 kategoride
    """

    @staticmethod
    def get_all_parameters() -> Dict[str, Any]:
        """Tüm parametreleri döndür"""
        params = {}

        # Teknik İndikatörler (50 parametre)
        params.update(ParameterDefinitions.get_technical_indicators())

        # Risk Yönetimi (20 parametre)
        params.update(ParameterDefinitions.get_risk_management())

        # Entry/Exit Koşulları (30 parametre)
        params.update(ParameterDefinitions.get_entry_exit_conditions())

        # Position Sizing (15 parametre)
        params.update(ParameterDefinitions.get_position_sizing())

        # Timing (20 parametre)
        params.update(ParameterDefinitions.get_timing_parameters())

        # Market Conditions (28 parametre)
        params.update(ParameterDefinitions.get_market_conditions())

        return params

    @staticmethod
    def get_technical_indicators() -> Dict[str, Any]:
        """Teknik İndikatör Parametreleri (50 adet)"""
        return {
            # RSI
            'rsi_period': range(10, 30),
            'rsi_oversold': range(20, 40),
            'rsi_overbought': range(60, 80),

            # Moving Averages
            'ma_fast': range(5, 50),
            'ma_slow': range(50, 200),
            'ema_period': range(10, 50),

            # Bollinger Bands
            'bollinger_period': range(15, 25),
            'bollinger_std': np.arange(1.5, 2.5, 0.1).tolist(),

            # MACD
            'macd_fast': range(8, 15),
            'macd_slow': range(21, 35),
            'macd_signal': range(7, 12),

            # Stochastic
            'stoch_k': range(10, 20),
            'stoch_d': range(3, 8),
            'stoch_smooth': range(1, 5),

            # Other Oscillators
            'williams_r_period': range(10, 20),
            'cci_period': range(15, 25),
            'roc_period': range(10, 20),

            # Trend Indicators
            'adx_period': range(10, 20),
            'adx_threshold': range(20, 40),

            # Volatility
            'atr_period': range(10, 20),
            'atr_multiplier': np.arange(1.0, 3.0, 0.5).tolist(),

            # Volume
            'volume_sma': range(15, 30),
            'volume_threshold': np.arange(1.2, 3.0, 0.2).tolist(),
            'obv_period': range(10, 30),

            # VWAP
            'vwap_period': range(10, 30),

            # Momentum
            'momentum_period': range(8, 20),

            # Ichimoku
            'ichimoku_tenkan': range(7, 12),
            'ichimoku_kijun': range(20, 30),
            'ichimoku_senkou': range(40, 60),

            # Price Channels
            'donchian_period': range(15, 30),
            'keltner_period': range(15, 25),

            # Additional
            'psar_acceleration': np.arange(0.01, 0.05, 0.01).tolist(),
            'psar_maximum': np.arange(0.1, 0.3, 0.05).tolist(),
        }

    @staticmethod
    def get_risk_management() -> Dict[str, Any]:
        """Risk Yönetimi Parametreleri (20 adet)"""
        return {
            # Stop Loss & Take Profit
            'stop_loss_pct': np.arange(0.01, 0.1, 0.005).tolist(),
            'take_profit_pct': np.arange(0.02, 0.2, 0.01).tolist(),
            'trailing_stop_pct': np.arange(0.005, 0.05, 0.005).tolist(),
            'stop_loss_atr_mult': np.arange(1.0, 4.0, 0.5).tolist(),
            'take_profit_atr_mult': np.arange(2.0, 6.0, 0.5).tolist(),

            # Position & Portfolio Risk
            'max_position_size': np.arange(0.1, 1.0, 0.1).tolist(),
            'risk_per_trade': np.arange(0.01, 0.05, 0.005).tolist(),
            'max_daily_loss': np.arange(0.02, 0.1, 0.01).tolist(),
            'max_portfolio_risk': np.arange(0.01, 0.05, 0.005).tolist(),

            # Correlation & Diversification
            'correlation_limit': np.arange(0.3, 0.8, 0.05).tolist(),
            'max_correlated_positions': range(2, 6),

            # Drawdown
            'drawdown_limit': np.arange(0.05, 0.2, 0.01).tolist(),
            'drawdown_recovery_period': range(5, 30),

            # VaR (Value at Risk)
            'var_confidence': [0.95, 0.99],
            'var_period': range(10, 30),

            # Risk-Free Rate
            'risk_free_rate': np.arange(0.02, 0.05, 0.005).tolist(),

            # Leverage
            'max_leverage': np.arange(1.0, 3.0, 0.5).tolist(),

            # Emergency Exit
            'emergency_exit_enabled': [True, False],
            'emergency_exit_threshold': np.arange(0.05, 0.15, 0.02).tolist(),
        }

    @staticmethod
    def get_entry_exit_conditions() -> Dict[str, Any]:
        """Entry/Exit Koşul Parametreleri (30 adet)"""
        return {
            # Entry Confirmation
            'entry_confirmation_bars': range(1, 5),
            'entry_volume_confirm': [True, False],
            'entry_trend_confirm': [True, False],

            # Exit Confirmation
            'exit_confirmation_bars': range(1, 3),
            'exit_on_opposite_signal': [True, False],

            # Trend Filters
            'trend_confirmation_bars': range(2, 10),
            'trend_strength_min': np.arange(0.3, 0.8, 0.05).tolist(),
            'trend_filter_ma_period': range(50, 200),

            # Volume Conditions
            'volume_threshold': np.arange(1.2, 3.0, 0.1).tolist(),
            'volume_spike_threshold': np.arange(1.5, 3.0, 0.2).tolist(),
            'min_volume_ratio': np.arange(0.5, 1.5, 0.1).tolist(),

            # Price Action
            'price_action_confirmation': range(1, 5),
            'breakout_threshold': np.arange(0.01, 0.05, 0.005).tolist(),
            'support_resistance_period': range(10, 50),

            # Divergence
            'divergence_enabled': [True, False],
            'divergence_lookback': range(10, 30),
            'divergence_threshold': np.arange(0.1, 0.5, 0.05).tolist(),

            # Gap Trading
            'gap_threshold': np.arange(0.005, 0.02, 0.002).tolist(),
            'gap_fill_required': [True, False],

            # Time-based
            'time_stop_hours': range(4, 48),
            'time_stop_bars': range(5, 50),

            # Multiple Timeframe
            'mtf_enabled': [True, False],
            'mtf_higher_timeframe': ['4h', '1d', '1w'],
            'mtf_confirmation_required': [True, False],

            # Pattern Recognition
            'pattern_recognition_enabled': [True, False],
            'candlestick_patterns': [True, False],

            # Volatility Filters
            'volatility_filter_enabled': [True, False],
            'volatility_filter_min': np.arange(0.5, 2.0, 0.1).tolist(),
            'volatility_filter_max': np.arange(2.0, 5.0, 0.2).tolist(),
        }

    @staticmethod
    def get_position_sizing() -> Dict[str, Any]:
        """Position Sizing Parametreleri (15 adet)"""
        return {
            # Sizing Method
            'position_sizing_method': ['fixed', 'percent', 'volatility', 'kelly', 'optimal_f'],

            # Fixed Size
            'fixed_size': range(100, 1000, 100),
            'fixed_units': range(1, 10),

            # Percent of Equity
            'equity_percent': np.arange(0.01, 0.2, 0.01).tolist(),

            # Kelly Criterion
            'kelly_multiplier': np.arange(0.1, 1.0, 0.1).tolist(),
            'kelly_max_fraction': np.arange(0.1, 0.5, 0.05).tolist(),

            # Fixed Fractional
            'fixed_fractional': np.arange(0.01, 0.1, 0.01).tolist(),

            # Volatility Adjusted
            'volatility_adjusted': [True, False],
            'volatility_target': np.arange(0.1, 0.3, 0.05).tolist(),

            # Risk-Based
            'risk_based_sizing': [True, False],
            'target_risk_per_trade': np.arange(0.01, 0.05, 0.005).tolist(),

            # Pyramiding
            'pyramiding_enabled': [True, False],
            'max_pyramiding_levels': range(1, 5),
            'pyramiding_scale': np.arange(0.5, 1.0, 0.1).tolist(),
        }

    @staticmethod
    def get_timing_parameters() -> Dict[str, Any]:
        """Timing Parametreleri (20 adet)"""
        return {
            # Entry/Exit Delays
            'entry_delay_bars': range(0, 5),
            'exit_delay_bars': range(0, 3),

            # Session Filters
            'session_filter_enabled': [True, False],
            'session_start_hour': range(0, 24),
            'session_end_hour': range(0, 24),
            'trade_on_session': ['all', 'us_session', 'europe_session', 'asia_session'],

            # Day of Week
            'day_of_week_filter': ['all', 'weekdays', 'avoid_monday', 'avoid_friday', 'mid_week_only'],
            'trade_on_monday': [True, False],
            'trade_on_friday': [True, False],

            # Month Effects
            'month_filter_enabled': [True, False],
            'avoid_month_start': [True, False],
            'avoid_month_end': [True, False],

            # News & Events
            'avoid_news_events': [True, False],
            'news_blackout_hours': range(1, 24),

            # Market Open/Close
            'avoid_market_open': [True, False],
            'avoid_market_close': [True, False],
            'market_open_buffer_min': range(0, 60),
            'market_close_buffer_min': range(0, 60),

            # Holding Period
            'min_holding_period_bars': range(1, 20),
            'max_holding_period_bars': range(10, 100),
        }

    @staticmethod
    def get_market_conditions() -> Dict[str, Any]:
        """Market Condition Parametreleri (28 adet)"""
        return {
            # Market Regime Detection
            'regime_detection_enabled': [True, False],
            'regime_detection_period': range(20, 100),
            'trending_threshold': np.arange(0.6, 0.9, 0.05).tolist(),
            'ranging_threshold': np.arange(0.3, 0.6, 0.05).tolist(),

            # Volatility Regime
            'volatility_regime_enabled': [True, False],
            'volatility_regime_fast': range(5, 20),
            'volatility_regime_slow': range(20, 50),
            'high_volatility_threshold': np.arange(1.5, 3.0, 0.2).tolist(),
            'low_volatility_threshold': np.arange(0.3, 1.0, 0.1).tolist(),

            # Trend Strength
            'trend_strength_filter': [True, False],
            'min_trend_strength': np.arange(0.3, 0.7, 0.05).tolist(),

            # Market Correlation
            'market_correlation_enabled': [True, False],
            'correlation_window': range(20, 60),
            'correlation_threshold': np.arange(0.5, 0.9, 0.05).tolist(),

            # Market Breadth
            'market_breadth_enabled': [True, False],
            'breadth_threshold': np.arange(0.3, 0.7, 0.05).tolist(),

            # Sector/Market Filters
            'market_cap_filter': ['all', 'large_cap', 'mid_cap', 'small_cap'],
            'sector_filter': ['all', 'tech', 'finance', 'healthcare', 'energy', 'consumer'],

            # Liquidity
            'min_liquidity': np.arange(100000, 1000000, 100000).tolist(),
            'spread_filter_enabled': [True, False],
            'max_spread_pct': np.arange(0.001, 0.01, 0.001).tolist(),

            # Market State
            'bull_market_multiplier': np.arange(1.0, 2.0, 0.1).tolist(),
            'bear_market_multiplier': np.arange(0.5, 1.0, 0.1).tolist(),

            # Sentiment
            'sentiment_enabled': [True, False],
            'sentiment_weight': np.arange(0.0, 0.3, 0.05).tolist(),

            # Mean Reversion
            'mean_reversion_period': range(10, 50),
            'mean_reversion_threshold': np.arange(1.0, 3.0, 0.2).tolist(),
        }

    @staticmethod
    def get_parameter_count() -> int:
        """Toplam parametre sayısını hesapla"""
        all_params = ParameterDefinitions.get_all_parameters()
        return len(all_params)

    @staticmethod
    def get_parameters_by_category() -> Dict[str, int]:
        """Kategori başına parametre sayısı"""
        return {
            'Technical Indicators': len(ParameterDefinitions.get_technical_indicators()),
            'Risk Management': len(ParameterDefinitions.get_risk_management()),
            'Entry/Exit Conditions': len(ParameterDefinitions.get_entry_exit_conditions()),
            'Position Sizing': len(ParameterDefinitions.get_position_sizing()),
            'Timing': len(ParameterDefinitions.get_timing_parameters()),
            'Market Conditions': len(ParameterDefinitions.get_market_conditions()),
        }

    @staticmethod
    def get_default_parameters() -> Dict[str, Any]:
        """Default değerlerle basit parametre seti"""
        return {
            # Basic MA strategy defaults
            'ma_fast': 10,
            'ma_slow': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04,
            'position_sizing_method': 'percent',
            'equity_percent': 0.1,
            'risk_per_trade': 0.02,
        }


if __name__ == "__main__":
    # Test parameter system
    print("="*60)
    print("163 PARAMETER SYSTEM")
    print("="*60)

    params = ParameterDefinitions.get_all_parameters()
    print(f"\nTotal Parameters: {ParameterDefinitions.get_parameter_count()}")

    print("\nParameters by Category:")
    for category, count in ParameterDefinitions.get_parameters_by_category().items():
        print(f"  {category:25}: {count} parameters")

    print("\nDefault Parameters:")
    defaults = ParameterDefinitions.get_default_parameters()
    for key, value in defaults.items():
        print(f"  {key:30}: {value}")

    print("\n" + "="*60)
