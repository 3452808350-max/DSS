#!/usr/bin/env python3
"""
简单数据收集器
只测试关键功能，避免速率限制
"""

import json
from datetime import datetime
import requests
import time

def test_alpha_vantage_simple():
    """简单测试Alpha Vantage"""
    print("🔍 测试Alpha Vantage (简单模式)...")
    
    api_key = "BBQTETM9CS8X8LI8"
    symbol = "AAPL"
    
    # 使用更简单的函数，避免速率限制
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                print(f"✅ Alpha Vantage 工作正常!")
                print(f"   股票: {symbol}")
                print(f"   价格: ${quote.get('05. price', 'N/A')}")
                print(f"   涨跌幅: {quote.get('10. change percent', 'N/A')}")
                return True
            elif 'Note' in data:
                print(f"⚠️  速率限制: {data['Note'][:50]}...")
                return False
            else:
                print(f"❌ 数据格式异常")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_fred_simple():
    """简单测试FRED"""
    print("\n🔍 测试FRED (简单模式)...")
    
    api_key = "c917a48f98933615e6a208e7474b810c"
    series_id = "GDP"
    
    url = "https://api.stlouisfed.org/fred/series"
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'seriess' in data and len(data['seriess']) > 0:
                series_info = data['seriess'][0]
                print(f"✅ FRED 工作正常!")
                print(f"   数据系列: {series_info.get('id')}")
                print(f"   标题: {series_info.get('title', '')[:50]}...")
                print(f"   单位: {series_info.get('units')}")
                return True
            else:
                print(f"❌ 数据格式异常")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def collect_minimal_data():
    """收集最小数据集"""
    print("\n📊 收集最小数据集...")
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'stocks': {},
        'status': {}
    }
    
    # 只测试AAPL
    print("  获取AAPL数据...")
    apple_data = test_alpha_vantage_simple()
    data['status']['alpha_vantage'] = apple_data
    
    if apple_data:
        # 实际获取数据
        api_key = "BBQTETM9CS8X8LI8"
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': 'AAPL',
            'apikey': api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                quote_data = response.json()
                data['stocks']['AAPL'] = quote_data.get('Global Quote', {})
        except:
            pass
    
    # 测试FRED
    print("  获取GDP数据...")
    fred_data = test_fred_simple()
    data['status']['fred'] = fred_data
    
    return data

def save_data_to_file(data):
    """保存数据到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simple_market_data_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 数据已保存到: {filename}")
    return filename

def create_data_integration_plan():
    """创建数据集成计划"""
    print("\n" + "=" * 60)
    print("🚀 数据集成实施计划")
    print("=" * 60)
    
    plan = """
基于已验证的API，实施以下数据集成策略：

✅ 第一阶段：立即部署（今天）
1. Alpha Vantage集成
   - 全球主要股票实时数据
   - 支持美股、港股等
   - 免费版有速率限制（5次/分钟）

2. FRED集成
   - 宏观经济指标（GDP、CPI、失业率等）
   - 历史数据丰富
   - 免费使用

✅ 第二阶段：A股数据增强（本周内）
1. 轻量级A股数据方案
   - 使用requests直接获取公开数据
   - 东方财富、新浪财经等公开接口
   - 避免依赖pandas等重型库

2. 数据缓存机制
   - 本地存储历史数据
   - 减少API调用频率
   - 离线分析能力

✅ 第三阶段：数据质量监控（下周）
1. 数据验证框架
   - 完整性检查
   - 准确性验证
   - 及时性监控

2. 异常检测
   - 数据异常报警
   - 自动重试机制
   - 备用数据源

🎯 核心优势：
• 最小依赖：只使用requests库
• 真实数据：基于已验证的API
• 渐进增强：从简单到复杂
• 容错设计：单点故障不影响整体

📊 预期数据流：
网页API → 数据收集器 → 本地存储 → 分析引擎 → 决策支持
    ↑           ↑           ↑           ↑           ↑
Alpha     FRED      缓存      验证      可视化
Vantage
    """
    
    print(plan)

def main():
    """主函数"""
    print("=" * 60)
    print("📡 简单数据收集器")
    print("=" * 60)
    
    print("\n🎯 目标：验证API并收集最小数据集")
    
    # 收集数据
    data = collect_minimal_data()
    
    # 保存数据
    saved_file = save_data_to_file(data)
    
    # 显示数据摘要
    print("\n📋 数据摘要:")
    print(f"   生成时间: {data['timestamp']}")
    print(f"   股票数据: {len(data['stocks'])} 只")
    
    if data['stocks'].get('AAPL'):
        apple = data['stocks']['AAPL']
        print(f"   AAPL价格: ${apple.get('05. price', 'N/A')}")
        print(f"   AAPL涨跌幅: {apple.get('10. change percent', 'N/A')}")
    
    print(f"   API状态:")
    for api, status in data['status'].items():
        status_icon = "✅" if status else "❌"
        print(f"     {api}: {status_icon}")
    
    # 创建实施计划
    create_data_integration_plan()
    
    print("\n🎉 简单数据收集器完成!")
    print("\n💡 下一步：")
    print("   1. 定期运行此脚本收集数据")
    print("   2. 扩展A股数据收集功能")
    print("   3. 集成到DSS决策支持系统")

if __name__ == "__main__":
    main()