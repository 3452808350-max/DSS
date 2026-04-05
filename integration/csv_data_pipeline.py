#!/usr/bin/env python3
"""
CSV数据管道
将市场数据保存为CSV格式，便于分析和处理
"""

import csv
import json
from datetime import datetime
import requests
import time
from pathlib import Path

class CSVDataPipeline:
    """
    CSV数据管道
    专门处理CSV格式的市场数据
    """
    
    def __init__(self, data_dir="market_data_csv"):
        """初始化CSV数据管道"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # API配置
        self.api_config = {
            'alpha_vantage': {
                'key': 'BBQTETM9CS8X8LI8',
                'endpoint': 'https://www.alphavantage.co/query'
            },
            'fred': {
                'key': 'c917a48f98933615e6a208e7474b810c',
                'endpoint': 'https://api.stlouisfed.org/fred'
            }
        }
        
        # 监控的股票列表
        self.stock_watchlist = [
            'AAPL',    # 苹果
            'MSFT',    # 微软
            'GOOGL',   # 谷歌
            'AMZN',    # 亚马逊
            'TSLA',    # 特斯拉
            'NVDA',    # 英伟达
            'META',    # Meta
            'JPM',     # 摩根大通
            'V',       # Visa
            'JNJ',     # 强生
        ]
        
        # 经济指标列表
        self.economic_indicators = [
            'GDP',      # 国内生产总值
            'CPIAUCSL', # 消费者价格指数
            'UNRATE',   # 失业率
            'INDPRO',   # 工业生产指数
            'RETAILSMSA' # 零售销售
        ]
        
        print("📊 CSV数据管道初始化完成")
        print(f"   监控股票: {len(self.stock_watchlist)} 只")
        print(f"   经济指标: {len(self.economic_indicators)} 个")
    
    def get_stock_data_csv(self, symbol):
        """获取股票数据并返回CSV格式"""
        api = self.api_config['alpha_vantage']
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': api['key']
        }
        
        try:
            response = requests.get(api['endpoint'], params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    
                    # 转换为CSV行数据
                    csv_row = {
                        'timestamp': datetime.now().isoformat(),
                        'symbol': symbol,
                        'price': quote.get('05. price', '0'),
                        'change': quote.get('09. change', '0'),
                        'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                        'volume': quote.get('06. volume', '0'),
                        'open': quote.get('02. open', '0'),
                        'high': quote.get('03. high', '0'),
                        'low': quote.get('04. low', '0'),
                        'previous_close': quote.get('08. previous close', '0'),
                        'latest_trading_day': quote.get('07. latest trading day', ''),
                        'data_source': 'alpha_vantage'
                    }
                    
                    return csv_row
                else:
                    print(f"⚠️  {symbol}: 数据格式异常")
                    return None
            else:
                print(f"❌ {symbol}: HTTP错误 {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ {symbol}: 请求失败 - {e}")
            return None
    
    def get_economic_data_csv(self, series_id):
        """获取经济数据并返回CSV格式"""
        api = self.api_config['fred']
        params = {
            'series_id': series_id,
            'api_key': api['key'],
            'file_type': 'json',
            'limit': 1  # 只获取最新数据
        }
        
        url = f"{api['endpoint']}/series/observations"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data and data['observations']:
                    latest = data['observations'][0]
                    
                    # 转换为CSV行数据
                    csv_row = {
                        'timestamp': datetime.now().isoformat(),
                        'series_id': series_id,
                        'date': latest.get('date', ''),
                        'value': latest.get('value', '0'),
                        'realtime_start': latest.get('realtime_start', ''),
                        'realtime_end': latest.get('realtime_end', ''),
                        'data_source': 'fred'
                    }
                    
                    return csv_row
                else:
                    print(f"⚠️  {series_id}: 无数据")
                    return None
            else:
                print(f"❌ {series_id}: HTTP错误 {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ {series_id}: 请求失败 - {e}")
            return None
    
    def collect_daily_stock_data(self):
        """收集每日股票数据"""
        print(f"\n📈 开始收集股票数据 ({len(self.stock_watchlist)}只)...")
        
        stock_data = []
        successful = 0
        failed = 0
        
        for symbol in self.stock_watchlist:
            print(f"  获取 {symbol}...", end='')
            data = self.get_stock_data_csv(symbol)
            
            if data:
                stock_data.append(data)
                successful += 1
                print(" ✅")
                
                # Alpha Vantage速率限制：免费版5次/分钟
                if successful % 5 == 0:
                    print("⏳ 速率限制，等待12秒...")
                    time.sleep(12)
            else:
                failed += 1
                print(" ❌")
        
        print(f"股票数据收集完成: ✅ {successful} | ❌ {failed}")
        return stock_data
    
    def collect_daily_economic_data(self):
        """收集每日经济数据"""
        print(f"\n📊 开始收集经济数据 ({len(self.economic_indicators)}个指标)...")
        
        economic_data = []
        successful = 0
        failed = 0
        
        for series_id in self.economic_indicators:
            print(f"  获取 {series_id}...", end='')
            data = self.get_economic_data_csv(series_id)
            
            if data:
                economic_data.append(data)
                successful += 1
                print(" ✅")
            else:
                failed += 1
                print(" ❌")
        
        print(f"经济数据收集完成: ✅ {successful} | ❌ {failed}")
        return economic_data
    
    def save_to_csv(self, data, filename_prefix):
        """保存数据到CSV文件"""
        if not data:
            print(f"⚠️  无数据可保存: {filename_prefix}")
            return None
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{filename_prefix}_{date_str}_{timestamp}.csv"
        filepath = self.data_dir / filename
        
        # 获取CSV字段名
        fieldnames = list(data[0].keys())
        
        # 写入CSV文件
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"💾 数据已保存到: {filepath}")
        print(f"   记录数: {len(data)}")
        print(f"   字段数: {len(fieldnames)}")
        
        return str(filepath)
    
    def create_daily_summary_csv(self, stock_data, economic_data):
        """创建每日摘要CSV"""
        summary_data = []
        
        # 股票摘要
        if stock_data:
            total_stocks = len(stock_data)
            prices = [float(d['price']) for d in stock_data if d['price'] != '0']
            changes = [float(d['change_percent']) for d in stock_data if d['change_percent']]
            
            if prices:
                avg_price = sum(prices) / len(prices)
                max_price = max(prices)
                min_price = min(prices)
            else:
                avg_price = max_price = min_price = 0
            
            if changes:
                avg_change = sum(changes) / len(changes)
                max_gain = max(changes)
                max_loss = min(changes)
                positive = sum(1 for c in changes if c > 0)
                negative = sum(1 for c in changes if c < 0)
            else:
                avg_change = max_gain = max_loss = 0
                positive = negative = 0
            
            summary_data.append({
                'timestamp': datetime.now().isoformat(),
                'data_type': 'stock_summary',
                'total_stocks': total_stocks,
                'avg_price': round(avg_price, 2),
                'max_price': round(max_price, 2),
                'min_price': round(min_price, 2),
                'avg_change_percent': round(avg_change, 2),
                'max_gain_percent': round(max_gain, 2),
                'max_loss_percent': round(max_loss, 2),
                'positive_stocks': positive,
                'negative_stocks': negative,
                'neutral_stocks': total_stocks - positive - negative
            })
        
        # 经济指标摘要
        if economic_data:
            summary_data.append({
                'timestamp': datetime.now().isoformat(),
                'data_type': 'economic_summary',
                'total_indicators': len(economic_data),
                'indicators_list': ','.join([d['series_id'] for d in economic_data]),
                'latest_update': max([d['date'] for d in economic_data if d['date']], default='')
            })
        
        # 总体摘要
        summary_data.append({
            'timestamp': datetime.now().isoformat(),
            'data_type': 'overall_summary',
            'total_data_points': len(stock_data) + len(economic_data),
            'stock_data_points': len(stock_data),
            'economic_data_points': len(economic_data),
            'collection_date': datetime.now().strftime("%Y-%m-%d"),
            'collection_time': datetime.now().strftime("%H:%M:%S"),
            'data_sources': 'alpha_vantage,fred'
        })
        
        return summary_data
    
    def run_daily_collection(self):
        """运行每日数据收集"""
        print("=" * 60)
        print("🚀 CSV数据管道 - 每日数据收集")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 收集股票数据
        stock_data = self.collect_daily_stock_data()
        
        # 收集经济数据
        economic_data = self.collect_daily_economic_data()
        
        # 保存原始数据
        stock_csv = self.save_to_csv(stock_data, "stocks_daily") if stock_data else None
        economic_csv = self.save_to_csv(economic_data, "economics_daily") if economic_data else None
        
        # 创建并保存摘要
        summary_data = self.create_daily_summary_csv(stock_data, economic_data)
        summary_csv = self.save_to_csv(summary_data, "summary_daily") if summary_data else None
        
        # 生成报告
        self.generate_collection_report(stock_data, economic_data, 
                                      stock_csv, economic_csv, summary_csv)
        
        print(f"\n✅ 每日数据收集完成!")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            'stock_data': stock_csv,
            'economic_data': economic_csv,
            'summary_data': summary_csv,
            'total_records': len(stock_data) + len(economic_data) + len(summary_data)
        }
    
    def generate_collection_report(self, stock_data, economic_data, 
                                 stock_csv, economic_csv, summary_csv):
        """生成收集报告"""
        print("\n" + "=" * 60)
        print("📋 数据收集报告")
        print("=" * 60)
        
        print(f"📈 股票数据:")
        print(f"   记录数: {len(stock_data)}")
        if stock_data:
            symbols = [d['symbol'] for d in stock_data]
            print(f"   股票列表: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")
            print(f"   保存文件: {stock_csv}")
        
        print(f"\n📊 经济数据:")
        print(f"   记录数: {len(economic_data)}")
        if economic_data:
            indicators = [d['series_id'] for d in economic_data]
            print(f"   指标列表: {', '.join(indicators)}")
            print(f"   保存文件: {economic_csv}")
        
        print(f"\n📋 摘要数据:")
        print(f"   保存文件: {summary_csv}")
        
        print(f"\n💾 总数据量:")
        total = len(stock_data) + len(economic_data)
        print(f"   总记录数: {total}")
        print(f"   CSV文件数: {sum(1 for f in [stock_csv, economic_csv, summary_csv] if f)}")
    
    def list_csv_files(self):
        """列出所有CSV文件"""
        csv_files = list(self.data_dir.glob("*.csv"))
        
        if not csv_files:
            print("📁 无CSV文件")
            return []
        
        print(f"\n📁 CSV文件列表 ({len(csv_files)}个文件):")
        print("-" * 60)
        
        files_by_type = {}
        for file in sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True):
            filename = file.name
            if filename.startswith("stocks_"):
                file_type = "股票数据"
            elif filename.startswith("economics_"):
                file_type = "经济数据"
            elif filename.startswith("summary_"):
                file_type = "摘要数据"
            else:
                file_type = "其他数据"
            
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            files_by_type[file_type].append(file)
        
        for file_type, files in files_by_type.items():
            print(f"\n{file_type}:")
            for file in files[:5]:  # 只显示最近5个
                size_kb = file.stat().st_size / 1024
                mtime = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"  {file.name} ({size_kb:.1f}KB, {mtime})")
            
            if len(files) > 5:
                print(f"  ... 还有 {len(files) - 5} 个文件")
        
        return csv_files


def main():
    """主函数"""
    print("📊 CSV数据管道")
    print("=" * 60)
    
    pipeline = CSVDataPipeline()
    
    # 运行每日收集
    results = pipeline.run_daily_collection()
    
    # 列出所有CSV文件
    pipeline.list_csv_files()
    
    print("\n" + "=" * 60)
    print("🎯 CSV数据管道使用说明")
    print("=" * 60)
    
    print("""
💡 使用方法:
1. 每日运行: python csv_data_pipeline.py
2. 查看文件: 在 market_data_csv/ 目录中
3. 数据分析: 使用Excel、Python pandas、R等工具

📁 生成的文件:
• stocks_daily_YYYY-MM-DD_HHMMSS.csv - 股票数据
• economics_daily_YYYY-MM-DD_HHMMSS.csv - 经济数据  
• summary_daily_YYYY-MM-DD_HHMMSS.csv - 数据摘要

🔧 自定义配置:
• 修改 stock_watchlist 添加/删除股票
• 修改 economic_indicators 调整经济指标
• 调整 data_dir 改变保存目录

📈 数据分析建议:
1. 使用pandas读取CSV: df = pd.read_csv('file.csv')
2. 时间序列分析
3. 相关性分析
4. 趋势预测
    """)
    
    print(f"\n✅ CSV数据管道测试完成!")
    print(f"💾 数据已保存到: {pipeline.data_dir}/")


if __name__ == "__main__":
    main()