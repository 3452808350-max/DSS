#!/usr/bin/env python3
"""
只测试中国A股数据获取
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import argparse
import logging
from datetime import datetime

from config.settings import get_all_configs
from data.acquisition.cn_market import fetch_cn_market_data

def setup_logging():
    """Set up logging configuration"""
    from config.settings import LOGGING_CONFIG
    
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG.LOG_LEVEL),
        format=LOGGING_CONFIG.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║      analyse (DSS) - 中国A股测试       ║
    ║                    Version 0.1.0                         ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def fetch_cn_data():
    """获取中国A股市场数据"""
    logger = logging.getLogger(__name__)
    logger.info("开始获取中国A股数据")
    
    print("\n📊 获取中国A股市场数据")
    print("="*60)
    
    try:
        cn_data = fetch_cn_market_data()
        
        if cn_data:
            print(f"✅ 成功获取 {len(cn_data)} 只A股股票")
            
            # 显示摘要
            gainers = sum(1 for d in cn_data.values() if d['change_percent'] > 0)
            losers = sum(1 for d in cn_data.values() if d['change_percent'] < 0)
            unchanged = sum(1 for d in cn_data.values() if d['change_percent'] == 0)
            
            print(f"\n📈 上涨: {gainers}, 📉 下跌: {losers}, ➖ 平盘: {unchanged}")
            
            # 显示涨幅前3名
            sorted_stocks = sorted(cn_data.items(), 
                                 key=lambda x: x[1]['change_percent'], 
                                 reverse=True)
            
            print("\n🏆 涨幅前3名:")
            for symbol, data in sorted_stocks[:3]:
                change = data['change_percent']
                icon = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
                print(f"{icon} {symbol}: {data['name']}")
                print(f"   价格: ¥{data['price']:.2f}, 涨跌幅: {change:+.2f}%")
                print(f"   成交量: {data['volume']:,}, 成交额: ¥{data['amount']:,.2f}")
                print(f"   数据源: {data['data_source']}")
                print()
            
            # 显示跌幅前3名
            print("\n📦 跌幅前3名:")
            for symbol, data in sorted_stocks[-3:]:
                change = data['change_percent']
                icon = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
                print(f"{icon} {symbol}: {data['name']}")
                print(f"   价格: ¥{data['price']:.2f}, 涨跌幅: {change:+.2f}%")
                print(f"   成交量: {data['volume']:,}, 成交额: ¥{data['amount']:,.2f}")
                print()
            
            # 保存数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = project_root / "data" / f"cn_market_{timestamp}.json"
            
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cn_data, f, indent=2, default=str, ensure_ascii=False)
            
            print(f"\n💾 数据已保存到: {filename}")
            print(f"📁 文件大小: {filename.stat().st_size:,} 字节")
                
        else:
            print("❌ 获取中国A股市场数据失败")
            
    except Exception as e:
        logger.error(f"获取中国数据失败: {e}")
        print(f"❌ 中国数据错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="analyse DSS - 中国A股测试")
    parser.add_argument("command", choices=["fetch"], help="命令")
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    # 打印横幅
    print_banner()
    
    if args.command == "fetch":
        fetch_cn_data()
    else:
        print(f"未知命令: {args.command}")

if __name__ == "__main__":
    main()