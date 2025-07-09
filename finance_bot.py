import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading

from config import Config
from data_fetcher import DataFetcher
from trading_strategies import StrategyManager
from backtesting_engine import BacktestingEngine
from sms_notifier import SMSNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinanceBot:
    def __init__(self):
        self.config = Config()
        self.data_fetcher = DataFetcher()
        self.strategy_manager = StrategyManager()
        self.backtesting_engine = BacktestingEngine(
            initial_capital=Config.INITIAL_CAPITAL,
            commission=0.001
        )
        self.sms_notifier = SMSNotifier()
        self.scheduler = BackgroundScheduler()
        
        # Bot state
        self.is_running = False
        self.last_signals = {}
        self.last_market_update = None
        self.trading_history = []
        
        # Performance tracking
        self.signal_stats = {
            'total_signals': 0,
            'correct_signals': 0,
            'by_strategy': {}
        }
        
        logger.info("Finance Bot initialized successfully")
    
    def start(self):
        """Start the finance bot"""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        logger.info("Starting Finance Bot...")
        
        # Test SMS connection
        if self.sms_notifier.is_configured():
            self.sms_notifier.test_sms_connection()
        
        # Schedule periodic tasks
        self._schedule_tasks()
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        # Send startup notification
        if self.sms_notifier.is_configured():
            self.sms_notifier.send_alert(
                "system", "FINBOT", 
                f"Finance Bot started successfully! Monitoring {len(Config.WATCHLIST)} symbols.",
                "normal"
            )
        
        logger.info("Finance Bot started successfully")
    
    def stop(self):
        """Stop the finance bot"""
        if not self.is_running:
            logger.warning("Bot is not running")
            return
        
        logger.info("Stopping Finance Bot...")
        
        self.scheduler.shutdown()
        self.is_running = False
        
        # Send shutdown notification
        if self.sms_notifier.is_configured():
            self.sms_notifier.send_alert(
                "system", "FINBOT", 
                "Finance Bot has been stopped.",
                "normal"
            )
        
        logger.info("Finance Bot stopped")
    
    def _schedule_tasks(self):
        """Schedule periodic tasks"""
        
        # Real-time trading signals (every minute during market hours)
        self.scheduler.add_job(
            func=self._analyze_watchlist,
            trigger=IntervalTrigger(minutes=Config.UPDATE_INTERVAL_MINUTES),
            id='trading_signals',
            name='Generate Trading Signals'
        )
        
        # Market overview (every 15 minutes)
        self.scheduler.add_job(
            func=self._send_market_overview,
            trigger=IntervalTrigger(minutes=15),
            id='market_overview',
            name='Market Overview Update'
        )
        
        # Daily backtest summary (once per day at market close)
        self.scheduler.add_job(
            func=self._run_daily_backtests,
            trigger='cron',
            hour=16,  # 4 PM ET (market close)
            minute=30,
            id='daily_backtest',
            name='Daily Backtest Summary'
        )
        
        # Performance summary (every hour)
        self.scheduler.add_job(
            func=self._send_performance_summary,
            trigger=IntervalTrigger(hours=1),
            id='performance_summary',
            name='Hourly Performance Summary'
        )
    
    def _analyze_watchlist(self):
        """Analyze all symbols in watchlist and send signals"""
        if not self.data_fetcher.is_market_open():
            logger.info("Market is closed, skipping analysis")
            return
        
        logger.info(f"Analyzing {len(Config.WATCHLIST)} symbols...")
        
        signals_to_send = []
        
        for symbol in Config.WATCHLIST:
            try:
                # Get recent data for analysis
                data = self.data_fetcher.get_historical_data(symbol, period="1mo", interval="1d")
                if data.empty:
                    logger.warning(f"No data available for {symbol}")
                    continue
                
                # Train ML strategies with recent data
                self.strategy_manager.train_ml_strategies(symbol, data)
                
                # Analyze with all strategies
                results = self.strategy_manager.analyze_symbol(symbol, data)
                
                # Get current price
                real_time_data = self.data_fetcher.get_real_time_data(symbol)
                if not real_time_data:
                    continue
                
                current_price = real_time_data['price']
                
                # Focus on composite strategy for main signals
                composite_result = results.get('composite', {})
                signal = composite_result.get('signal', 'HOLD')
                strength = composite_result.get('strength', 0.5)
                
                # Check if this is a new signal (different from last)
                last_signal = self.last_signals.get(symbol, {}).get('signal', 'HOLD')
                
                if signal != 'HOLD' and signal != last_signal:
                    # This is a new actionable signal
                    
                    # Get supporting evidence from other strategies
                    supporting_strategies = [
                        name for name, result in results.items() 
                        if result.get('signal') == signal and name != 'composite'
                    ]
                    
                    additional_info = ""
                    if supporting_strategies:
                        additional_info = f"Supported by: {', '.join(supporting_strategies[:3])}"
                    
                    signal_data = {
                        'symbol': symbol,
                        'signal': signal,
                        'strategy': 'Composite',
                        'price': current_price,
                        'strength': strength,
                        'additional_info': additional_info,
                        'timestamp': datetime.now()
                    }
                    
                    signals_to_send.append(signal_data)
                    
                    # Update signal stats
                    self.signal_stats['total_signals'] += 1
                    
                    # Store signal for comparison
                    self.last_signals[symbol] = {
                        'signal': signal,
                        'price': current_price,
                        'timestamp': datetime.now()
                    }
                    
                    logger.info(f"New signal for {symbol}: {signal} at ${current_price:.2f}")
            
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
        
        # Send signals
        if signals_to_send:
            if len(signals_to_send) == 1:
                signal = signals_to_send[0]
                self.sms_notifier.send_trading_signal(
                    signal['symbol'], signal['signal'], signal['strategy'],
                    signal['price'], signal['strength'], signal['additional_info']
                )
            else:
                self.sms_notifier.send_bulk_signals(signals_to_send)
        
        logger.info(f"Analysis complete. {len(signals_to_send)} new signals generated.")
    
    def _send_market_overview(self):
        """Send market overview update"""
        try:
            market_data = self.data_fetcher.get_market_overview()
            if market_data:
                self.sms_notifier.send_market_update(market_data)
                self.last_market_update = datetime.now()
        except Exception as e:
            logger.error(f"Error sending market overview: {e}")
    
    def _run_daily_backtests(self):
        """Run daily backtests for all watchlist symbols"""
        logger.info("Running daily backtests...")
        
        backtest_results = {}
        
        for symbol in Config.WATCHLIST[:3]:  # Limit to 3 symbols for SMS brevity
            try:
                # Get historical data
                data = self.data_fetcher.get_historical_data(
                    symbol, 
                    period=f"{Config.BACKTESTING_YEARS}y"
                )
                
                if data.empty:
                    continue
                
                # Run comprehensive backtest
                results = self.backtesting_engine.run_comprehensive_backtest(symbol, data)
                backtest_results[symbol] = results
                
                # Find best strategy
                best_strategy_name = max(results.keys(), key=lambda k: results[k].total_return)
                best_result = results[best_strategy_name]
                
                # Send results via SMS
                self.sms_notifier.send_backtest_results(
                    symbol, best_strategy_name,
                    best_result.total_return,
                    best_result.win_rate,
                    best_result.signals_accuracy
                )
                
                time.sleep(2)  # Small delay between SMS messages
                
            except Exception as e:
                logger.error(f"Error backtesting {symbol}: {e}")
        
        logger.info("Daily backtests completed")
    
    def _send_performance_summary(self):
        """Send hourly performance summary"""
        if self.signal_stats['total_signals'] == 0:
            return
        
        accuracy = (self.signal_stats['correct_signals'] / 
                   self.signal_stats['total_signals']) * 100
        
        message = f"""
📊 BOT PERFORMANCE (Last Hour)

Total Signals: {self.signal_stats['total_signals']}
Accuracy: {accuracy:.1f}%
Symbols Monitored: {len(Config.WATCHLIST)}

Last Update: {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        # Reset stats for next hour
        self.signal_stats = {
            'total_signals': 0,
            'correct_signals': 0,
            'by_strategy': {}
        }
        
        if self.sms_notifier.is_configured():
            self.sms_notifier.send_sms(message)
    
    def run_single_backtest(self, symbol: str, strategy: str = None) -> Dict:
        """Run backtest for a single symbol"""
        try:
            data = self.data_fetcher.get_historical_data(symbol, period="2y")
            if data.empty:
                return {"error": f"No data available for {symbol}"}
            
            if strategy:
                result = self.backtesting_engine.run_backtest(symbol, data, strategy)
                return {strategy: result}
            else:
                results = self.backtesting_engine.run_comprehensive_backtest(symbol, data)
                return results
                
        except Exception as e:
            logger.error(f"Error in single backtest for {symbol}: {e}")
            return {"error": str(e)}
    
    def get_current_signals(self) -> Dict:
        """Get current trading signals for all watchlist symbols"""
        current_signals = {}
        
        for symbol in Config.WATCHLIST:
            try:
                data = self.data_fetcher.get_historical_data(symbol, period="1mo")
                if not data.empty:
                    results = self.strategy_manager.analyze_symbol(symbol, data)
                    current_signals[symbol] = results
            except Exception as e:
                logger.error(f"Error getting signals for {symbol}: {e}")
        
        return current_signals
    
    def add_symbol_to_watchlist(self, symbol: str):
        """Add a new symbol to watchlist"""
        if symbol not in Config.WATCHLIST:
            Config.WATCHLIST.append(symbol.upper())
            logger.info(f"Added {symbol} to watchlist")
            
            if self.sms_notifier.is_configured():
                self.sms_notifier.send_alert(
                    "watchlist", symbol,
                    f"Symbol {symbol} added to watchlist",
                    "low"
                )
    
    def remove_symbol_from_watchlist(self, symbol: str):
        """Remove symbol from watchlist"""
        if symbol in Config.WATCHLIST:
            Config.WATCHLIST.remove(symbol.upper())
            logger.info(f"Removed {symbol} from watchlist")
    
    def get_bot_status(self) -> Dict:
        """Get current bot status"""
        return {
            'is_running': self.is_running,
            'watchlist_size': len(Config.WATCHLIST),
            'last_market_update': self.last_market_update,
            'total_signals_today': self.signal_stats['total_signals'],
            'sms_configured': self.sms_notifier.is_configured(),
            'market_open': self.data_fetcher.is_market_open()
        }
    
    def run_manual_analysis(self, symbol: str) -> Dict:
        """Run manual analysis for a specific symbol"""
        try:
            # Get real-time data
            real_time_data = self.data_fetcher.get_real_time_data(symbol)
            
            # Get historical data
            historical_data = self.data_fetcher.get_historical_data(symbol, period="3mo")
            
            if historical_data.empty:
                return {"error": f"No historical data for {symbol}"}
            
            # Train ML strategies
            self.strategy_manager.train_ml_strategies(symbol, historical_data)
            
            # Get signals from all strategies
            signals = self.strategy_manager.analyze_symbol(symbol, historical_data)
            
            # Get news
            news = self.data_fetcher.get_company_news(symbol, limit=3)
            
            return {
                'symbol': symbol,
                'current_data': real_time_data,
                'signals': signals,
                'news': news,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error in manual analysis for {symbol}: {e}")
            return {"error": str(e)}

def main():
    """Main function to run the finance bot"""
    bot = FinanceBot()
    
    try:
        bot.start()
        
        print("\n" + "="*60)
        print("🤖 FINANCE BOT STARTED 🤖")
        print("="*60)
        print(f"📊 Monitoring: {', '.join(Config.WATCHLIST)}")
        print(f"⏰ Update Interval: {Config.UPDATE_INTERVAL_MINUTES} minute(s)")
        print(f"📱 SMS Configured: {'Yes' if bot.sms_notifier.is_configured() else 'No'}")
        print(f"💰 Initial Capital: ${Config.INITIAL_CAPITAL:,.2f}")
        print("="*60)
        print("\nPress Ctrl+C to stop the bot")
        print("="*60)
        
        # Keep the bot running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down Finance Bot...")
        bot.stop()
        print("Finance Bot stopped successfully!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        bot.stop()

if __name__ == "__main__":
    main()