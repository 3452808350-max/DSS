
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
