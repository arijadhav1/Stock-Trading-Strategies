from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import logging
from typing import List, Dict, Optional
from datetime import datetime
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSNotifier:
    def __init__(self):
        self.account_sid = Config.TWILIO_ACCOUNT_SID
        self.auth_token = Config.TWILIO_AUTH_TOKEN
        self.phone_number = Config.TWILIO_PHONE_NUMBER
        self.recipients = Config.SMS_RECIPIENTS
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning("Twilio credentials not configured. SMS notifications will be disabled.")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
    
    def send_sms(self, message: str, phone_numbers: Optional[List[str]] = None) -> bool:
        """Send SMS to specified phone numbers or default recipients"""
        if not self.client:
            logger.warning("SMS client not available. Message not sent.")
            return False
        
        recipients = phone_numbers or self.recipients
        if not recipients:
            logger.warning("No SMS recipients configured")
            return False
        
        success_count = 0
        for phone_number in recipients:
            try:
                message_obj = self.client.messages.create(
                    body=message,
                    from_=self.phone_number,
                    to=phone_number
                )
                logger.info(f"SMS sent successfully to {phone_number}: {message_obj.sid}")
                success_count += 1
            except TwilioException as e:
                logger.error(f"Failed to send SMS to {phone_number}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending SMS to {phone_number}: {e}")
        
        return success_count > 0
    
    def send_trading_signal(self, symbol: str, signal: str, strategy: str, 
                           price: float, strength: float, additional_info: str = "") -> bool:
        """Send trading signal notification"""
        
        # Signal emoji mapping
        signal_emojis = {
            'BUY': '🟢📈',
            'SELL': '🔴📉',
            'HOLD': '🟡⏸️'
        }
        
        emoji = signal_emojis.get(signal, '⚪')
        strength_bar = self._get_strength_bar(strength)
        
        message = f"""
{emoji} TRADING SIGNAL {emoji}

Symbol: {symbol}
Signal: {signal}
Strategy: {strategy}
Price: ${price:.2f}
Strength: {strength_bar} ({strength:.0%})

{additional_info}

Time: {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_sms(message)
    
    def send_market_update(self, market_data: Dict[str, Dict]) -> bool:
        """Send market overview update"""
        message = "📊 MARKET OVERVIEW 📊\n\n"
        
        for symbol, data in market_data.items():
            change_emoji = "🟢" if data['change_percent'] > 0 else "🔴" if data['change_percent'] < 0 else "⚪"
            message += f"{change_emoji} {data['name']}: ${data['price']:.2f} ({data['change_percent']:+.2f}%)\n"
        
        message += f"\nTime: {datetime.now().strftime('%H:%M:%S')}"
        
        return self.send_sms(message)
    
    def send_backtest_results(self, symbol: str, best_strategy: str, 
                            total_return: float, win_rate: float, 
                            signals_accuracy: float) -> bool:
        """Send backtest results summary"""
        
        return_emoji = "🎉" if total_return > 0 else "😞"
        
        message = f"""
{return_emoji} BACKTEST RESULTS {return_emoji}

Symbol: {symbol}
Best Strategy: {best_strategy}

📈 Total Return: {total_return:.2%}
🎯 Win Rate: {win_rate:.2%}
🔍 Signal Accuracy: {signals_accuracy:.2%}

Time: {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_sms(message)
    
    def send_portfolio_update(self, portfolio_value: float, daily_change: float, 
                            top_performers: List[Dict]) -> bool:
        """Send portfolio performance update"""
        
        change_emoji = "🟢" if daily_change > 0 else "🔴" if daily_change < 0 else "⚪"
        
        message = f"""
💼 PORTFOLIO UPDATE 💼

Total Value: ${portfolio_value:,.2f}
Daily Change: {change_emoji} {daily_change:+.2f}%

🏆 Top Performers:
        """
        
        for performer in top_performers[:3]:
            message += f"• {performer['symbol']}: {performer['return']:+.2f}%\n"
        
        message += f"\nTime: {datetime.now().strftime('%H:%M:%S')}"
        
        return self.send_sms(message)
    
    def send_alert(self, alert_type: str, symbol: str, message_text: str, 
                   urgency: str = "normal") -> bool:
        """Send custom alert"""
        
        urgency_emojis = {
            "low": "ℹ️",
            "normal": "⚠️",
            "high": "🚨",
            "critical": "🔥"
        }
        
        emoji = urgency_emojis.get(urgency, "⚠️")
        
        message = f"""
{emoji} {alert_type.upper()} ALERT {emoji}

Symbol: {symbol}
{message_text}

Time: {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_sms(message)
    
    def send_news_alert(self, symbol: str, news_title: str, sentiment: str = "neutral") -> bool:
        """Send news alert for a stock"""
        
        sentiment_emojis = {
            "positive": "📰✅",
            "negative": "📰❌",
            "neutral": "📰ℹ️"
        }
        
        emoji = sentiment_emojis.get(sentiment, "📰")
        
        message = f"""
{emoji} NEWS ALERT {emoji}

Symbol: {symbol}
{news_title}

Time: {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_sms(message)
    
    def send_bulk_signals(self, signals: List[Dict]) -> bool:
        """Send multiple trading signals in one message"""
        if not signals:
            return False
        
        message = "🔔 MULTIPLE SIGNALS 🔔\n\n"
        
        for signal in signals[:5]:  # Limit to 5 signals to avoid SMS length limits
            emoji = "🟢" if signal['signal'] == 'BUY' else "🔴" if signal['signal'] == 'SELL' else "🟡"
            message += f"{emoji} {signal['symbol']}: {signal['signal']} (${signal['price']:.2f})\n"
        
        if len(signals) > 5:
            message += f"... and {len(signals) - 5} more signals\n"
        
        message += f"\nTime: {datetime.now().strftime('%H:%M:%S')}"
        
        return self.send_sms(message)
    
    def _get_strength_bar(self, strength: float) -> str:
        """Generate visual strength indicator"""
        filled_bars = int(strength * 5)
        return "█" * filled_bars + "░" * (5 - filled_bars)
    
    def test_sms_connection(self) -> bool:
        """Test SMS functionality"""
        test_message = f"""
🧪 Finance Bot Test Message 🧪

This is a test message from your Finance Bot.
If you receive this, SMS notifications are working correctly!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return self.send_sms(test_message)
    
    def add_recipient(self, phone_number: str) -> bool:
        """Add a new SMS recipient"""
        if phone_number not in self.recipients:
            self.recipients.append(phone_number)
            logger.info(f"Added new SMS recipient: {phone_number}")
            return True
        return False
    
    def remove_recipient(self, phone_number: str) -> bool:
        """Remove an SMS recipient"""
        if phone_number in self.recipients:
            self.recipients.remove(phone_number)
            logger.info(f"Removed SMS recipient: {phone_number}")
            return True
        return False
    
    def get_recipients(self) -> List[str]:
        """Get list of current SMS recipients"""
        return self.recipients.copy()
    
    def is_configured(self) -> bool:
        """Check if SMS is properly configured"""
        return self.client is not None and len(self.recipients) > 0