#!/usr/bin/env python3
"""
测试AI-Trader中实际存在的股票数据
"""

from integration.ai_trader_data_loader import AITraderDataLoader
import logging

logging.basicConfig(level=logging.INFO)

print("🧪 测试AI-Trader中实际存在的股票")
print("=" * 60)

loader = AITraderDataLoader()

# 测试实际存在的股票（招商银行 600036.SH）
print("1. 测试招商银行 (600036.SH):")

# 获取历史价格
prices = loader.get_historical_prices('600036', days=5, market='A')
if prices:
    print(f"   最近5天收盘价: {prices}")
    print(f"   最新价格: {prices[-1]}")
    if len(prices) >= 2:
        change = ((prices[-1] - prices[0]) / prices[0] * 100)
        print(f"   期间变化: {change:.2f}%")
else:
    print("   ⚠️ 无法获取价格数据")

# 测试中国石化 (600028.SH)
print("\n2. 测试中国石化 (600028.SH):")
prices = loader.get_historical_prices('600028', days=3, market='A')
if prices:
    print(f"   最近3天收盘价: {prices}")
else:
    print("   ⚠️ 无法获取价格数据")

# 查看市场概览详情
print("\n3. 查看市场概览详情:")
overview = loader.get_market_overview(market='A')
if overview and 'top_gainers' in overview:
    print(f"   日期: {overview.get('date')}")
    print(f"   总股票数: {overview.get('total_stocks')}")
    
    print(f"   涨幅前三:")
    for i, stock in enumerate(overview.get('top_gainers', [])[:3]):
        print(f"     {i+1}. {stock.get('symbol')}: {stock.get('change', 0):.2f}%")
    
    print(f"   跌幅前三:")
    for i, stock in enumerate(overview.get('top_losers', [])[:3]):
        print(f"     {i+1}. {stock.get('symbol')}: {stock.get('change', 0):.2f}%")

print("\n🎯 测试完成!")