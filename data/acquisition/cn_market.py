"""
中国A股市场数据获取模块
基于胶水编程理念，使用成熟库连接
"""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd

from config.settings import API_CONFIG

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
    
    def __init__(self, prefered_lib="tushare"):
        """
        初始化
        
        Args:
            prefered_lib: 优先使用的库 (tushare, akshare, efinance)
            默认使用tushare，因为它通常更快
        """
        self.prefered_lib = prefered_lib
        self._init_preferred_library()
    
    def _init_preferred_library(self):
        """初始化优先库"""
        if self.prefered_lib == "akshare" and HAS_AKSHARE:
            logger.info("使用akshare作为中国A股数据源")
        elif self.prefered_lib == "tushare" and HAS_TUSHARE:
            logger.info("使用tushare作为中国A股数据源")
            # tushare需要token
            from config.settings import API_CONFIG
            tushare_token = getattr(API_CONFIG, 'TUSHARE_API_KEY', '')
            if tushare_token:
                ts.set_token(tushare_token)
            else:
                logger.warning("tushare token未配置，部分功能可能受限")
        elif self.prefered_lib == "efinance" and HAS_EFINANCE:
            logger.info("使用efinance作为中国A股数据源")
        else:
            logger.warning("没有可用的中国股票数据库，请安装akshare/tushare/efinance")
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票实时报价
        
        Args:
            symbol: 股票代码，如 '000001' (平安银行)
                   '600519' (贵州茅台)
            
        Returns:
            股票报价信息字典，格式与US市场统一
        """
        try:
            # 优先使用tushare的旧版API（不需要token）
            if HAS_TUSHARE:
                try:
                    # 使用tushare的旧版API获取实时行情
                    df = ts.get_realtime_quotes([symbol])
                    
                    if not df.empty:
                        return {
                            'symbol': symbol,
                            'name': df.iloc[0]['name'],
                            'timestamp': pd.Timestamp.now().isoformat(),
                            'price': float(df.iloc[0]['price']),
                            'change': float(df.iloc[0]['price']) - float(df.iloc[0]['pre_close']),
                            'change_percent': (float(df.iloc[0]['price']) - float(df.iloc[0]['pre_close'])) / float(df.iloc[0]['pre_close']) * 100,
                            'volume': int(df.iloc[0]['volume']),
                            'amount': float(df.iloc[0]['amount']),
                            'open': float(df.iloc[0]['open']),
                            'high': float(df.iloc[0]['high']),
                            'low': float(df.iloc[0]['low']),
                            'previous_close': float(df.iloc[0]['pre_close']),
                            'data_source': 'tushare',
                            'market': 'CN'
                        }
                except Exception as tushare_error:
                    logger.warning(f"tushare实时行情获取失败，尝试其他方法: {tushare_error}")
            
            # 备选方案：akshare
            if HAS_AKSHARE:
                try:
                    # 使用akshare获取实时数据
                    stock_zh_a_spot_df = ak.stock_zh_a_spot()
                    stock_data = stock_zh_a_spot_df[stock_zh_a_spot_df['代码'] == symbol]
                    
                    if not stock_data.empty:
                        return {
                            'symbol': symbol,
                            'name': stock_data.iloc[0]['名称'],
                            'timestamp': pd.Timestamp.now().isoformat(),
                            'price': float(stock_data.iloc[0]['最新价']),
                            'change': float(stock_data.iloc[0]['涨跌额']),
                            'change_percent': float(stock_data.iloc[0]['涨跌幅']),
                            'volume': int(stock_data.iloc[0]['成交量']),
                            'amount': float(stock_data.iloc[0]['成交额']),
                            'open': float(stock_data.iloc[0]['今开']),
                            'high': float(stock_data.iloc[0]['最高']),
                            'low': float(stock_data.iloc[0]['最低']),
                            'previous_close': float(stock_data.iloc[0]['昨收']),
                            'data_source': 'akshare',
                            'market': 'CN'
                        }
                except Exception as akshare_error:
                    logger.warning(f"akshare获取失败: {akshare_error}")
            
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
            DataFrame包含历史数据，格式统一
        """
        try:
            if HAS_AKSHARE:
                # 使用akshare获取历史数据
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                        start_date=start_date, end_date=end_date,
                                        adjust="qfq")
                
                # 统一列名
                if not df.empty:
                    df = df.rename(columns={
                        '日期': 'date',
                        '开盘': 'open',
                        '收盘': 'close',
                        '最高': 'high',
                        '最低': 'low',
                        '成交量': 'volume',
                        '成交额': 'amount',
                        '振幅': 'amplitude',
                        '涨跌幅': 'change_percent',
                        '涨跌额': 'change',
                        '换手率': 'turnover'
                    })
                    df['symbol'] = symbol
                    df['market'] = 'CN'
                    df['data_source'] = 'akshare'
                
                return df
            elif HAS_TUSHARE and hasattr(API_CONFIG, 'TUSHARE_API_KEY'):
                # 使用tushare备选
                pro = ts.pro_api()
                # 判断是沪市还是深市
                exchange = 'SH' if symbol.startswith('6') else 'SZ'
                df = pro.daily(ts_code=f"{symbol}.{exchange}", 
                              start_date=start_date, end_date=end_date)
                
                if not df.empty:
                    df = df.rename(columns={
                        'trade_date': 'date',
                        'open': 'open',
                        'close': 'close',
                        'high': 'high',
                        'low': 'low',
                        'vol': 'volume',
                        'amount': 'amount',
                        'pct_chg': 'change_percent'
                    })
                    df['symbol'] = symbol
                    df['market'] = 'CN'
                    df['data_source'] = 'tushare'
                
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
            # 优先使用tushare
            if HAS_TUSHARE:
                try:
                    df = ts.get_realtime_quotes(symbols)
                    
                    for _, row in df.iterrows():
                        symbol = row['code']
                        results[symbol] = {
                            'symbol': symbol,
                            'name': row['name'],
                            'timestamp': pd.Timestamp.now().isoformat(),
                            'price': float(row['price']),
                            'change': float(row['price']) - float(row['pre_close']),
                            'change_percent': (float(row['price']) - float(row['pre_close'])) / float(row['pre_close']) * 100,
                            'volume': int(row['volume']),
                            'amount': float(row['amount']),
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'previous_close': float(row['pre_close']),
                            'data_source': 'tushare',
                            'market': 'CN'
                        }
                    
                    return results
                    
                except Exception as tushare_error:
                    logger.warning(f"tushare批量获取失败，尝试akshare: {tushare_error}")
            
            # 备选方案：akshare
            if HAS_AKSHARE:
                try:
                    stock_zh_a_spot_df = ak.stock_zh_a_spot()
                    
                    for symbol in symbols:
                        stock_data = stock_zh_a_spot_df[stock_zh_a_spot_df['代码'] == symbol]
                        
                        if not stock_data.empty:
                            results[symbol] = {
                                'symbol': symbol,
                                'name': stock_data.iloc[0]['名称'],
                                'timestamp': pd.Timestamp.now().isoformat(),
                                'price': float(stock_data.iloc[0]['最新价']),
                                'change': float(stock_data.iloc[0]['涨跌额']),
                                'change_percent': float(stock_data.iloc[0]['涨跌幅']),
                                'volume': int(stock_data.iloc[0]['成交量']),
                                'open': float(stock_data.iloc[0]['今开']),
                                'high': float(stock_data.iloc[0]['最高']),
                                'low': float(stock_data.iloc[0]['最低']),
                                'previous_close': float(stock_data.iloc[0]['昨收']),
                                'data_source': 'akshare',
                                'market': 'CN'
                            }
                        else:
                            logger.warning(f"股票 {symbol} 未找到")
                except Exception as akshare_error:
                    logger.warning(f"akshare批量获取失败: {akshare_error}")
            
            return results
            
        except Exception as e:
            logger.error(f"批量获取报价失败: {e}")
            return results
    
    def get_index_data(self, index_symbol: str = "sh000001") -> Optional[Dict[str, Any]]:
        """
        获取指数数据
        
        Args:
            index_symbol: 指数代码
                sh000001: 上证指数
                sz399001: 深证成指
                sz399006: 创业板指
            
        Returns:
            指数数据字典
        """
        try:
            if HAS_AKSHARE:
                # 获取指数实时数据
                index_spot_df = ak.stock_zh_index_spot()
                index_data = index_spot_df[index_spot_df['代码'] == index_symbol]
                
                if not index_data.empty:
                    return {
                        'symbol': index_symbol,
                        'name': index_data.iloc[0]['名称'],
                        'price': float(index_data.iloc[0]['最新价']),
                        'change': float(index_data.iloc[0]['涨跌额']),
                        'change_percent': float(index_data.iloc[0]['涨跌幅']),
                        'data_source': 'akshare'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"获取指数数据失败: {e}")
            return None
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        获取市场整体状态
        
        Returns:
            市场状态信息
        """
        try:
            market_status = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'data_source': 'akshare' if HAS_AKSHARE else 'none'
            }
            
            if HAS_AKSHARE:
                # 获取涨跌家数
                try:
                    stock_zh_a_spot_df = ak.stock_zh_a_spot()
                    
                    if not stock_zh_a_spot_df.empty:
                        gainers = (stock_zh_a_spot_df['涨跌幅'] > 0).sum()
                        losers = (stock_zh_a_spot_df['涨跌幅'] < 0).sum()
                        unchanged = (stock_zh_a_spot_df['涨跌幅'] == 0).sum()
                        
                        market_status.update({
                            'total_stocks': len(stock_zh_a_spot_df),
                            'gainers': int(gainers),
                            'losers': int(losers),
                            'unchanged': int(unchanged),
                            'gain_ratio': float(gainers / len(stock_zh_a_spot_df)) if len(stock_zh_a_spot_df) > 0 else 0
                        })
                except Exception as e:
                    logger.warning(f"获取涨跌家数失败: {e}")
            
            return market_status
            
        except Exception as e:
            logger.error(f"获取市场状态失败: {e}")
            return {'error': str(e)}

# 便利函数
def fetch_cn_market_data(symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    便利函数：获取中国A股市场数据
    
    Args:
        symbols: 股票代码列表，None则使用默认列表
        
    Returns:
        股票数据字典
    """
    fetcher = CNMarketDataFetcher()
    
    if symbols is None:
        # 获取一些有代表性的A股
        symbols = [
            '000001',  # 平安银行
            '000002',  # 万科A
            '600519',  # 贵州茅台
            '601318',  # 中国平安
            '600036',  # 招商银行
            '000858',  # 五粮液
            '002415',  # 海康威视
            '300750',  # 宁德时代
        ]
    
    return fetcher.get_batch_quotes(symbols)

