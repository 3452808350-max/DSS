#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎胶水层 - 标准化回测接口
基于Vibe Coding方法论：每个策略可独立提示修改

运行方式:
    python glue_backtest.py
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Trade:
    """交易记录"""
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    direction: str  # 'long' or 'short'
    size: float
    pnl: Optional[float] = None
    return_pct: Optional[float] = None

@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    num_trades: int
    trades: List[Trade]
    equity_curve: pd.DataFrame

class Strategy(ABC):
    """
    策略基类（Vibe Coding友好设计）
    
    可通过自然语言提示AI修改：
    - "修改均线策略的周期为30日"
    - "添加止损逻辑到策略中"
    """
    
    def __init__(self, **params):
        self.params = params
        self.name = self.__class__.__name__
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            df: 标准化DataFrame (date, open, close, high, low, volume)
        
        Returns:
            添加了signal列的DataFrame (1:买入, -1:卖出, 0:持有)
        """
        pass
    
    def on_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据处理钩子（可重写）"""
        return df

class SmaStrategy(Strategy):
    """简单均线策略"""
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        super().__init__(fast_period=fast_period, slow_period=slow_period)
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """MA5上穿MA20买入，下穿卖出"""
        df = df.copy()
        df['fast_ma'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_period).mean()
        
        df['signal'] = 0
        df.loc[df['fast_ma'] > df['slow_ma'], 'signal'] = 1
        df.loc[df['fast_ma'] < df['slow_ma'], 'signal'] = -1
        
        return df

