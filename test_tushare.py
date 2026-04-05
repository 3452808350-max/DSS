#!/usr/bin/env python3
"""
测试tushare
"""

import tushare as ts
import pandas as pd

print("🧪 测试tushare")
print("=" * 60)

# 设置token（如果没有，使用空字符串）
ts.set_token('')

# 创建pro接口
pro = ts.pro_api()

print("1. 测试基础功能:")
try:
    # 测试获取股票基本信息
    print("   尝试获取股票基本信息...")
    
    # 获取上证指数成分股
    df = pro.index_weight(index_code='000001.SH', start_date='20260201', end_date='20260211')
    
    if not df.empty:
        print(f"   ✅ 成功获取数据，共 {len(df)} 条记录")
        print(f"      列名: {list(df.columns)}")
        print(f"      示例数据:")
        print(df.head(3).to_string())
    else:
        print("   ⚠️  数据为空，可能需要token")
        
except Exception as e:
    print(f"   ❌ 获取数据失败: {e}")

print("\n2. 测试无需token的功能:")
try:
    # 尝试使用不需要token的功能
    print("   尝试获取实时行情（可能需要token）...")
    
    # 使用旧版API（可能不需要token）
    df = ts.get_realtime_quotes(['000001', '600519'])
    
    if not df.empty:
        print(f"   ✅ 成功获取实时行情，共 {len(df)} 只股票")
        print(f"      列名: {list(df.columns)[:10]}...")
        print(f"      平安银行: {df.iloc[0]['name']} - {df.iloc[0]['price']}")
        print(f"      贵州茅台: {df.iloc[1]['name']} - {df.iloc[1]['price']}")
    else:
        print("   ⚠️  实时行情获取失败")
        
except Exception as e:
    print(f"   ❌ 实时行情获取失败: {e}")

print("\n3. 测试历史数据:")
try:
    # 获取历史数据
    print("   尝试获取历史数据...")
    
    df = ts.get_hist_data('000001', start='2026-02-01', end='2026-02-11')
    
    if not df.empty:
        print(f"   ✅ 成功获取历史数据，共 {len(df)} 条记录")
        print(f"      最近交易日: {df.index[0]}")
        print(f"      收盘价: {df.iloc[0]['close']}")
        print(f"      涨跌幅: {df.iloc[0]['p_change']}%")
    else:
        print("   ⚠️  历史数据获取失败")
        
except Exception as e:
    print(f"   ❌ 历史数据获取失败: {e}")

print("\n🎯 tushare测试完成!")