def test_cn_market_module():
    """测试中国A股数据模块"""
    print("🧪 测试中国A股数据获取模块")
    print("=" * 60)
    
    fetcher = CNMarketDataFetcher()
    
    # 测试单只股票
    print("\n1. 测试单只股票 (000001 - 平安银行):")
    quote = fetcher.get_stock_quote('000001')
    if quote:
        print(f"   ✅ 成功获取: {quote['name']}")
        print(f"      价格: {quote['price']}, 涨跌幅: {quote['change_percent']:.2f}%")
    else:
        print("   ❌ 获取失败")
    
    # 测试批量获取
    print("\n2. 测试批量获取 (3只股票):")
    quotes = fetcher.get_batch_quotes(['000001', '600519', '601318'])
    print(f"   ✅ 成功获取 {len(quotes)} 只股票")
    for symbol, data in quotes.items():
        print(f"      {symbol}: {data['name']} - {data['price']} ({data['change_percent']:.2f}%)")
    
    # 测试市场状态
    print("\n3. 测试市场状态:")
    market_status = fetcher.get_market_status()
    if 'total_stocks' in market_status:
        print(f"   ✅ 总股票数: {market_status['total_stocks']}")
        print(f"      上涨: {market_status['gainers']}, 下跌: {market_status['losers']}")
        print(f"      上涨比例: {market_status['gain_ratio']:.1%}")
    else:
        print("   ⚠️  市场状态获取受限")
    
    # 测试指数
    print("\n4. 测试指数数据 (sh000001 - 上证指数):")
    index_data = fetcher.get_index_data('sh000001')
    if index_data:
        print(f"   ✅ {index_data['name']}: {index_data['price']} ({index_data['change_percent']:.2f}%)")
    else:
        print("   ⚠️  指数数据获取受限")
    
    print("\n🎉 中国A股数据模块测试完成!")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    test_cn_market_module()