class RsiStrategy(Strategy):
    """RSI策略"""
    
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        super().__init__(period=period, overbought=overbought, oversold=oversold)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI超卖买入，超买卖出"""
        df = df.copy()
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['signal'] = 0
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1
        
        return df

class MomentumStrategy(Strategy):
    """动量策略"""
    
    def __init__(self, lookback: int = 20, threshold: float = 0.05):
        super().__init__(lookback=lookback, threshold=threshold)
        self.lookback = lookback
        self.threshold = threshold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """N日涨幅超过阈值买入，低于负阈值卖出"""
        df = df.copy()
        df['momentum'] = df['close'].pct_change(periods=self.lookback)
        
        df['signal'] = 0
        df.loc[df['momentum'] > self.threshold, 'signal'] = 1
        df.loc[df['momentum'] < -self.threshold, 'signal'] = -1
        
        return df

class BacktestEngine:
    """
    回测引擎（胶水代码）
    
    可通过自然语言提示AI修改：
    - "添加滑点模型到回测引擎"
    - "修改手续费率为万分之三"
    """
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 commission: float = 0.001,  # 千分之一手续费
                 slippage: float = 0.001):   # 千分之一滑点
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
    
    def run(self, df: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        """
        执行回测
        
        Args:
            df: 标准化DataFrame
            strategy: 策略实例
        
        Returns:
            回测结果
        """
        # 生成信号
        df = strategy.generate_signals(df)
        df = df.dropna()
        
        # 初始化
        capital = self.initial_capital
        position = 0
        trades = []
        equity_curve = []
        
        current_trade = None
        
        for i, row in df.iterrows():
            signal = row['signal']
            price = row['close']
            date = row['date'] if isinstance(row['date'], datetime) else pd.to_datetime(row['date'])
            
            # 记录权益
            current_value = capital + position * price
            equity_curve.append({
                'date': date,
                'equity': current_value,
                'signal': signal
            })
            
            # 交易逻辑
            if signal == 1 and position == 0:  # 买入信号
                # 计算买入数量（全仓）
                buy_price = price * (1 + self.slippage)
                position = capital * (1 - self.commission) / buy_price
                capital = 0
                
                current_trade = Trade(
                    entry_date=date,
                    exit_date=None,
                    entry_price=buy_price,
                    exit_price=None,
                    direction='long',
                    size=position
                )
            
            elif signal == -1 and position > 0:  # 卖出信号
                # 卖出
                sell_price = price * (1 - self.slippage)
                capital = position * sell_price * (1 - self.commission)
                
                # 记录交易
                pnl = position * (sell_price - current_trade.entry_price)
                return_pct = (sell_price - current_trade.entry_price) / current_trade.entry_price
                
                current_trade.exit_date = date
                current_trade.exit_price = sell_price
                current_trade.pnl = pnl
                current_trade.return_pct = return_pct
                trades.append(current_trade)
                
                position = 0
                current_trade = None
        
        # 计算最终价值
        final_value = capital + position * df['close'].iloc[-1]
        
        # 计算绩效指标
        return self._calculate_metrics(
            strategy_name=strategy.name,
            df=df,
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=self.initial_capital,
            final_value=final_value
        )
    
    def _calculate_metrics(self, 
                          strategy_name: str,
                          df: pd.DataFrame,
                          trades: List[Trade],
                          equity_curve: List[Dict],
                          initial_capital: float,
                          final_value: float) -> BacktestResult:
        """计算绩效指标"""
        equity_df = pd.DataFrame(equity_curve)
        equity_df.set_index('date', inplace=True)
        
        # 基本指标
        total_return = (final_value - initial_capital) / initial_capital
        days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
        annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        # 夏普比率（简化版，假设无风险利率为0）
        returns = equity_df['equity'].pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0
        
        # 最大回撤
        cummax = equity_df['equity'].cummax()
        drawdown = (equity_df['equity'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 交易统计
        if trades:
            winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl and t.pnl <= 0]
            
            win_rate = len(winning_trades) / len(trades) if trades else 0
            
            total_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
            total_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 1e-10
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        else:
            win_rate = 0
            profit_factor = 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=df['date'].iloc[0],
            end_date=df['date'].iloc[-1],
            initial_capital=initial_capital,
            final_value=final_value,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            num_trades=len(trades),
            trades=trades,
            equity_curve=equity_df
        )

def print_backtest_report(result: BacktestResult):
    """打印回测报告"""
    print("=" * 60)
    print(f"📊 回测报告: {result.strategy_name}")
    print("=" * 60)
    print(f"回测区间: {result.start_date.strftime('%Y-%m-%d')} 至 {result.end_date.strftime('%Y-%m-%d')}")
    print(f"初始资金: {result.initial_capital:,.2f}")
    print(f"最终资金: {result.final_value:,.2f}")
    print("-" * 60)
    print(f"总收益率: {result.total_return*100:.2f}%")
    print(f"年化收益: {result.annual_return*100:.2f}%")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"最大回撤: {result.max_drawdown*100:.2f}%")
    print("-" * 60)
    print(f"交易次数: {result.num_trades}")
    print(f"胜率: {result.win_rate*100:.2f}%")
    print(f"盈亏比: {result.profit_factor:.2f}")
    print("=" * 60)

# 验证检查点
if __name__ == "__main__":
    print("=" * 60)
    print("回测引擎胶水层 - 验证测试")
    print("=" * 60)
    
    # 创建测试数据
    np.random.seed(42)
    test_data = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=252, freq='D'),
        'open': 100 + np.cumsum(np.random.randn(252) * 0.5),
        'close': 100 + np.cumsum(np.random.randn(252) * 0.5),
        'high': 100 + np.cumsum(np.random.randn(252) * 0.5),
        'low': 100 + np.cumsum(np.random.randn(252) * 0.5),
        'volume': np.random.randint(1000000, 10000000, 252)
    })
    # 确保价格合理性
    test_data['high'] = np.maximum(test_data['high'], test_data[['open', 'close']].max(axis=1))
    test_data['low'] = np.minimum(test_data['low'], test_data[['open', 'close']].min(axis=1))
    
    engine = BacktestEngine(initial_capital=100000.0)
    
    # 测试1：均线策略
    print("\n📈 测试1: 均线策略回测")
    sma_strategy = SmaStrategy(fast_period=5, slow_period=20)
    result = engine.run(test_data, sma_strategy)
    print_backtest_report(result)
    
    # 测试2：RSI策略
    print("\n📈 测试2: RSI策略回测")
    rsi_strategy = RsiStrategy(period=14, overbought=70, oversold=30)
    result = engine.run(test_data, rsi_strategy)
    print_backtest_report(result)
    
    # 测试3：动量策略
    print("\n📈 测试3: 动量策略回测")
    mom_strategy = MomentumStrategy(lookback=20, threshold=0.05)
    result = engine.run(test_data, mom_strategy)
    print_backtest_report(result)
    
    # 测试4：策略对比
    print("\n📊 测试4: 策略对比")
    strategies = [
        ('均线策略', SmaStrategy(5, 20)),
        ('RSI策略', RsiStrategy(14, 70, 30)),
        ('动量策略', MomentumStrategy(20, 0.05))
    ]
    
    print("\n策略对比表:")
    print("-" * 80)
    print(f"{'策略':15s} {'总收益':>10s} {'年化收益':>10s} {'夏普':>8s} {'最大回撤':>10s} {'交易次数':>8s}")
    print("-" * 80)
    
    for name, strategy in strategies:
        result = engine.run(test_data, strategy)
        print(f"{name:15s} {result.total_return*100:>9.2f}% {result.annual_return*100:>9.2f}% "
              f"{result.sharpe_ratio:>8.2f} {result.max_drawdown*100:>9.2f}% {result.num_trades:>8d}")
    
    print("-" * 80)
    
    print("\n" + "=" * 60)
    print("✅ 所有验证测试完成")
    print("=" * 60)
