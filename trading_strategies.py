import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeSMAIndicator
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self, name: str):
        self.name = name
        self.signals = []
        self.performance_metrics = {}
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """Generate trading signal: 'BUY', 'SELL', or 'HOLD'"""
        raise NotImplementedError("Subclasses must implement generate_signal method")
    
    def get_signal_strength(self, data: pd.DataFrame) -> float:
        """Return signal strength between 0 and 1"""
        return 0.5

class RSIStrategy(TradingStrategy):
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(f"RSI_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.period:
            return 'HOLD'
        
        rsi = RSIIndicator(data['Close'], window=self.period).rsi()
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.oversold:
            return 'BUY'
        elif current_rsi > self.overbought:
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_signal_strength(self, data: pd.DataFrame) -> float:
        if len(data) < self.period:
            return 0.5
        
        rsi = RSIIndicator(data['Close'], window=self.period).rsi()
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.oversold:
            return (self.oversold - current_rsi) / self.oversold
        elif current_rsi > self.overbought:
            return (current_rsi - self.overbought) / (100 - self.overbought)
        else:
            return 0.5

class MACDStrategy(TradingStrategy):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(f"MACD_{fast}_{slow}_{signal}")
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < max(self.fast, self.slow, self.signal) + 1:
            return 'HOLD'
        
        macd_indicator = MACD(data['Close'], window_fast=self.fast, window_slow=self.slow, window_sign=self.signal)
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()
        
        if len(macd_line) < 2 or len(signal_line) < 2:
            return 'HOLD'
        
        # MACD crossover strategy
        if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
            return 'BUY'
        elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
            return 'SELL'
        else:
            return 'HOLD'

class BollingerBandsStrategy(TradingStrategy):
    def __init__(self, period: int = 20, std_dev: int = 2):
        super().__init__(f"BB_{period}_{std_dev}")
        self.period = period
        self.std_dev = std_dev
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.period:
            return 'HOLD'
        
        bb = BollingerBands(data['Close'], window=self.period, window_dev=self.std_dev)
        upper_band = bb.bollinger_hband()
        lower_band = bb.bollinger_lband()
        current_price = data['Close'].iloc[-1]
        
        if current_price < lower_band.iloc[-1]:
            return 'BUY'
        elif current_price > upper_band.iloc[-1]:
            return 'SELL'
        else:
            return 'HOLD'

class MovingAverageCrossoverStrategy(TradingStrategy):
    def __init__(self, short_period: int = 10, long_period: int = 30):
        super().__init__(f"MA_Cross_{short_period}_{long_period}")
        self.short_period = short_period
        self.long_period = long_period
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < max(self.short_period, self.long_period) + 1:
            return 'HOLD'
        
        short_ma = SMAIndicator(data['Close'], window=self.short_period).sma_indicator()
        long_ma = SMAIndicator(data['Close'], window=self.long_period).sma_indicator()
        
        if len(short_ma) < 2 or len(long_ma) < 2:
            return 'HOLD'
        
        # Golden cross / Death cross
        if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
            return 'BUY'
        elif short_ma.iloc[-1] < long_ma.iloc[-1] and short_ma.iloc[-2] >= long_ma.iloc[-2]:
            return 'SELL'
        else:
            return 'HOLD'

class MLRandomForestStrategy(TradingStrategy):
    def __init__(self, n_estimators: int = 200, min_samples_split: int = 50):
        super().__init__("ML_RandomForest")
        self.model = RandomForestClassifier(
            n_estimators=n_estimators, 
            min_samples_split=min_samples_split, 
            random_state=1
        )
        self.is_trained = False
        self.predictors = []
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare ML features based on the existing notebook approach"""
        df = data.copy()
        
        # Add target variable
        df['Tomorrow'] = df['Close'].shift(-1)
        df['Target'] = (df['Tomorrow'] > df['Close']).astype(int)
        
        # Create rolling averages and trend features
        horizons = [2, 5, 60, 250, 1000]
        new_predictors = ['Close', 'Volume', 'Open', 'High', 'Low']
        
        for horizon in horizons:
            rolling_averages = df.rolling(horizon).mean()
            
            ratio_column = f"Close_Ratio_{horizon}"
            df[ratio_column] = df['Close'] / rolling_averages['Close']
            
            trend_column = f"Trend_{horizon}"
            df[trend_column] = df.shift(1).rolling(horizon).sum()['Target']
            
            new_predictors += [ratio_column, trend_column]
        
        # Add RSI
        df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
        new_predictors.append('RSI')
        
        self.predictors = new_predictors
        return df.dropna()
    
    def train_model(self, data: pd.DataFrame):
        """Train the ML model"""
        prepared_data = self.prepare_features(data)
        
        if len(prepared_data) < 100:
            logger.warning("Not enough data to train ML model")
            return
        
        # Use 80% for training
        train_size = int(len(prepared_data) * 0.8)
        train_data = prepared_data.iloc[:train_size]
        
        try:
            self.model.fit(train_data[self.predictors], train_data['Target'])
            self.is_trained = True
            logger.info(f"ML model trained on {len(train_data)} samples")
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return 'HOLD'
        
        try:
            prepared_data = self.prepare_features(data)
            if prepared_data.empty or len(prepared_data) < 1:
                return 'HOLD'
            
            latest_features = prepared_data[self.predictors].iloc[-1:].fillna(0)
            prediction_proba = self.model.predict_proba(latest_features)[0]
            
            # Get RSI for additional logic
            rsi = prepared_data['RSI'].iloc[-1] if 'RSI' in prepared_data.columns else 50
            
            # Enhanced prediction logic from the notebook
            buy_probability = prediction_proba[1] if len(prediction_proba) > 1 else 0.5
            
            # Boost buy signal if RSI is oversold
            if rsi < 30:
                buy_probability = min(1.0, buy_probability * 1.5)
            
            if buy_probability >= 0.6:
                return 'BUY'
            elif buy_probability <= 0.4:
                return 'SELL'
            else:
                return 'HOLD'
                
        except Exception as e:
            logger.error(f"Error in ML signal generation: {e}")
            return 'HOLD'
    
    def get_signal_strength(self, data: pd.DataFrame) -> float:
        if not self.is_trained:
            return 0.5
        
        try:
            prepared_data = self.prepare_features(data)
            if prepared_data.empty:
                return 0.5
            
            latest_features = prepared_data[self.predictors].iloc[-1:].fillna(0)
            prediction_proba = self.model.predict_proba(latest_features)[0]
            
            return prediction_proba[1] if len(prediction_proba) > 1 else 0.5
        except:
            return 0.5

class VolumeStrategy(TradingStrategy):
    def __init__(self, volume_period: int = 20, volume_threshold: float = 1.5):
        super().__init__(f"Volume_{volume_period}")
        self.volume_period = volume_period
        self.volume_threshold = volume_threshold
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.volume_period:
            return 'HOLD'
        
        avg_volume = data['Volume'].rolling(self.volume_period).mean()
        current_volume = data['Volume'].iloc[-1]
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
        
        volume_ratio = current_volume / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 1
        
        # High volume with price increase = Buy signal
        if volume_ratio > self.volume_threshold and current_price > prev_price:
            return 'BUY'
        # High volume with price decrease = Sell signal
        elif volume_ratio > self.volume_threshold and current_price < prev_price:
            return 'SELL'
        else:
            return 'HOLD'

class CompositeStrategy(TradingStrategy):
    def __init__(self, strategies: List[TradingStrategy], weights: Optional[List[float]] = None):
        super().__init__("Composite")
        self.strategies = strategies
        self.weights = weights or [1.0] * len(strategies)
        
        if len(self.weights) != len(self.strategies):
            self.weights = [1.0] * len(strategies)
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        signals = []
        strengths = []
        
        for strategy, weight in zip(self.strategies, self.weights):
            signal = strategy.generate_signal(data)
            strength = strategy.get_signal_strength(data) * weight
            
            signals.append(signal)
            strengths.append(strength)
        
        # Calculate weighted average
        buy_weight = sum(s for s, sig in zip(strengths, signals) if sig == 'BUY')
        sell_weight = sum(s for s, sig in zip(strengths, signals) if sig == 'SELL')
        hold_weight = sum(s for s, sig in zip(strengths, signals) if sig == 'HOLD')
        
        total_weight = buy_weight + sell_weight + hold_weight
        
        if total_weight == 0:
            return 'HOLD'
        
        buy_ratio = buy_weight / total_weight
        sell_ratio = sell_weight / total_weight
        
        if buy_ratio > 0.6:
            return 'BUY'
        elif sell_ratio > 0.6:
            return 'SELL'
        else:
            return 'HOLD'

class StrategyManager:
    def __init__(self):
        self.strategies = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize all trading strategies"""
        self.strategies = {
            'rsi': RSIStrategy(),
            'macd': MACDStrategy(),
            'bb': BollingerBandsStrategy(),
            'ma_cross': MovingAverageCrossoverStrategy(),
            'ml_rf': MLRandomForestStrategy(),
            'volume': VolumeStrategy()
        }
        
        # Create composite strategy
        strategy_list = list(self.strategies.values())
        weights = [1.0, 1.2, 0.8, 1.0, 1.5, 0.7]  # Higher weight for ML
        self.strategies['composite'] = CompositeStrategy(strategy_list, weights)
    
    def get_strategy(self, name: str) -> Optional[TradingStrategy]:
        """Get strategy by name"""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> Dict[str, TradingStrategy]:
        """Get all strategies"""
        return self.strategies
    
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> Dict[str, Dict]:
        """Analyze a symbol with all strategies"""
        results = {}
        
        for name, strategy in self.strategies.items():
            try:
                signal = strategy.generate_signal(data)
                strength = strategy.get_signal_strength(data)
                
                results[name] = {
                    'signal': signal,
                    'strength': strength,
                    'strategy_name': strategy.name,
                    'timestamp': datetime.now()
                }
            except Exception as e:
                logger.error(f"Error analyzing {symbol} with {name}: {e}")
                results[name] = {
                    'signal': 'HOLD',
                    'strength': 0.5,
                    'strategy_name': strategy.name,
                    'timestamp': datetime.now(),
                    'error': str(e)
                }
        
        return results
    
    def train_ml_strategies(self, symbol: str, historical_data: pd.DataFrame):
        """Train ML strategies with historical data"""
        ml_strategy = self.strategies.get('ml_rf')
        if ml_strategy and isinstance(ml_strategy, MLRandomForestStrategy):
            ml_strategy.train_model(historical_data)
            logger.info(f"Trained ML strategy for {symbol}")