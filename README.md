# 🤖 Advanced Finance Trading Bot

A comprehensive, real-time finance bot that provides minute-by-minute trading signals, advanced backtesting capabilities, and SMS notifications via Twilio. Built with machine learning and multiple trading strategies to analyze stock data like never before.

## 🚀 Features

### Real-Time Trading Signals
- **Minute-by-minute updates** during market hours
- **Multiple trading strategies**:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Moving Average Crossover
  - Volume Analysis
  - Machine Learning (Random Forest)
  - Composite Strategy (combines all strategies)

### Advanced Backtesting
- **Comprehensive performance metrics**:
  - Win rate percentage
  - Signal accuracy percentage
  - Total return and profit calculations
  - Sharpe ratio
  - Maximum drawdown
  - Profit factor
- **Strategy comparison** across multiple timeframes
- **Automated daily backtesting** with SMS summaries

### SMS Integration
- **Real-time notifications** via Twilio
- **Market overview updates**
- **Trading signal alerts** with strength indicators
- **Backtest result summaries**
- **Portfolio performance updates**

### Data Sources
- **Yahoo Finance** (primary data source)
- **Alpha Vantage** (optional for enhanced real-time data)
- **Real-time market data** with multiple fallback options

## 📋 Requirements

- Python 3.8+
- Twilio account (for SMS notifications)
- Alpha Vantage API key (optional, for enhanced data)

## 🔧 Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd finance-bot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys and phone numbers
```

4. **Set up Twilio** (Required for SMS):
   - Sign up at [Twilio](https://www.twilio.com/)
   - Get your Account SID, Auth Token, and phone number
   - Add them to your `.env` file

5. **Optional: Set up Alpha Vantage**:
   - Get free API key at [Alpha Vantage](https://www.alphavantage.co/)
   - Add to `.env` file for enhanced real-time data

## ⚙️ Configuration

Edit your `.env` file with the following settings:

```env
# Required for SMS notifications
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
SMS_RECIPIENTS=+1234567890,+0987654321

# Optional for enhanced data
ALPHA_VANTAGE_API_KEY=your_api_key

# Bot settings
UPDATE_INTERVAL_MINUTES=1
WATCHLIST=AAPL,GOOGL,MSFT,AMZN,TSLA
INITIAL_CAPITAL=10000.0
```

## 🚀 Usage

### Start the Bot
```bash
python finance_bot.py
```

The bot will:
- Send a test SMS to verify connectivity
- Start monitoring your watchlist
- Send real-time trading signals
- Provide market updates every 15 minutes
- Run daily backtests at market close

### Interactive Usage

You can also use the bot interactively:

```python
from finance_bot import FinanceBot

bot = FinanceBot()

# Run manual analysis
result = bot.run_manual_analysis('AAPL')
print(result)

# Run backtest for specific symbol
backtest = bot.run_single_backtest('AAPL')
print(backtest)

# Get current signals
signals = bot.get_current_signals()
print(signals)

# Add/remove symbols from watchlist
bot.add_symbol_to_watchlist('TSLA')
bot.remove_symbol_from_watchlist('AAPL')
```

## 📊 Trading Strategies

### 1. RSI Strategy
- **Buy**: RSI < 30 (oversold)
- **Sell**: RSI > 70 (overbought)
- **Configurable thresholds**

### 2. MACD Strategy
- **Buy**: MACD line crosses above signal line
- **Sell**: MACD line crosses below signal line

### 3. Bollinger Bands
- **Buy**: Price touches lower band
- **Sell**: Price touches upper band

### 4. Moving Average Crossover
- **Buy**: Short MA crosses above long MA (Golden Cross)
- **Sell**: Short MA crosses below long MA (Death Cross)

### 5. Volume Strategy
- **Buy**: High volume + price increase
- **Sell**: High volume + price decrease

### 6. Machine Learning (Random Forest)
- Uses features from existing notebook:
  - Rolling averages (2, 5, 60, 250, 1000 periods)
  - Price ratios
  - Trend indicators
  - RSI integration
- **Enhanced with RSI boost** for oversold conditions

### 7. Composite Strategy
- **Combines all strategies** with weighted voting
- **Higher weight** for ML predictions
- **Requires 60% consensus** for signals

## 📈 Backtesting Results

The bot provides comprehensive backtesting metrics:

```
STRATEGY PERFORMANCE COMPARISON:
Strategy          Total Return  Win Rate  Signal Accuracy  Total Trades  Sharpe Ratio
Composite         15.23%        68.5%     72.3%           45            1.25
ML_RandomForest   12.87%        65.2%     69.8%           38            1.18
RSI_14            8.45%         61.3%     64.2%           52            0.95
```

## 📱 SMS Notifications

The bot sends various types of SMS notifications:

### Trading Signals
```
🟢📈 TRADING SIGNAL 🟢📈

