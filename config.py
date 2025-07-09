import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Alpha Vantage API Key (for real-time data)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    # Alpaca API Keys (for trading data)
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
    ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')  # Paper trading by default
    
    # Bot Configuration
    UPDATE_INTERVAL_MINUTES = int(os.getenv('UPDATE_INTERVAL_MINUTES', 1))  # Minute-by-minute updates
    WATCHLIST = os.getenv('WATCHLIST', 'AAPL,GOOGL,MSFT,AMZN,TSLA').split(',')
    
    # Trading Strategy Configuration
    RSI_OVERSOLD_THRESHOLD = int(os.getenv('RSI_OVERSOLD_THRESHOLD', 30))
    RSI_OVERBOUGHT_THRESHOLD = int(os.getenv('RSI_OVERBOUGHT_THRESHOLD', 70))
    
    # Risk Management
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 0.1))  # 10% of portfolio
    STOP_LOSS_PERCENTAGE = float(os.getenv('STOP_LOSS_PERCENTAGE', 0.02))  # 2% stop loss
    
    # Backtesting Configuration
    BACKTESTING_YEARS = int(os.getenv('BACKTESTING_YEARS', 2))
    INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', 10000.0))
    
    # Notification Recipients
    SMS_RECIPIENTS = os.getenv('SMS_RECIPIENTS', '').split(',') if os.getenv('SMS_RECIPIENTS') else []