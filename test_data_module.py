#!/usr/bin/env python3
"""
测试数据获取模块
"""

import sys
sys.path.insert(0, ".")

from data.acquisition.us_market import USMarketDataFetcher
import time

print("测试USMarketDataFetcher...")
fetcher = USMarketDataFetcher()

# 测试单个股票
print("\n1. 测试单个股票 (AAPL):")
quote = fetcher.get_stock_quote("AAPL")
if quote:
    print(f"   ✅ AAPL: ${quote['price']:.2f} ({quote['change_percent']:.2f}%)")
else:
    print("   ❌ 获取失败")

# 测试批量获取 (小批量避免频率限制)
print("\n2. 测试批量获取 (MSFT, GOOGL):")
symbols = ["MSFT", "GOOGL"]
print(f"   等待12秒避免频率限制...")
time.sleep(12)

quotes = fetcher.get_batch_quotes(symbols)
for symbol, quote in quotes.items():
    print(f"   ✅ {symbol}: ${quote['price']:.2f} ({quote['change_percent']:.2f}%)")

print(f"\n📊 成功获取 {len(quotes)}/{len(symbols)} 个股票数据")

# 测试便利函数
print("\n3. 测试便利函数:")
from data.acquisition.us_market import fetch_us_market_data

# 只测试少量股票避免频率限制
test_symbols = ["AAPL", "MSFT"]
print(f"   测试 {len(test_symbols)} 个股票...")
data = fetch_us_market_data(test_symbols)
print(f"   ✅ 获取 {len(data)} 个股票数据")

print("\n🎉 数据获取模块测试完成!")