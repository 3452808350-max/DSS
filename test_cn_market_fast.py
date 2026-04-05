#!/usr/bin/env python3
"""
快速测试中国A股数据模块
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.acquisition.cn_market import CNMarketDataFetcher
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_fast():
    """快速测试"""
    print("🚀 快速测试中国A股数据模块")
    print("=" * 60)
    
    fetcher = CNMarketDataFetcher()
    
    # 只测试一只股票，避免获取全部数据
    print("\n1. 测试单只股票 (000001 - 平安银行):")
    quote = fetcher.get_stock_quote('000001')
    if quote:
        print(f"   ✅ 成功获取: {quote['name']}")
        print(f"      价格: {quote['price']}, 涨跌幅: {quote['change_percent']:.2f}%")
        print(f"      成交量: {quote['volume']:,}, 成交额: {quote['amount']:,.2f}")
    else:
        print("   ❌ 获取失败")
    
    # 测试指数数据（如果有其他方法）
    print("\n2. 测试备用数据源:")
    try:
        # 尝试使用其他方法获取数据
        import akshare as ak
        
        # 尝试获取单只股票的历史数据（可能更快）
        print("   尝试获取贵州茅台历史数据...")
        hist_df = ak.stock_zh_a_hist(symbol="600519", period="daily", 
                                     start_date="2026-02-10", end_date="2026-02-11")
        if not hist_df.empty:
            print(f"   ✅ 成功获取历史数据")
            print(f"      日期: {hist_df.iloc[-1]['日期']}")
            print(f"      收盘价: {hist_df.iloc[-1]['收盘']}")
        else:
            print("   ⚠️  未获取到历史数据")
            
    except Exception as e:
        print(f"   ❌ 备用方法失败: {e}")
    
    print("\n🎯 快速测试完成!")

if __name__ == "__main__":
    test_fast()