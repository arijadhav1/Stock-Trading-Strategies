#!/usr/bin/env python3
"""
Finance Bot Demonstration Script

This script demonstrates the key features of the finance bot:
1. Data fetching
2. Trading strategy analysis
3. Backtesting
4. SMS notifications (if configured)

Run this script to see the bot in action without starting the full automation.
"""

import pandas as pd
from datetime import datetime
import time

from data_fetcher import DataFetcher
from trading_strategies import StrategyManager
from backtesting_engine import BacktestingEngine
from sms_notifier import SMSNotifier
from config import Config

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f"📊 {title}")
    print(f"{'-'*40}")

def demonstrate_data_fetching():
    """Demonstrate data fetching capabilities"""
    print_header("DATA FETCHING DEMONSTRATION")
    
    data_fetcher = DataFetcher()
    
    # Test symbol
    symbol = "AAPL"
    
    print_section("Real-time Data")
    real_time_data = data_fetcher.get_real_time_data(symbol)
    if real_time_data:
        print(f"Symbol: {real_time_data['symbol']}")
        print(f"Current Price: ${real_time_data['price']:.2f}")
        print(f"Volume: {real_time_data['volume']:,}")
        print(f"Market Cap: ${real_time_data.get('market_cap', 0):,}")
        print(f"P/E Ratio: {real_time_data.get('pe_ratio', 'N/A')}")
    else:
        print("❌ Could not fetch real-time data")
    
    print_section("Historical Data")
    historical_data = data_fetcher.get_historical_data(symbol, period="3mo")
    if not historical_data.empty:
        print(f"📈 Historical data for {symbol}:")
        print(f"   Data points: {len(historical_data)}")
        print(f"   Date range: {historical_data.index[0].date()} to {historical_data.index[-1].date()}")
        print(f"   Latest close: ${historical_data['Close'].iloc[-1]:.2f}")
        print(f"   Price change (3mo): {((historical_data['Close'].iloc[-1] / historical_data['Close'].iloc[0]) - 1) * 100:.2f}%")
    else:
        print("❌ Could not fetch historical data")
    
    print_section("Market Overview")
    market_data = data_fetcher.get_market_overview()
    if market_data:
        for symbol_key, data in market_data.items():
            change_indicator = "🟢" if data['change_percent'] > 0 else "🔴" if data['change_percent'] < 0 else "⚪"
            print(f"{change_indicator} {data['name']}: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")
    else:
        print("❌ Could not fetch market overview")
    
    print_section("Company News")
    news = data_fetcher.get_company_news(symbol, limit=3)
    if news:
        for i, article in enumerate(news, 1):
            print(f"{i}. {article['title']}")
            print(f"   Source: {article['source']} | {article['published'].strftime('%Y-%m-%d %H:%M')}")
    else:
        print("❌ Could not fetch company news")

def demonstrate_trading_strategies():
    """Demonstrate trading strategy analysis"""
    print_header("TRADING STRATEGIES DEMONSTRATION")
    
    data_fetcher = DataFetcher()
    strategy_manager = StrategyManager()
    
    symbol = "AAPL"
    
    print_section(f"Strategy Analysis for {symbol}")
    
    # Get historical data
    data = data_fetcher.get_historical_data(symbol, period="6mo")
    if data.empty:
        print("❌ Could not fetch data for strategy analysis")
        return
    
    # Train ML strategies
    strategy_manager.train_ml_strategies(symbol, data)
    
    # Analyze with all strategies
    results = strategy_manager.analyze_symbol(symbol, data)
    
    # Get current price for context
    real_time_data = data_fetcher.get_real_time_data(symbol)
    current_price = real_time_data['price'] if real_time_data else data['Close'].iloc[-1]
    
    print(f"Current Price: ${current_price:.2f}")
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Display results in a table format
    print(f"{'Strategy':<20} {'Signal':<8} {'Strength':<15} {'Confidence'}")
    print("-" * 60)
    
    for strategy_name, result in results.items():
        signal = result.get('signal', 'HOLD')
        strength = result.get('strength', 0.5)
        
        # Visual strength indicator
        strength_bar = "█" * int(strength * 5) + "░" * (5 - int(strength * 5))
        confidence = f"{strength:.0%}"
        
        # Color coding for signals
        signal_indicator = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "🟡"
        
        print(f"{strategy_name:<20} {signal_indicator}{signal:<7} {strength_bar:<15} {confidence}")
    
    print_section("Strategy Consensus")
    
    # Count signal types
    buy_signals = sum(1 for r in results.values() if r.get('signal') == 'BUY')
    sell_signals = sum(1 for r in results.values() if r.get('signal') == 'SELL')
    hold_signals = sum(1 for r in results.values() if r.get('signal') == 'HOLD')
    
    total_strategies = len(results)
    
    print(f"📈 BUY signals:  {buy_signals}/{total_strategies} ({buy_signals/total_strategies:.0%})")
    print(f"📉 SELL signals: {sell_signals}/{total_strategies} ({sell_signals/total_strategies:.0%})")
    print(f"⏸️  HOLD signals: {hold_signals}/{total_strategies} ({hold_signals/total_strategies:.0%})")
    
    # Highlight composite strategy
    composite_result = results.get('composite', {})
    if composite_result:
        signal = composite_result.get('signal', 'HOLD')
        strength = composite_result.get('strength', 0.5)
        print(f"\n🎯 COMPOSITE RECOMMENDATION: {signal} (Confidence: {strength:.0%})")

