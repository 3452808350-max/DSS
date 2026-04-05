#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略回测框架
基于Vibe Coding方法论

功能:
- 多种策略支持 (均线交叉、动量、双均线)
- 绩效指标计算
- 可视化报告

运行方式:
    python backtest_engine.py --symbol 000001 --strategy sma
    python backtest_engine.py --symbol 000001 --strategy momentum
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import argparse

PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = PROJECT_ROOT / "database" / "stocks.db"


@dataclass
class Trade:
    """交易记录"""
    entry_date: str
    exit_date: Optional[str]
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
    symbol: str
    start_date: str
    end_date: str
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


class Strategy:
    """策略基类"""
    
    def __init__(self, **params):
        self.params = params
        self.name = self.__class__.__name__
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        raise NotImplementedError


class SmaCrossStrategy(Strategy):
    """均线交叉策略"""
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        super().__init__(fast_period=fast_period, slow_period=slow_period)
        self.fast = fast_period
        self.slow = slow_period
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """金叉买入，死叉卖出"""
        df = df.copy()
        
        # 计算均线
        df['fast_ma'] = df['close'].rolling(window=self.fast).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow).mean()
        
        # 生成信号
        df['signal'] = 0
        df.loc[df['fast_ma'] > df['slow_ma'], 'signal'] = 1  # 持有
        df.loc[df['fast_ma'] <= df['slow_ma'], 'signal'] = -1  # 空仓
        
        # 计算交叉点
        df['cross'] = df['signal'].diff()
        
        return df


class MomentumStrategy(Strategy):
    """动量策略"""
    
    def __init__(self, period: int = 20, threshold: float = 0.02):
        super().__init__(period=period, threshold=threshold)
        self.period = period
        self.threshold = threshold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """动量突破买入"""
        df = df.copy()
        
        # 计算动量
        df['momentum'] = df['close'].pct_change(self.period)
        
        # 生成信号
        df['signal'] = 0
        df.loc[df['momentum'] > self.threshold, 'signal'] = 1
        df.loc[df['momentum'] < -self.threshold, 'signal'] = -1
        
        return df


