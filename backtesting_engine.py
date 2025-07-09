import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from trading_strategies import TradingStrategy, StrategyManager
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Trade:
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    trade_type: str  # 'BUY' or 'SELL'
    strategy: str
    symbol: str
    profit_loss: Optional[float] = None
    is_open: bool = True

@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    avg_trade_duration: float
    profit_factor: float
    total_fees: float
    net_profit: float
    signals_accuracy: float
    trades: List[Trade]
    equity_curve: pd.Series
    
class BacktestingEngine:
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission  # 0.1% commission per trade
        self.strategy_manager = StrategyManager()
        
    def run_backtest(self, symbol: str, data: pd.DataFrame, strategy_name: str, 
                    start_date: Optional[str] = None, end_date: Optional[str] = None) -> BacktestResult:
        """Run backtest for a specific strategy"""
        
        # Filter data by date range if provided
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
            
        if len(data) < 50:
            logger.warning(f"Insufficient data for backtesting {symbol} with {strategy_name}")
            return self._create_empty_result(strategy_name, symbol)
        
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if not strategy:
            logger.error(f"Strategy {strategy_name} not found")
            return self._create_empty_result(strategy_name, symbol)
        
        # Train ML strategies if needed
        if strategy_name == 'ml_rf':
            self.strategy_manager.train_ml_strategies(symbol, data)
        
        # Initialize tracking variables
        trades = []
        capital = self.initial_capital
        position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        entry_date = None
        equity_curve = []
        
        signals_correct = 0
        total_signals = 0
        
        # Run through data
        for i in range(50, len(data)):  # Start from index 50 to have enough history
            current_data = data.iloc[:i+1]
            current_price = current_data['Close'].iloc[-1]
            current_date = current_data.index[-1]
            
            # Generate signal
            signal = strategy.generate_signal(current_data)
            
            # Track signal accuracy
            if i < len(data) - 1:
                next_price = data['Close'].iloc[i+1]
                if signal == 'BUY' and next_price > current_price:
                    signals_correct += 1
                elif signal == 'SELL' and next_price < current_price:
                    signals_correct += 1
                elif signal == 'HOLD':
                    signals_correct += 1  # Neutral signal is considered correct
                total_signals += 1
            
            # Execute trades based on signals
            if signal == 'BUY' and position <= 0:
                # Close short position if exists
                if position == -1:
                    trade = self._close_position(trades[-1], current_price, current_date)
                    capital += trade.profit_loss
                
                # Open long position
                quantity = int(capital * 0.95 / current_price)  # Use 95% of capital
                if quantity > 0:
                    trade = Trade(
                        entry_date=current_date,
                        exit_date=None,
                        entry_price=current_price,
                        exit_price=None,
                        quantity=quantity,
                        trade_type='BUY',
                        strategy=strategy_name,
                        symbol=symbol
                    )
                    trades.append(trade)
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    capital -= quantity * current_price * (1 + self.commission)
            
            elif signal == 'SELL' and position >= 0:
                # Close long position if exists
                if position == 1:
                    trade = self._close_position(trades[-1], current_price, current_date)
                    capital += trade.profit_loss
                    position = 0
            
            # Calculate current equity
            if position == 1 and trades:
                unrealized_pnl = (current_price - trades[-1].entry_price) * trades[-1].quantity
                current_equity = capital + unrealized_pnl
            else:
                current_equity = capital
            
            equity_curve.append(current_equity)
        
        # Close any remaining open positions
        if trades and trades[-1].is_open:
            final_price = data['Close'].iloc[-1]
            final_date = data.index[-1]
            self._close_position(trades[-1], final_price, final_date)
        
        # Calculate performance metrics
        return self._calculate_metrics(strategy_name, symbol, trades, equity_curve, 
                                     signals_correct, total_signals)
    
    def _close_position(self, trade: Trade, exit_price: float, exit_date: datetime) -> Trade:
        """Close an open trade"""
        trade.exit_price = exit_price
        trade.exit_date = exit_date
        trade.is_open = False
        
        if trade.trade_type == 'BUY':
            trade.profit_loss = (exit_price - trade.entry_price) * trade.quantity
        else:  # SHORT
            trade.profit_loss = (trade.entry_price - exit_price) * trade.quantity
        
        # Subtract commission
        total_commission = (trade.entry_price + exit_price) * trade.quantity * self.commission
        trade.profit_loss -= total_commission
        
        return trade
    
    def _calculate_metrics(self, strategy_name: str, symbol: str, trades: List[Trade], 
                          equity_curve: List[float], signals_correct: int, 
                          total_signals: int) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        
        if not trades:
            return self._create_empty_result(strategy_name, symbol)
        
        # Basic trade statistics
        closed_trades = [t for t in trades if not t.is_open]
        total_trades = len(closed_trades)
        
        if total_trades == 0:
            return self._create_empty_result(strategy_name, symbol)
        
        profits = [t.profit_loss for t in closed_trades if t.profit_loss > 0]
        losses = [t.profit_loss for t in closed_trades if t.profit_loss < 0]
        
        winning_trades = len(profits)
        losing_trades = len(losses)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Financial metrics
        total_profit = sum(profits) if profits else 0
        total_loss = sum(losses) if losses else 0
        net_profit = total_profit + total_loss
        total_return = net_profit / self.initial_capital
        
        # Risk metrics
        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()
        
        sharpe_ratio = 0
        if len(returns) > 1 and returns.std() != 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)  # Annualized
        
        # Maximum drawdown
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        max_drawdown = drawdown.min()
        
        # Trade duration
        trade_durations = []
        for trade in closed_trades:
            if trade.exit_date and trade.entry_date:
                duration = (trade.exit_date - trade.entry_date).days
                trade_durations.append(duration)
        
        avg_trade_duration = np.mean(trade_durations) if trade_durations else 0
        
        # Profit factor
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0
        
        # Total fees
        total_fees = sum([(t.entry_price + (t.exit_price or 0)) * t.quantity * self.commission 
                         for t in closed_trades])
        
        # Signal accuracy
        signals_accuracy = signals_correct / total_signals if total_signals > 0 else 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            avg_trade_duration=avg_trade_duration,
            profit_factor=profit_factor,
            total_fees=total_fees,
            net_profit=net_profit,
            signals_accuracy=signals_accuracy,
            trades=closed_trades,
            equity_curve=equity_series
        )
    
    def _create_empty_result(self, strategy_name: str, symbol: str) -> BacktestResult:
        """Create empty result for failed backtests"""
        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            avg_trade_duration=0.0,
            profit_factor=0.0,
            total_fees=0.0,
            net_profit=0.0,
            signals_accuracy=0.0,
            trades=[],
            equity_curve=pd.Series([])
        )
    
    def run_comprehensive_backtest(self, symbol: str, data: pd.DataFrame) -> Dict[str, BacktestResult]:
        """Run backtest for all strategies"""
        results = {}
        strategies = self.strategy_manager.get_all_strategies()
        
        for strategy_name in strategies.keys():
            try:
                result = self.run_backtest(symbol, data, strategy_name)
                results[strategy_name] = result
                logger.info(f"Completed backtest for {symbol} - {strategy_name}: "
                          f"Return: {result.total_return:.2%}, Win Rate: {result.win_rate:.2%}")
            except Exception as e:
                logger.error(f"Error backtesting {symbol} with {strategy_name}: {e}")
                results[strategy_name] = self._create_empty_result(strategy_name, symbol)
        
        return results
    
    def compare_strategies(self, results: Dict[str, BacktestResult]) -> pd.DataFrame:
        """Compare strategy performance"""
        comparison_data = []
        
        for strategy_name, result in results.items():
            comparison_data.append({
                'Strategy': strategy_name,
                'Total Return': f"{result.total_return:.2%}",
                'Win Rate': f"{result.win_rate:.2%}",
                'Signal Accuracy': f"{result.signals_accuracy:.2%}",
                'Total Trades': result.total_trades,
                'Sharpe Ratio': f"{result.sharpe_ratio:.2f}",
                'Max Drawdown': f"{result.max_drawdown:.2%}",
                'Profit Factor': f"{result.profit_factor:.2f}",
                'Net Profit': f"${result.net_profit:.2f}",
                'Avg Trade Duration': f"{result.avg_trade_duration:.1f} days"
            })
        
        df = pd.DataFrame(comparison_data)
        return df.sort_values('Total Return', ascending=False)
    
    def generate_backtest_report(self, symbol: str, results: Dict[str, BacktestResult]) -> str:
        """Generate comprehensive backtest report"""
        report = f"\n{'='*80}\n"
        report += f"BACKTESTING REPORT FOR {symbol}\n"
        report += f"{'='*80}\n"
        report += f"Initial Capital: ${self.initial_capital:,.2f}\n"
        report += f"Commission: {self.commission:.3%} per trade\n"
        report += f"Test Period: {len(list(results.values())[0].equity_curve)} periods\n\n"
        
        # Strategy comparison table
        comparison_df = self.compare_strategies(results)
        report += "STRATEGY PERFORMANCE COMPARISON:\n"
        report += "-" * 80 + "\n"
        report += comparison_df.to_string(index=False)
        report += "\n\n"
        
        # Best performing strategy details
        best_strategy = max(results.values(), key=lambda x: x.total_return)
        report += f"BEST PERFORMING STRATEGY: {best_strategy.strategy_name}\n"
        report += "-" * 50 + "\n"
        report += f"Total Return: {best_strategy.total_return:.2%}\n"
        report += f"Win Rate: {best_strategy.win_rate:.2%}\n"
        report += f"Signal Accuracy: {best_strategy.signals_accuracy:.2%}\n"
        report += f"Sharpe Ratio: {best_strategy.sharpe_ratio:.2f}\n"
        report += f"Maximum Drawdown: {best_strategy.max_drawdown:.2%}\n"
        report += f"Profit Factor: {best_strategy.profit_factor:.2f}\n"
        report += f"Total Trades: {best_strategy.total_trades}\n"
        report += f"Average Trade Duration: {best_strategy.avg_trade_duration:.1f} days\n"
        
        return report