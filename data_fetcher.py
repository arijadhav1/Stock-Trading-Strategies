import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.alpha_vantage_key = Config.ALPHA_VANTAGE_API_KEY
        self.cache = {}
        self.last_fetch_time = {}
        
    def get_real_time_data(self, symbol: str) -> Dict:
        """Get real-time data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get latest price data
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None
                
            latest = hist.iloc[-1]
            
            return {
                'symbol': symbol,
                'price': latest['Close'],
                'volume': latest['Volume'],
                'high': latest['High'],
                'low': latest['Low'],
                'open': latest['Open'],
                'timestamp': datetime.now(),
                'previous_close': info.get('previousClose', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0)
            }
        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
        """Get historical data for backtesting"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.error(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Clean the data
            data = data.drop(['Dividends', 'Stock Splits'], axis=1, errors='ignore')
            data['Tomorrow'] = data['Close'].shift(-1)
            data['Target'] = (data['Tomorrow'] > data['Close']).astype(int)
            
            return data.dropna()
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_intraday_data(self, symbol: str, interval: str = "1min") -> pd.DataFrame:
        """Get intraday data using Alpha Vantage API"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not provided, using yfinance for intraday data")
            return self._get_yfinance_intraday(symbol, interval)
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': interval,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'compact'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return self._get_yfinance_intraday(symbol, interval)
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                time.sleep(60)  # Wait 1 minute for rate limit
                return self._get_yfinance_intraday(symbol, interval)
            
            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                return self._get_yfinance_intraday(symbol, interval)
            
            time_series = data[time_series_key]
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return self._get_yfinance_intraday(symbol, interval)

    def _get_yfinance_intraday(self, symbol: str, interval: str) -> pd.DataFrame:
        """Fallback to yfinance for intraday data"""
        try:
            ticker = yf.Ticker(symbol)
            # Convert interval format for yfinance
            yf_interval = interval.replace('min', 'm')
            data = ticker.history(period="1d", interval=yf_interval)
            return data
        except Exception as e:
            logger.error(f"Error fetching yfinance intraday data for {symbol}: {e}")
            return pd.DataFrame()

    def get_market_overview(self) -> Dict:
        """Get overall market data"""
        try:
            # Get major indices
            indices = {
                'SPY': 'S&P 500',
                'QQQ': 'NASDAQ',
                'DIA': 'Dow Jones',
                'VIX': 'Volatility Index'
            }
            
            market_data = {}
            for symbol, name in indices.items():
                data = self.get_real_time_data(symbol)
                if data:
                    prev_close = data.get('previous_close', data['price'])
                    change = data['price'] - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                    
                    market_data[symbol] = {
                        'name': name,
                        'price': data['price'],
                        'change': change,
                        'change_percent': change_pct
                    }
            
            return market_data
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            return {}

    def get_batch_real_time_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time data for multiple symbols"""
        results = {}
        for symbol in symbols:
            data = self.get_real_time_data(symbol)
            if data:
                results[symbol] = data
            time.sleep(0.1)  # Small delay to avoid rate limiting
        return results

    def get_company_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Get recent news for a company"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            formatted_news = []
            for item in news[:limit]:
                formatted_news.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)),
                    'source': item.get('publisher', '')
                })
            
            return formatted_news
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def is_market_open(self) -> bool:
        """Check if the market is currently open"""
        now = datetime.now()
        # Simple check for US market hours (9:30 AM - 4:00 PM ET, Monday-Friday)
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        
        if weekday >= 5:  # Weekend
            return False
        
        market_open = (hour > 9) or (hour == 9 and minute >= 30)
        market_close = hour < 16
        
        return market_open and market_close