class MeanReversionStrategy(Strategy):
    """均值回归策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(period=period, std_dev=std_dev)
        self.period = period
        self.std_dev = std_dev
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """价格偏离均线太多时反向交易"""
        df = df.copy()
        
        df['ma'] = df['close'].rolling(window=self.period).mean()
        df['std'] = df['close'].rolling(window=self.period).std()
        
        df['upper'] = df['ma'] + df['std'] * self.std_dev
        df['lower'] = df['ma'] - df['std'] * self.std_dev
        
        df['signal'] = 0
        df.loc[df['close'] < df['lower'], 'signal'] = 1  # 超卖买入
        df.loc[df['close'] > df['upper'], 'signal'] = -1  # 超卖卖出
        
        return df


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
    
    def load_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """加载数据"""
        # 处理股票代码格式
        code_query = symbol
        if not symbol.startswith('sh.') and not symbol.startswith('sz.'):
            if symbol.startswith('6'):
                code_query = f"sh.{symbol}"
            else:
                code_query = f"sz.{symbol}"
        
        conn = sqlite3.connect(str(DB_PATH))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = pd.read_sql(f"""
            SELECT date, code, open, high, low, close, volume
            FROM daily_prices 
            WHERE code = '{code_query}'
            AND date >= '{start_date.strftime('%Y-%m-%d')}'
            ORDER BY date
        """, conn)
        conn.close()
        
        # 转换类型
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def run(self, df: pd.DataFrame, strategy: Strategy, 
            initial_capital: float = None) -> BacktestResult:
        """
        运行回测
        
        Args:
            df: 数据
            strategy: 策略
            initial_capital: 初始资金
        
        Returns:
            BacktestResult
        """
        if initial_capital is None:
            initial_capital = self.initial_capital
        
        # 生成信号
        df = strategy.generate_signals(df)
        
        # 初始化
        cash = initial_capital
        shares = 0
        position = False
        equity = []
        trades = []
        entry_price = 0
        entry_date = None
        
        # 模拟交易
        for i, row in df.iterrows():
            if pd.isna(row.get('signal', 0)):
                equity.append(cash + shares * row['close'])
                continue
            
            signal = row['signal']
            
            # 买入
            if signal == 1 and not position:
                shares = cash / row['close']
                cash = 0
                position = True
                entry_price = row['close']
                entry_date = row['date']
            
            # 卖出
            elif signal == -1 and position:
                cash = shares * row['close']
                pnl = cash - initial_capital
                
                trades.append(Trade(
                    entry_date=entry_date,
                    exit_date=row['date'],
                    entry_price=entry_price,
                    exit_price=row['close'],
                    direction='long',
                    size=shares,
                    pnl=pnl,
                    return_pct=pnl / initial_capital * 100
                ))
                
                shares = 0
                position = False
            
            # 记录权益
            equity.append(cash + shares * row['close'])
        
        # 最终权益
        final_value = cash + shares * df['close'].iloc[-1]
        
        # 计算绩效指标
        total_return = (final_value - initial_capital) / initial_capital
        
        # 年化收益率
        days = len(df)
        annual_return = (1 + total_return) ** (252 / days) - 1
        
        # 夏普比率 (简化)
        returns = pd.Series(equity).pct_change().dropna()
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # 最大回撤
        equity_series = pd.Series(equity)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 胜率
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        # 盈利因子
        total_profit = sum(t.pnl for t in trades if t.pnl and t.pnl > 0)
        total_loss = abs(sum(t.pnl for t in trades if t.pnl and t.pnl < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # 权益曲线
        equity_curve = df[['date']].copy()
        equity_curve['equity'] = equity[:len(df)]
        
        return BacktestResult(
            strategy_name=strategy.name,
            symbol=df['code'].iloc[0] if 'code' in df.columns else 'unknown',
            start_date=df['date'].iloc[0],
            end_date=df['date'].iloc[-1],
            initial_capital=initial_capital,
            final_value=final_value,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            num_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )
    
    def print_report(self, result: BacktestResult):
        """打印回测报告"""
        print("=" * 60)
        print(f"📊 回测报告: {result.symbol} - {result.strategy_name}")
        print("=" * 60)
        print(f"📅 周期: {result.start_date} ~ {result.end_date}")
        print(f"💰 初始资金: ¥{result.initial_capital:,.2f}")
        print(f"💵 最终资金: ¥{result.final_value:,.2f}")
        print()
        print(f"📈 总收益率: {result.total_return:+.2%}")
        print(f"📈 年化收益率: {result.annual_return:+.2%}")
        print(f"📉 夏普比率: {result.sharpe_ratio:.2f}")
        print(f"📉 最大回撤: {result.max_drawdown:.2%}")
        print()
        print(f"🎯 交易次数: {result.num_trades}")
        print(f"✅ 胜率: {result.win_rate:.1%}")
        print(f"💎 盈利因子: {result.profit_factor:.2f}")
        print("=" * 60)
    
    def plot_results(self, result: BacktestResult, save_path: str = None):
        """绘制结果图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # 处理股票代码格式
        code_query = result.symbol
        if not result.symbol.startswith('sh.') and not result.symbol.startswith('sz.'):
            if result.symbol.startswith('6'):
                code_query = f"sh.{result.symbol}"
            else:
                code_query = f"sz.{result.symbol}"
        
        # 读取原始数据
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql(f"""
            SELECT date, close FROM daily_prices 
            WHERE code = '{code_query}'
            ORDER BY date
        """, conn)
        conn.close()
        
        # 价格曲线
        ax1.plot(df['date'], df['close'], label='Price', alpha=0.7)
        ax1.set_title(f"{result.symbol} Price & Signals")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 权益曲线
        ax2.plot(result.equity_curve['date'], result.equity_curve['equity'], 
                 label='Equity', color='green')
        ax2.axhline(y=result.initial_capital, color='red', linestyle='--', 
                   label='Initial Capital')
        ax2.set_title("Equity Curve")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100)
            print(f"📊 图表已保存: {save_path}")
        
        plt.close()


def test():
    """测试回测引擎"""
    print("🧪 测试回测引擎...")
    print("=" * 60)
    
    engine = BacktestEngine(initial_capital=100000)
    
    # 加载数据
    df = engine.load_data('000001', days=365)
    print(f"📊 加载数据: {len(df)} 条")
    
    if len(df) == 0:
        print("❌ 无数据，请先运行数据采集")
        return
    
    # 测试均线策略
    print("\n📌 测试均线交叉策略:")
    strategy = SmaCrossStrategy(fast_period=5, slow_period=20)
    result = engine.run(df, strategy)
    engine.print_report(result)
    engine.plot_results(result, '/tmp/backtest_sma.png')
    
    # 测试动量策略
    print("\n📌 测试动量策略:")
    strategy = MomentumStrategy(period=20, threshold=0.02)
    result = engine.run(df, strategy)
    engine.print_report(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='回测引擎')
    parser.add_argument('--symbol', type=str, default='000001', help='股票代码')
    parser.add_argument('--strategy', type=str, default='sma', 
                       choices=['sma', 'momentum', 'meanreversion'],
                       help='策略类型')
    parser.add_argument('--days', type=int, default=365, help='回测天数')
    parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    
    args = parser.parse_args()
    
    engine = BacktestEngine(initial_capital=args.capital)
    
    # 加载数据
    df = engine.load_data(args.symbol, args.days)
    
    if len(df) == 0:
        print(f"❌ 无数据: {args.symbol}")
        print("请先运行: python data_collector.py --update-daily")
    else:
        # 选择策略
        if args.strategy == 'sma':
            strategy = SmaCrossStrategy()
        elif args.strategy == 'momentum':
            strategy = MomentumStrategy()
        elif args.strategy == 'meanreversion':
            strategy = MeanReversionStrategy()
        
        # 运行回测
        result = engine.run(df, strategy)
        engine.print_report(result)
        
        # 保存图表
        chart_path = f'/tmp/backtest_{args.symbol}_{args.strategy}.png'
        engine.plot_results(result, chart_path)
