#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MVP: 纯A股研究的最小可行产品
基于Vibe Coding方法论 - 1小时内可运行的端到端示例

运行方式:
    python mvp_a股研究.py

预期输出:
    - 获取到 XX 条数据
    - 均线计算完成
    - 买入信号: X 次
    - 卖出信号: X 次
    - 图表已保存: mvp_chart.png
"""

import akshare as ak
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 无GUI环境使用
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def fetch_stock_data(symbol: str = "000001", days: int = 90) -> pd.DataFrame:
    """
    获取股票历史数据（胶水代码：连接AKShare与本地分析）
    
    Args:
        symbol: 股票代码，如 "000001"
        days: 获取天数
    
    Returns:
        DataFrame with columns: date, open, close, high, low, volume
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"  正在获取 {symbol} 从 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} 的数据...")
    
    # 胶水层：调用AKShare，标准化输出
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
        adjust="qfq"  # 前复权
    )
    
    # 标准化列名（胶水转换）
    df = df.rename(columns={
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume'
    })
    df['date'] = pd.to_datetime(df['date'])
    
    return df[['date', 'open', 'close', 'high', 'low', 'volume']]

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算技术指标（胶水代码）
    
    Args:
        df: 标准化DataFrame
    
    Returns:
        添加了技术指标的DataFrame
    """
    # 计算均线
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    
    # 计算MACD（简化版）
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成交易信号（胶水代码）
    
    策略：MA5上穿MA20买入，下穿卖出
    
    Args:
        df: 包含技术指标的DataFrame
    
    Returns:
        添加了交易信号的DataFrame
    """
    df['signal'] = 0
    
    # 买入信号：MA5 > MA20
    df.loc[df['MA5'] > df['MA20'], 'signal'] = 1
    
    # 卖出信号：MA5 < MA20
    df.loc[df['MA5'] < df['MA20'], 'signal'] = -1
    
    # 检测交叉点（信号变化）
    df['signal_change'] = df['signal'].diff().fillna(0)
    
    return df

def visualize_results(df: pd.DataFrame, symbol: str, output_file: str = 'mvp_chart.png'):
    """
    可视化结果（胶水代码）
    
    Args:
        df: 包含信号的数据
        symbol: 股票代码
        output_file: 输出文件路径
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # 主图：价格和均线
    ax1 = axes[0]
    ax1.plot(df['date'], df['close'], label='收盘价', alpha=0.8, linewidth=1.5)
    ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.7, linewidth=1)
    ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.7, linewidth=1)
    
    # 标记买入/卖出信号
    buy_signals = df[df['signal_change'] == 2]  # 从-1变为1
    sell_signals = df[df['signal_change'] == -2]  # 从1变为-1
    
    ax1.scatter(buy_signals['date'], buy_signals['close'], 
                color='red', marker='^', s=100, label='买入信号', zorder=5)
    ax1.scatter(sell_signals['date'], sell_signals['close'], 
                color='green', marker='v', s=100, label='卖出信号', zorder=5)
    
    ax1.set_title(f'{symbol} - 均线策略分析', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 成交量
    ax2 = axes[1]
    colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] else 'green' 
              for i in range(len(df))]
    ax2.bar(df['date'], df['volume'], color=colors, alpha=0.6)
    ax2.set_ylabel('成交量')
    ax2.grid(True, alpha=0.3)
    
    # MACD
    ax3 = axes[2]
    ax3.plot(df['date'], df['MACD'], label='MACD', linewidth=1)
    ax3.plot(df['date'], df['Signal'], label='Signal', linewidth=1)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax3.fill_between(df['date'], df['MACD'] - df['Signal'], 0, 
                     alpha=0.3, label='Histogram')
    ax3.set_ylabel('MACD')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"  ✓ 图表已保存: {output_file}")

def calculate_performance(df: pd.DataFrame) -> dict:
    """
    计算策略绩效（胶水代码）
    
    Args:
        df: 包含信号的数据
    
    Returns:
        绩效指标字典
    """
    # 计算收益率
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # 总收益率
    total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
    strategy_return = (df['strategy_returns'].cumsum().iloc[-1]) * 100
    
    # 交易次数
    buy_count = (df['signal_change'] == 2).sum()
    sell_count = (df['signal_change'] == -2).sum()
    
    return {
        'total_return': total_return,
        'strategy_return': strategy_return,
        'buy_signals': buy_count,
        'sell_signals': sell_count,
        'trading_days': len(df)
    }

def main():
    """主函数：MVP完整流程"""
    print("=" * 60)
    print("个人DSS系统 MVP - 基于Vibe Coding方法论")
    print("=" * 60)
    
    # 配置
    SYMBOL = "000001"  # 平安银行
    DAYS = 90
    
    # 步骤1：获取数据
    print("\n📊 步骤1: 获取数据...")
    try:
        df = fetch_stock_data(SYMBOL, DAYS)
        print(f"  ✓ 获取到 {len(df)} 条数据")
        print(f"  ✓ 数据范围: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"  ✗ 数据获取失败: {e}")
        return
    
    # 验证检查点1：数据完整性
    assert len(df) > 0, "数据获取失败"
    assert 'close' in df.columns, "缺少收盘价列"
    print("  ✓ 数据完整性验证通过")
    
    # 步骤2：计算指标
    print("\n📈 步骤2: 计算技术指标...")
    df = calculate_indicators(df)
    print("  ✓ MA5/MA20 均线计算完成")
    print("  ✓ MACD 计算完成")
    
    # 步骤3：生成信号
    print("\n🎯 步骤3: 生成交易信号...")
    df = generate_signals(df)
    perf = calculate_performance(df)
    print(f"  ✓ 买入信号: {perf['buy_signals']} 次")
    print(f"  ✓ 卖出信号: {perf['sell_signals']} 次")
    
    # 步骤4：可视化
    print("\n📉 步骤4: 生成图表...")
    visualize_results(df, SYMBOL)
    
    # 步骤5：绩效报告
    print("\n📋 步骤5: 绩效摘要")
    print("-" * 40)
    print(f"  交易天数: {perf['trading_days']} 天")
    print(f"  持有收益率: {perf['total_return']:.2f}%")
    print(f"  策略收益率: {perf['strategy_return']:.2f}%")
    print(f"  超额收益: {perf['strategy_return'] - perf['total_return']:.2f}%")
    print("-" * 40)
    
    print("\n" + "=" * 60)
    print("🎉 MVP完成！你已经拥有了一个完整的量化分析流程")
    print("=" * 60)
    print("\n下一步建议:")
    print("  1. 修改 SYMBOL 变量测试其他股票")
    print("  2. 调整均线周期参数")
    print("  3. 添加更多技术指标")
    print("  4. 参考白皮书 Phase 1 建立数据管道")

if __name__ == "__main__":
    main()
