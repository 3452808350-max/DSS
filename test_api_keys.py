#!/usr/bin/env python3
"""
测试API密钥有效性
"""

import requests
import json
from datetime import datetime

def test_alpha_vantage():
    """测试Alpha Vantage API"""
    print("🔍 测试Alpha Vantage API...")
    
    api_key = "BBQTETM9CS8X8LI8"
    symbol = "AAPL"
    
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': api_key,
        'outputsize': 'compact'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'Error Message' in data:
                print(f"❌ Alpha Vantage错误: {data['Error Message']}")
                return False
            elif 'Note' in data:
                print(f"⚠️  Alpha Vantage限制: {data['Note']}")
                return False
            else:
                print(f"✅ Alpha Vantage API有效!")
                print(f"   股票: {symbol}")
                
                # 显示最新数据
                time_series = data.get('Time Series (Daily)', {})
                if time_series:
                    latest_date = max(time_series.keys())
                    latest_data = time_series[latest_date]
                    print(f"   最新日期: {latest_date}")
                    print(f"   收盘价: {latest_data.get('4. close')}")
                    print(f"   成交量: {latest_data.get('5. volume')}")
                
                return True
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_fmp_api():
    """测试Financial Modeling Prep API"""
    print("\n🔍 测试Financial Modeling Prep API...")
    
    api_key = "oJw67iSq4FuJTIArmUKI9l3e3qZmNZod"
    symbol = "AAPL"
    
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ FMP API有效!")
                company = data[0]
                print(f"   公司: {company.get('companyName', 'N/A')}")
                print(f"   行业: {company.get('industry', 'N/A')}")
                print(f"   市值: ${company.get('mktCap', 0):,}")
                return True
            else:
                print(f"❌ FMP返回空数据")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_fred_api():
    """测试FRED API"""
    print("\n🔍 测试FRED API...")
    
    api_key = "c917a48f98933615e6a208e7474b810c"
    series_id = "GDP"
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'limit': 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'observations' in data:
                print(f"✅ FRED API有效!")
                observations = data['observations']
                print(f"   数据系列: {series_id}")
                print(f"   数据点数: {len(observations)}")
                
                # 显示最新5个数据点
                for i, obs in enumerate(observations[:3]):
                    print(f"   {obs.get('date')}: {obs.get('value')}")
                return True
            else:
                print(f"❌ FRED返回数据格式错误")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_tradestie_api():
    """测试Tradestie API"""
    print("\n🔍 测试Tradestie API...")
    
    ticker = "GME"
    url = "https://api.tradestie.com/v1/apps/reddit"
    params = {'ticker': ticker}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"✅ Tradestie API有效!")
                print(f"   Ticker: {ticker}")
                print(f"   Reddit帖子数: {len(data)}")
                
                if len(data) > 0:
                    # 显示第一个帖子
                    first_post = data[0]
                    print(f"   示例帖子: {first_post.get('ticker', 'N/A')}")
                    print(f"   情绪分数: {first_post.get('sentiment_score', 'N/A')}")
                return True
            else:
                print(f"❌ Tradestie返回数据格式错误")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_tushare_data():
    """测试Tushare数据"""
    print("\n🔍 测试Tushare A股数据...")
    
    try:
        # 导入本地模块
        import sys
        from pathlib import Path
        
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from data.acquisition.cn_market import CNMarketDataFetcher
        
        fetcher = CNMarketDataFetcher(prefered_lib="tushare")
        
        # 测试平安银行
        data = fetcher.get_stock_quote('000001')
        
        if data:
            print(f"✅ Tushare数据有效!")
            print(f"   股票: {data.get('name', 'N/A')}")
            print(f"   代码: {data.get('symbol', 'N/A')}")
            print(f"   价格: {data.get('price', 'N/A')}")
            print(f"   涨跌幅: {data.get('change_percent', 'N/A')}%")
            return True
        else:
            print(f"❌ 无法获取Tushare数据")
            return False
            
    except Exception as e:
        print(f"❌ Tushare测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("📊 API密钥有效性测试")
    print("=" * 60)
    
    results = {
        'Alpha Vantage': test_alpha_vantage(),
        'Financial Modeling Prep': test_fmp_api(),
        'FRED': test_fred_api(),
        'Tradestie': test_tradestie_api(),
        'Tushare': test_tushare_data()
    }
    
    print("\n" + "=" * 60)
    print("📈 测试结果总结")
    print("=" * 60)
    
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 有效" if result else "❌ 无效"
        print(f"{name:25} {status}")
    
    print(f"\n成功率: {successful}/{total} ({successful/total*100:.1f}%)")
    
    if successful >= 3:
        print("\n🎉 多数API密钥有效，可以开始数据集成!")
    else:
        print("\n⚠️  部分API密钥可能有问题，需要检查")

if __name__ == "__main__":
    main()