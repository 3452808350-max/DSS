#!/usr/bin/env python3
"""
简单CSV测试
快速生成CSV格式的市场数据
"""

import csv
from datetime import datetime
import requests

def test_single_stock_csv():
    """测试单个股票CSV数据"""
    print("📊 测试单个股票CSV数据...")
    
    api_key = "BBQTETM9CS8X8LI8"
    symbol = "AAPL"
    
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
                
                # 准备CSV数据
                csv_data = [{
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
                    'data_source': 'alpha_vantage'
                }]
                
                # 保存为CSV
                filename = f"stock_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)
                
                print(f"✅ CSV文件已生成: {filename}")
                
                # 显示CSV内容
                print(f"\n📋 CSV内容预览:")
                print("-" * 80)
                with open(filename, 'r', encoding='utf-8') as f:
                    print(f.read())
                
                return filename
            else:
                print(f"❌ 数据格式异常")
                return None
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def create_sample_csv_dataset():
    """创建示例CSV数据集"""
    print("\n📁 创建示例CSV数据集...")
    
    # 示例股票数据
    sample_stocks = [
        {
            'timestamp': '2026-02-12T12:30:00',
            'symbol': 'AAPL',
            'price': '275.50',
            'change': '1.82',
            'change_percent': '0.665',
            'volume': '51931283',
            'open': '274.70',
            'high': '280.18',
            'low': '274.45',
            'previous_close': '273.68',
            'data_source': 'alpha_vantage'
        },
        {
            'timestamp': '2026-02-12T12:30:00',
            'symbol': 'MSFT',
            'price': '415.86',
            'change': '2.34',
            'change_percent': '0.566',
            'volume': '18456789',
            'open': '414.50',
            'high': '417.20',
            'low': '413.80',
            'previous_close': '413.52',
            'data_source': 'alpha_vantage'
        },
        {
            'timestamp': '2026-02-12T12:30:00',
            'symbol': 'GOOGL',
            'price': '152.34',
            'change': '0.89',
            'change_percent': '0.588',
            'volume': '25678901',
            'open': '151.80',
            'high': '153.10',
            'low': '151.20',
            'previous_close': '151.45',
            'data_source': 'alpha_vantage'
        }
    ]
    
    # 示例经济数据
    sample_economics = [
        {
            'timestamp': '2026-02-12T12:30:00',
            'series_id': 'GDP',
            'date': '2025-10-01',
            'value': '22794.3',
            'realtime_start': '2026-02-12',
            'realtime_end': '2026-02-12',
            'data_source': 'fred'
        },
        {
            'timestamp': '2026-02-12T12:30:00',
            'series_id': 'CPIAUCSL',
            'date': '2026-01-01',
            'value': '312.332',
            'realtime_start': '2026-02-12',
            'realtime_end': '2026-02-12',
            'data_source': 'fred'
        }
    ]
    
    # 保存股票数据
    stocks_filename = f"sample_stocks_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(stocks_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = sample_stocks[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_stocks)
    
    print(f"✅ 示例股票CSV: {stocks_filename}")
    
    # 保存经济数据
    economics_filename = f"sample_economics_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(economics_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = sample_economics[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_economics)
    
    print(f"✅ 示例经济CSV: {economics_filename}")
    
    # 显示文件内容
    print(f"\n📋 示例股票CSV内容:")
    print("-" * 80)
    with open(stocks_filename, 'r', encoding='utf-8') as f:
        print(f.read())
    
    return stocks_filename, economics_filename

def demonstrate_csv_analysis():
    """演示CSV数据分析"""
    print("\n🔍 CSV数据分析演示...")
    
    # 创建示例数据
    stocks_file, economics_file = create_sample_csv_dataset()
    
    print(f"\n📈 数据分析示例:")
    print("=" * 60)
    
    # 读取股票CSV
    import csv
    with open(stocks_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        stocks = list(reader)
    
    # 基本统计
    print(f"股票数量: {len(stocks)}")
    
    # 价格分析
    prices = [float(stock['price']) for stock in stocks]
    changes = [float(stock['change_percent']) for stock in stocks]
    
    print(f"平均价格: ${sum(prices)/len(prices):.2f}")
    print(f"最高价格: ${max(prices):.2f} ({stocks[prices.index(max(prices))]['symbol']})")
    print(f"最低价格: ${min(prices):.2f} ({stocks[prices.index(min(prices))]['symbol']})")
    print(f"平均涨跌幅: {sum(changes)/len(changes):.3f}%")
    
    # 涨跌统计
    positive = sum(1 for c in changes if c > 0)
    negative = sum(1 for c in changes if c < 0)
    print(f"上涨股票: {positive} 只")
    print(f"下跌股票: {negative} 只")
    
    # 成交量分析
    volumes = [int(stock['volume']) for stock in stocks]
    total_volume = sum(volumes)
    print(f"总成交量: {total_volume:,}")
    print(f"平均成交量: {sum(volumes)/len(volumes):,.0f}")
    
    print("\n💡 CSV数据分析完成!")
    print("可以使用Excel、pandas、R等工具进行更深入的分析")

def main():
    """主函数"""
    print("=" * 60)
    print("📊 CSV数据格式测试")
    print("=" * 60)
    
    # 测试单个股票CSV
    csv_file = test_single_stock_csv()
    
    if csv_file:
        print(f"\n✅ 实时CSV数据测试成功!")
        print(f"文件: {csv_file}")
    else:
        print(f"\n⚠️  实时数据测试失败，使用示例数据")
    
    # 创建示例数据集
    demonstrate_csv_analysis()
    
    print("\n" + "=" * 60)
    print("🎯 CSV数据格式优势")
    print("=" * 60)
    
    print("""
✅ CSV格式的优点:
1. **通用性强** - Excel、Python、R、SQL等都能直接读取
2. **人类可读** - 文本格式，无需特殊软件
3. **体积小巧** - 相比JSON更节省空间
4. **处理快速** - 大多数工具都有优化过的CSV处理
5. **兼容性好** - 几乎所有数据分析工具都支持

📁 建议的文件结构:
market_data/
├── stocks/
│   ├── stocks_2026-02-12.csv
│   ├── stocks_2026-02-11.csv
│   └── ...
├── economics/
│   ├── economics_2026-02-12.csv
│   ├── economics_2026-02-11.csv
│   └── ...
└── summary/
    ├── summary_2026-02-12.csv
    ├── summary_2026-02-11.csv
    └── ...

🔧 使用建议:
1. 每日生成新的CSV文件
2. 使用日期作为文件名的一部分
3. 保持一致的列结构
4. 添加数据源和更新时间戳
5. 定期备份重要数据

📈 分析工具推荐:
• Excel/Power BI - 可视化分析
• Python pandas - 数据处理和建模
• R语言 - 统计分析和可视化
• SQL数据库 - 长期存储和查询
    """)
    
    print(f"\n✅ CSV数据格式测试完成!")
    print(f"💡 建议: 所有市场数据都保存为CSV格式，便于后续分析")

if __name__ == "__main__":
    main()