Symbol: AAPL
Signal: BUY
Strategy: Composite
Price: $175.23
Strength: ████░ (80%)

Supported by: RSI, ML_RandomForest, Volume

Time: 14:32:15
```

### Market Updates
```
📊 MARKET OVERVIEW 📊

🟢 S&P 500: $4,234.56 (+0.75%)
🟢 NASDAQ: $13,045.23 (+1.23%)
🔴 Dow Jones: $33,987.45 (-0.34%)

Time: 15:00:00
```

### Backtest Results
```
🎉 BACKTEST RESULTS 🎉

Symbol: AAPL
Best Strategy: Composite

📈 Total Return: 15.23%
🎯 Win Rate: 68.50%
🔍 Signal Accuracy: 72.30%

Time: 16:30:00
```

## 🔒 Risk Management

- **Position sizing**: Maximum 10% of capital per position
- **Stop losses**: 2% automatic stop loss
- **Commission fees**: 0.1% per trade factored into backtesting
- **Paper trading**: Default Alpaca configuration for safe testing

## 🛠️ Customization

### Adding New Strategies

1. Create a new strategy class in `trading_strategies.py`:

```python
class MyCustomStrategy(TradingStrategy):
    def __init__(self):
        super().__init__("MyCustom")
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        # Your custom logic here
        return 'BUY'  # or 'SELL' or 'HOLD'
```

2. Add it to the StrategyManager:

```python
self.strategies['my_custom'] = MyCustomStrategy()
```

### Modifying Watchlist

Update the `WATCHLIST` in your `.env` file:
```env
WATCHLIST=AAPL,GOOGL,MSFT,AMZN,TSLA,NVDA,META,NFLX,SPY,QQQ
```

### Adjusting Update Frequency

Change the update interval:
```env
UPDATE_INTERVAL_MINUTES=5  # Update every 5 minutes instead of 1
```

## 📊 Performance Monitoring

The bot tracks and reports:
- **Signal accuracy** over time
- **Strategy performance** comparison
- **Market correlation** analysis
- **Risk-adjusted returns**

## 🚨 Troubleshooting

### Common Issues

1. **SMS not working**:
   - Verify Twilio credentials in `.env`
   - Check phone number format (+1234567890)
   - Ensure Twilio account has sufficient balance

2. **No data for symbols**:
   - Check symbol spelling (use uppercase)
   - Verify market hours
   - Try different data sources

3. **ML model not training**:
   - Ensure sufficient historical data (>100 points)
   - Check for data quality issues

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 File Structure

```
finance-bot/
├── config.py              # Configuration management
├── data_fetcher.py         # Data collection from APIs
├── trading_strategies.py   # All trading strategies
├── backtesting_engine.py   # Backtesting framework
├── sms_notifier.py        # Twilio SMS integration
├── finance_bot.py         # Main bot application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Submit a pull request

## ⚠️ Disclaimer

This bot is for educational and research purposes only. It is not financial advice. Always do your own research and consider consulting with a financial advisor before making investment decisions. Past performance does not guarantee future results.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Open an issue on GitHub

---

**Happy Trading! 📈💰**