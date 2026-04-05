#!/usr/bin/env python3
"""
最小可行数据管道
基于已验证的API构建真实数据集成
"""

import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
import requests
import time

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class MinimalDataPipeline:
    """
    最小可行数据管道
    只使用已验证有效的API
    """
    
    def __init__(self):
        """初始化数据管道"""
        # 已验证的API密钥
        self.valid_apis = {
            'alpha_vantage': {
                'key': 'BBQTETM9CS8X8LI8',
                'endpoint': 'https://www.alphavantage.co/query',
                'rate_limit': 5  # 每分钟请求限制
            },
            'fred': {
                'key': 'c917a48f98933615e6a208e7474b810c',
                'endpoint': 'https://api.stlouisfed.org/fred',
                'rate_limit': 10
            }
        }
        
        # 简单的A股数据获取（不依赖pandas）
        self.cn_stocks = {
            '000001': '平安银行',
            '600519': '贵州茅台', 
            '601318': '中国平安',
            '300750': '宁德时代'
        }
        
        self.request_count = {'alpha_vantage': 0, 'fred': 0}
        self.last_request_time = {'alpha_vantage': 0, 'fred': 0}
        
        print("✅ 最小可行数据管道初始化完成")
        print(f"   可用API: {', '.join(self.valid_apis.keys())}")
    
    def _rate_limit(self, api_name):
        """简单的速率限制"""
        current_time = time.time()
        last_time = self.last_request_time.get(api_name, 0)
        
        if current_time - last_time < 60 / self.valid_apis[api_name]['rate_limit']:
            wait_time = 60 / self.valid_apis[api_name]['rate_limit'] - (current_time - last_time)
            print(f"⏳ 速率限制，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
        
        self.last_request_time[api_name] = time.time()
        self.request_count[api_name] = self.request_count.get(api_name, 0) + 1
    
    def get_global_stock_data(self, symbol):
        """获取全球股票数据（Alpha Vantage）"""
        self._rate_limit('alpha_vantage')
        
        api = self.valid_apis['alpha_vantage']
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': api['key']
        }
        
        try:
            response = requests.get(api['endpoint'], params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    return {
                        'symbol': symbol,
                        'price': quote.get('05. price', '0'),
                        'change': quote.get('09. change', '0'),
                        'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                        'volume': quote.get('06. volume', '0'),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'alpha_vantage'
                    }
                else:
                    print(f"⚠️  Alpha Vantage返回数据格式异常: {data}")
                    return None
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def get_economic_indicator(self, series_id='GDP', limit=5):
        """获取经济指标数据（FRED）"""
        self._rate_limit('fred')
        
        api = self.valid_apis['fred']
        params = {
            'series_id': series_id,
            'api_key': api['key'],
            'file_type': 'json',
            'limit': limit
        }
        
        url = f"{api['endpoint']}/series/observations"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data:
                    # 提取最新数据
                    observations = data['observations']
                    latest_data = []
                    
                    for obs in observations[:3]:  # 取最新3个
                        if obs.get('value') != '.':
                            latest_data.append({
                                'date': obs.get('date'),
                                'value': float(obs.get('value', 0))
                            })
                    
                    return {
                        'series_id': series_id,
                        'description': data.get('seriess', [{}])[0].get('title', ''),
                        'latest_data': latest_data,
                        'unit': data.get('seriess', [{}])[0].get('units', ''),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'fred'
                    }
                else:
                    print(f"⚠️  FRED返回数据格式异常")
                    return None
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def get_cn_stock_simple(self, symbol):
        """简单获取A股数据（不依赖外部库）"""
        # 这里可以集成简单的网页爬取或使用其他轻量级方法
        # 暂时返回模拟数据
        return {
            'symbol': symbol,
            'name': self.cn_stocks.get(symbol, '未知'),
            'price': '模拟数据',
            'change_percent': '0.0',
            'timestamp': datetime.now().isoformat(),
            'source': 'simulated',
            'note': '需要集成真实A股数据源'
        }
    
    def get_market_overview(self):
        """获取市场概览数据"""
        print("📊 获取市场概览数据...")
        
        overview = {
            'timestamp': datetime.now().isoformat(),
            'stocks': {},
            'economic_indicators': {},
            'summary': {}
        }
        
        # 获取主要股票数据
        major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        
        for symbol in major_stocks:
            print(f"  获取 {symbol} 数据...")
            stock_data = self.get_global_stock_data(symbol)
            
            if stock_data:
                overview['stocks'][symbol] = stock_data
        
        # 获取经济指标
        economic_series = ['GDP', 'CPIAUCSL', 'UNRATE']  # GDP, CPI, 失业率
        
        for series in economic_series:
            print(f"  获取 {series} 数据...")
            econ_data = self.get_economic_indicator(series)
            
            if econ_data:
                overview['economic_indicators'][series] = econ_data
        
        # 生成摘要
        if overview['stocks']:
            prices = [float(data['price']) for data in overview['stocks'].values() if data['price']]
            changes = [float(data['change_percent']) for data in overview['stocks'].values() if data['change_percent']]
            
            overview['summary'] = {
                'stock_count': len(overview['stocks']),
                'avg_price': sum(prices) / len(prices) if prices else 0,
                'avg_change': sum(changes) / len(changes) if changes else 0,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"✅ 市场概览数据获取完成")
        return overview
    
    def save_data(self, data, filename=None):
        """保存数据到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_data_{timestamp}.json"
        
        data_dir = Path("real_market_data")
        data_dir.mkdir(exist_ok=True)
        
        filepath = data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 数据已保存到: {filepath}")
        return str(filepath)
    
    def generate_report(self, data):
        """生成数据报告"""
        report = []
        report.append("=" * 60)
        report.append("📈 市场数据报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"数据来源: {', '.join(self.valid_apis.keys())}")
        report.append("")
        
        # 股票数据
        if data.get('stocks'):
            report.append("📊 股票数据:")
            report.append("-" * 40)
            
            for symbol, stock in data['stocks'].items():
                price = stock.get('price', 'N/A')
                change = stock.get('change_percent', '0')
                report.append(f"{symbol:6} | 价格: ${price:8} | 涨跌幅: {change}%")
        
        # 经济指标
        if data.get('economic_indicators'):
            report.append("")
            report.append("📈 经济指标:")
            report.append("-" * 40)
            
            for series_id, indicator in data['economic_indicators'].items():
                latest = indicator.get('latest_data', [])
                if latest:
                    latest_value = latest[0]
                    report.append(f"{series_id:10} | {indicator.get('description', '')[:30]}...")
                    report.append(f"          最新值: {latest_value.get('value')} ({latest_value.get('date')})")
        
        # 摘要
        if data.get('summary'):
            report.append("")
            report.append("📋 数据摘要:")
            report.append("-" * 40)
            summary = data['summary']
            report.append(f"股票数量: {summary.get('stock_count', 0)}")
            report.append(f"平均价格: ${summary.get('avg_price', 0):.2f}")
            report.append(f"平均涨跌幅: {summary.get('avg_change', 0):.2f}%")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """主函数"""
    print("🚀 启动最小可行数据管道")
    print("=" * 60)
    
    pipeline = MinimalDataPipeline()
    
    # 测试单个股票
    print("\n1. 测试单个股票数据 (AAPL):")
    apple_data = pipeline.get_global_stock_data('AAPL')
    if apple_data:
        print(f"   ✅ 成功获取 {apple_data['symbol']} 数据")
        print(f"      价格: ${apple_data['price']}")
        print(f"      涨跌幅: {apple_data['change_percent']}%")
    else:
        print("   ❌ 获取股票数据失败")
    
    # 测试经济指标
    print("\n2. 测试经济指标数据 (GDP):")
    gdp_data = pipeline.get_economic_indicator('GDP')
    if gdp_data:
        print(f"   ✅ 成功获取 {gdp_data['series_id']} 数据")
        print(f"      描述: {gdp_data['description'][:50]}...")
        if gdp_data['latest_data']:
            latest = gdp_data['latest_data'][0]
            print(f"      最新值: {latest['value']} ({latest['date']})")
    else:
        print("   ❌ 获取经济指标失败")
    
    # 获取完整市场概览
    print("\n3. 获取市场概览数据:")
    overview = pipeline.get_market_overview()
    
    # 生成报告
    report = pipeline.generate_report(overview)
    print(f"\n{report}")
    
    # 保存数据
    saved_file = pipeline.save_data(overview)
    
    print("\n🎯 最小可行数据管道测试完成!")
    print(f"\n📊 请求统计:")
    print(f"   Alpha Vantage: {pipeline.request_count.get('alpha_vantage', 0)} 次")
    print(f"   FRED: {pipeline.request_count.get('fred', 0)} 次")
    
    print(f"\n💡 下一步建议:")
    print("   1. 定期运行此管道收集数据")
    print("   2. 集成A股真实数据源")
    print("   3. 添加数据分析和可视化")
    print("   4. 建立数据质量监控")


if __name__ == "__main__":
    main()