def demonstrate_backtesting():
    """Demonstrate backtesting capabilities"""
    print_header("BACKTESTING DEMONSTRATION")
    
    data_fetcher = DataFetcher()
    backtesting_engine = BacktestingEngine(initial_capital=10000.0)
    
    symbol = "AAPL"
    
    print_section(f"Running Backtest for {symbol}")
    print("⏳ This may take a moment...")
    
    # Get historical data for backtesting
    data = data_fetcher.get_historical_data(symbol, period="1y")
    if data.empty:
        print("❌ Could not fetch data for backtesting")
        return
    
    # Run comprehensive backtest
    results = backtesting_engine.run_comprehensive_backtest(symbol, data)
    
    if not results:
        print("❌ Backtesting failed")
        return
    
    # Generate and display report
    report = backtesting_engine.generate_backtest_report(symbol, results)
    print(report)
    
    print_section("Best Strategy Details")
    
    # Find best strategy
    best_strategy_name = max(results.keys(), key=lambda k: results[k].total_return)
    best_result = results[best_strategy_name]
    
    print(f"🏆 Best Performing Strategy: {best_strategy_name}")
    print(f"💰 Net Profit: ${best_result.net_profit:.2f}")
    print(f"📈 Total Return: {best_result.total_return:.2%}")
    print(f"🎯 Win Rate: {best_result.win_rate:.2%}")
    print(f"🔍 Signal Accuracy: {best_result.signals_accuracy:.2%}")
    print(f"📊 Sharpe Ratio: {best_result.sharpe_ratio:.2f}")
    print(f"📉 Max Drawdown: {best_result.max_drawdown:.2%}")
    print(f"🔢 Total Trades: {best_result.total_trades}")
    
    if best_result.trades:
        print_section("Recent Trades")
        recent_trades = best_result.trades[-5:]  # Last 5 trades
        for i, trade in enumerate(recent_trades, 1):
            profit_indicator = "💚" if trade.profit_loss > 0 else "❤️"
            print(f"{profit_indicator} Trade {i}: {trade.trade_type} @ ${trade.entry_price:.2f} → ${trade.exit_price:.2f} "
                  f"(P&L: ${trade.profit_loss:.2f})")

def demonstrate_sms_notifications():
    """Demonstrate SMS notification capabilities"""
    print_header("SMS NOTIFICATIONS DEMONSTRATION")
    
    sms_notifier = SMSNotifier()
    
    print_section("SMS Configuration Status")
    
    if sms_notifier.is_configured():
        print("✅ SMS is properly configured")
        print(f"📱 Recipients: {len(sms_notifier.get_recipients())} number(s)")
        
        print_section("Testing SMS Connection")
        user_input = input("Would you like to send a test SMS? (y/N): ").strip().lower()
        
        if user_input == 'y':
            print("📤 Sending test SMS...")
            success = sms_notifier.test_sms_connection()
            if success:
                print("✅ Test SMS sent successfully!")
            else:
                print("❌ Failed to send test SMS")
        else:
            print("⏭️  Skipping SMS test")
            
        print_section("SMS Notification Examples")
        print("The bot can send various types of notifications:")
        print("📊 Trading signals with strength indicators")
        print("📈 Market overview updates")
        print("🎯 Backtest result summaries")
        print("📱 Portfolio performance updates")
        print("🚨 Custom alerts and news notifications")
        
    else:
        print("❌ SMS is not configured")
        print("📝 To enable SMS notifications:")
        print("   1. Sign up for a Twilio account")
        print("   2. Add your credentials to the .env file")
        print("   3. Add recipient phone numbers")
        print("   4. Restart the demo")

def main():
    """Main demonstration function"""
    print_header("ADVANCED FINANCE BOT DEMONSTRATION")
    print("🚀 This demo showcases the key features of the finance bot")
    print("📊 You can run this anytime to test functionality")
    print()
    
    # Check if market is open
    data_fetcher = DataFetcher()
    market_status = "🟢 OPEN" if data_fetcher.is_market_open() else "🔴 CLOSED"
    print(f"📈 Market Status: {market_status}")
    print(f"⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run demonstrations
        demonstrate_data_fetching()
        time.sleep(1)
        
        demonstrate_trading_strategies()
        time.sleep(1)
        
        demonstrate_backtesting()
        time.sleep(1)
        
        demonstrate_sms_notifications()
        
        print_header("DEMONSTRATION COMPLETE")
        print("🎉 All demonstrations completed successfully!")
        print("📚 Check the README.md for detailed usage instructions")
        print("🤖 To start the full bot, run: python finance_bot.py")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("🔧 Check your configuration and try again")

if __name__ == "__main__":
    main()