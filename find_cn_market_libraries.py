#!/usr/bin/env python3
"""
寻找中国A股数据获取的成熟轮子
基于胶水编程理念：能抄不写，能连不造
"""

import subprocess
import sys

def search_pypi_for_china_stock():
    """搜索PyPI上中国股票相关的库"""
    libraries = [
        # 已知的中国金融数据库
        "akshare",           # 东方财富、新浪等数据
        "easytrader",        # 自动交易
        "efinance",          # 东方财富数据
        "tushare",           # 国内金融数据
        "baostock",          # 百度股票数据
        "jqdatasdk",         # 聚宽数据
        "ricequant",         # 米筐数据
        "windpy",            # Wind数据
        "pytdx",             # 通达信数据
    ]
    
    print("🔍 搜索中国A股数据获取库")
    print("=" * 60)
    
    for lib in libraries:
        try:
            # 尝试导入
            __import__(lib)
            print(f"✅ {lib}: 已安装")
        except ImportError:
            print(f"📦 {lib}: 可用 (需要安装)")
    
    print("\n🎯 推荐使用:")
    print("1. akshare - 免费，数据全面，社区活跃")
    print("2. tushare - 专业，API稳定，有免费额度")
    print("3. efinance - 简单易用，东方财富数据")

def check_akshare_availability():
    """检查akshare的可用性"""
    print("\n📊 检查akshare数据示例:")
    print("-" * 40)
    
    try:
        import akshare as ak
        # 尝试获取一个简单的数据
        stock_zh_a_spot_df = ak.stock_zh_a_spot()
        print(f"✅ akshare可用，获取到 {len(stock_zh_a_spot_df)} 只A股实时数据")
        print(f"   列名: {list(stock_zh_a_spot_df.columns[:5])}...")
        return True
    except ImportError:
        print("❌ akshare未安装，可以使用: pip install akshare")
        return False
    except Exception as e:
        print(f"⚠️  akshare安装但运行出错: {e}")
        return False

def create_cn_market_module_template():
    """创建中国A股数据模块模板"""
    template = '''
"""
中国A股市场数据获取模块
基于胶水编程理念，使用成熟库连接
"""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd

# 尝试导入各种中国股票数据库
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("警告: akshare未安装，部分功能受限")

try:
    import tushare as ts
    HAS_TUSHARE = True
except ImportError:
    HAS_TUSHARE = False

try:
    import efinance as ef
    HAS_EFINANCE = True
except ImportError:
    HAS_EFINANCE = False

logger = logging.getLogger(__name__)

class CNMarketDataFetcher:
    """中国A股数据获取器 - 胶水编程实现"""
    
    def __init__(self, prefered_lib="akshare"):
        """
        初始化
        
        Args:
            prefered_lib: 优先使用的库 (akshare, tushare, efinance)
        """
        self.prefered_lib = prefered_lib
        self._init_preferred_library()
    
    def _init_preferred_library(self):
        """初始化优先库"""
        if self.prefered_lib == "akshare" and HAS_AKSHARE:
            logger.info("使用akshare作为数据源")
        elif self.prefered_lib == "tushare" and HAS_TUSHARE:
            logger.info("使用tushare作为数据源")
            # tushare需要token
            ts.set_token('你的tushare_token')
        elif self.prefered_lib == "efinance" and HAS_EFINANCE:
            logger.info("使用efinance作为数据源")
        else:
            logger.warning("没有可用的中国股票数据库，请安装akshare/tushare/efinance")
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票实时报价
        
        Args:
            symbol: 股票代码，如 '000001' (平安银行)
            
        Returns:
            股票报价信息字典
        """
        try:
            if HAS_AKSHARE:
                # 使用akshare获取实时数据
                stock_zh_a_spot_df = ak.stock_zh_a_spot()
                stock_data = stock_zh_a_spot_df[stock_zh_a_spot_df['代码'] == symbol]
                
                if not stock_data.empty:
                    return {
                        'symbol': symbol,
                        'name': stock_data.iloc[0]['名称'],
                        'price': float(stock_data.iloc[0]['最新价']),
                        'change': float(stock_data.iloc[0]['涨跌幅']),
                        'volume': int(stock_data.iloc[0]['成交量']),
                        'amount': float(stock_data.iloc[0]['成交额']),
                        'data_source': 'akshare'
                    }
            
            # 可以添加其他库的备选方案
            logger.warning(f"无法获取股票 {symbol} 的数据")
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 报价失败: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            
        Returns:
            DataFrame包含历史数据
        """
        try:
            if HAS_AKSHARE:
                # 使用akshare获取历史数据
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                        start_date=start_date, end_date=end_date,
                                        adjust="qfq")
                return df
            elif HAS_TUSHARE:
                # 使用tushare备选
                pro = ts.pro_api()
                df = pro.daily(ts_code=f"{symbol}.SZ", 
                              start_date=start_date, end_date=end_date)
                return df
            else:
                logger.error("没有可用的历史数据获取库")
                return None
                
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return None
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取股票报价
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            字典映射股票代码到报价信息
        """
        results = {}
        
        try:
            if HAS_AKSHARE:
                stock_zh_a_spot_df = ak.stock_zh_a_spot()
                
                for symbol in symbols:
                    stock_data = stock_zh_a_spot_df[stock_zh_a_spot_df['代码'] == symbol]
                    
                    if not stock_data.empty:
                        results[symbol] = {
                            'symbol': symbol,
                            'name': stock_data.iloc[0]['名称'],
                            'price': float(stock_data.iloc[0]['最新价']),
                            'change': float(stock_data.iloc[0]['涨跌幅']),
                            'data_source': 'akshare'
                        }
                    else:
                        logger.warning(f"股票 {symbol} 未找到")
            
            return results
            
        except Exception as e:
            logger.error(f"批量获取报价失败: {e}")
            return results

# 便利函数
def fetch_cn_market_data(symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    便利函数：获取中国A股市场数据
    
    Args:
        symbols: 股票代码列表，None则获取所有
        
    Returns:
        股票数据字典
    """
    fetcher = CNMarketDataFetcher()
    
    if symbols is None:
        # 获取一些默认的A股
        symbols = ['000001', '000002', '600519', '601318']
    
    return fetcher.get_batch_quotes(symbols)

if __name__ == "__main__":
    # 测试代码
    print("测试中国A股数据获取模块")
    fetcher = CNMarketDataFetcher()
    
    # 测试单只股票
    quote = fetcher.get_stock_quote('000001')
    if quote:
        print(f"平安银行: {quote}")
    
    # 测试批量获取
    quotes = fetcher.get_batch_quotes(['000001', '600519'])
    print(f"批量获取: {len(quotes)} 只股票")
'''
    
    print("\n📝 中国A股数据模块模板:")
    print("=" * 60)
    print(template)
    
    # 保存到文件
    with open('cn_market_template.py', 'w', encoding='utf-8') as f:
        f.write(template)
    print("\n💾 模板已保存到: cn_market_template.py")

if __name__ == "__main__":
    search_pypi_for_china_stock()
    
    # 检查akshare
    check_akshare_availability()
    
    # 创建模板
    create_cn_market_module_template()
    
    print("\n🎯 下一步:")
    print("1. 安装推荐的库: pip install akshare")
    print("2. 使用模板创建 data/acquisition/cn_market.py")
    print("3. 测试数据获取功能")
    print("4. 集成到analyse DSS系统")