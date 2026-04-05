#!/usr/bin/env python3
"""
测试更新后的中国A股数据模块
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.acquisition.cn_market import CNMarketDataFetcher, fetch_cn_market_data
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_updated_module():
    """测试更新后的模块"""
    print("🚀 测试更新后的中国A股数据模块")
    print("=" * 60)
    
    fetcher = CNMarketDataFetcher(prefered_lib="tushare")
    
    # 测试单只股票
    print("\n1. 测试单只股票 (000001 - 平安银行):")
    quote = fetcher.get_stock_quote('000001')
    if quote:
        print(f"   ✅ 成功获取: {quote['name']}")
        print(f"      价格: {quote['price']}, 涨跌幅: {quote['change_percent']:.2f}%")
        print(f"      成交量: {quote['volume']:,}, 成交额: {quote['amount']:,.2f}")
        print(f"      数据源: {quote['data_source']}")
    else:
        print("   ❌ 获取失败")
    
    # 测试批量获取
    print("\n2. 测试批量获取 (3只股票):")
    symbols = ['000001', '600519', '601318']  # 平安银行, 贵州茅台, 中国平安
    quotes = fetcher.get_batch_quotes(symbols)
    print(f"   ✅ 成功获取 {len(quotes)}/{len(symbols)} 只股票")
    for symbol, data in quotes.items():
        print(f"      {symbol}: {data['name']} - {data['price']} ({data['change_percent']:.2f}%)")
    
    # 测试便利函数
    print("\n3. 测试便利函数 fetch_cn_market_data():")
    market_data = fetch_cn_market_data()
    print(f"   ✅ 获取默认股票列表，共 {len(market_data)} 只股票")
    
    # 显示前3只股票
    count = 0
    for symbol, data in market_data.items():
        if count < 3:
            print(f"      {symbol}: {data['name']} - {data['price']} ({data['change_percent']:.2f}%)")
            count += 1
        else:
            break
    
    print("\n🎯 更新后的模块测试完成!")

if __name__ == "__main__":
    test_updated_module()