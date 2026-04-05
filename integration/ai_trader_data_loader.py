"""
AI-Trader数据加载器
直接读取AI-Trader的数据文件，避免复杂的工具调用
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AITraderDataLoader:
    """
    AI-Trader数据加载器
    直接读取AI-Trader的JSONL数据文件
    """
    
    def __init__(self, ai_trader_path: str = "/home/kyj/文档/AI-Trader"):
        """
        初始化数据加载器
        
        Args:
            ai_trader_path: AI-Trader项目路径
        """
        self.ai_trader_path = Path(ai_trader_path)
        self.data_cache = {}
        
        # 数据文件路径
        self.us_stock_data = self.ai_trader_path / "data" / "merged.jsonl"
        self.a_stock_data = self.ai_trader_path / "data" / "A_stock" / "merged.jsonl"
        self.a_stock_hourly_data = self.ai_trader_path / "data" / "A_stock" / "merged_hourly.jsonl"
        
        logger.info(f"AI-Trader数据加载器初始化完成")
        logger.info(f"US数据文件: {self.us_stock_data.exists()}")
        logger.info(f"A股数据文件: {self.a_stock_data.exists()}")
        logger.info(f"A股小时数据文件: {self.a_stock_hourly_data.exists()}")
    
    def load_data_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        加载JSONL数据文件
        
        Args:
            file_path: JSONL文件路径
            
        Returns:
            数据列表
        """
        if not file_path.exists():
            logger.warning(f"数据文件不存在: {file_path}")
            return []
        
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # AI-Trader使用每行一个完整JSON对象的方式
                # 但看起来是Alpha Vantage格式，需要特殊处理
                
                # 尝试按行解析
                lines = content.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            item = json.loads(line)
                            
                            # 转换Alpha Vantage格式到统一格式
                            converted_item = self._convert_alpha_vantage_format(item)
                            if converted_item:
                                data.append(converted_item)
                                
                        except json.JSONDecodeError as e:
                            logger.debug(f"JSON解析错误: {e}, 行内容: {line[:100]}...")
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 条数据")
            return data
            
        except Exception as e:
            logger.error(f"加载数据文件失败: {e}")
            return []
    
    def _convert_alpha_vantage_format(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        转换Alpha Vantage格式到统一格式
        
        Args:
            raw_data: 原始Alpha Vantage数据
            
        Returns:
            转换后的数据，如果格式不支持返回None
        """
        try:
            # 检查是否是Alpha Vantage格式
            if 'Meta Data' in raw_data and 'Time Series (Daily)' in raw_data:
                meta = raw_data['Meta Data']
                time_series = raw_data['Time Series (Daily)']
                
                symbol = meta.get('2. Symbol', '')
                name = meta.get('2.1. Name', '')
                
                # 转换每个日期的数据
                converted_items = []
                for date_str, daily_data in time_series.items():
                    converted_item = {
                        'symbol': symbol,
                        'name': name,
                        'date': date_str,
                        'open': float(daily_data.get('1. buy price', 0)),  # Alpha Vantage使用buy price作为open
                        'high': float(daily_data.get('2. high', 0)),
                        'low': float(daily_data.get('3. low', 0)),
                        'close': float(daily_data.get('4. sell price', 0)),  # sell price作为close
                        'volume': int(daily_data.get('5. volume', 0)),
                        'data_source': 'alpha_vantage'
                    }
                    converted_items.append(converted_item)
                
                # 由于原始格式是单个文件包含多日数据，我们返回列表
                # 但为了兼容性，我们只返回最新一天的数据
                if converted_items:
                    # 按日期排序，返回最新一天
                    converted_items.sort(key=lambda x: x['date'], reverse=True)
                    return converted_items[0]
                else:
                    return None
            else:
                # 如果不是Alpha Vantage格式，直接返回
                return raw_data
                
        except Exception as e:
            logger.warning(f"转换Alpha Vantage格式失败: {e}")
            return None
    
    def get_stock_data(self, symbol: str, date: str, market: str = "A") -> Optional[Dict[str, Any]]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            date: 日期，格式 'YYYY-MM-DD'
            market: 市场类型，'A'表示A股，'US'表示美股
            
        Returns:
            股票数据，如果找不到返回None
        """
        # 确定数据文件
        if market.upper() == 'A':
            data_file = self.a_stock_data
            # AI-Trader使用 '000001.SH' 格式
            if '.' not in symbol:
                symbol = f"{symbol}.SH" if symbol.startswith('6') else f"{symbol}.SZ"
        else:
            data_file = self.us_stock_data
        
        # 加载数据（或从缓存获取）
        if data_file not in self.data_cache:
            self.data_cache[data_file] = self.load_data_file(data_file)
        
        data_list = self.data_cache[data_file]
        
        # 查找匹配的数据
        for item in data_list:
            if item.get('symbol') == symbol and item.get('date') == date:
                return item
        
        logger.debug(f"未找到数据: symbol={symbol}, date={date}, market={market}")
        return None
    
    def get_recent_data(self, symbol: str, days: int = 30, market: str = "A") -> List[Dict[str, Any]]:
        """
        获取最近N天的数据
        
        Args:
            symbol: 股票代码
            days: 天数
            market: 市场类型
            
        Returns:
            最近的数据列表
        """
        if market.upper() == 'A':
            data_file = self.a_stock_data
            if '.' not in symbol:
                symbol = f"{symbol}.SH" if symbol.startswith('6') else f"{symbol}.SZ"
        else:
            data_file = self.us_stock_data
        
        # 加载数据
        if data_file not in self.data_cache:
            self.data_cache[data_file] = self.load_data_file(data_file)
        
        data_list = self.data_cache[data_file]
        
        # 过滤该股票的数据
        stock_data = [item for item in data_list if item.get('symbol') == symbol]
        
        # 按日期排序（最近的在前）
        stock_data.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # 返回最近N天的数据
        return stock_data[:days]
    
    def get_historical_prices(self, symbol: str, days: int = 30, market: str = "A") -> List[float]:
        """
        获取历史价格数据
        
        Args:
            symbol: 股票代码
            days: 天数
            market: 市场类型
            
        Returns:
            价格列表（从旧到新）
        """
        recent_data = self.get_recent_data(symbol, days, market)
        
        # 提取收盘价，并按日期升序排列
        prices = []
        for item in sorted(recent_data, key=lambda x: x.get('date', '')):
            close_price = item.get('close')
            if close_price is not None:
                prices.append(float(close_price))
        
        return prices
    
    def get_historical_volumes(self, symbol: str, days: int = 30, market: str = "A") -> List[int]:
        """
        获取历史成交量数据
        
        Args:
            symbol: 股票代码
            days: 天数
            market: 市场类型
            
        Returns:
            成交量列表（从旧到新）
        """
        recent_data = self.get_recent_data(symbol, days, market)
        
        # 提取成交量，并按日期升序排列
        volumes = []
        for item in sorted(recent_data, key=lambda x: x.get('date', '')):
            volume = item.get('volume')
            if volume is not None:
                volumes.append(int(volume))
        
        return volumes
    
    def get_market_overview(self, market: str = "A", date: str = None) -> Dict[str, Any]:
        """
        获取市场概览
        
        Args:
            market: 市场类型
            date: 日期，如果为None则使用最新数据
            
        Returns:
            市场概览信息
        """
        if market.upper() == 'A':
            data_file = self.a_stock_data
        else:
            data_file = self.us_stock_data
        
        # 加载数据
        if data_file not in self.data_cache:
            self.data_cache[data_file] = self.load_data_file(data_file)
        
        data_list = self.data_cache[data_file]
        
        # 如果指定日期，过滤该日期的数据
        if date:
            daily_data = [item for item in data_list if item.get('date') == date]
        else:
            # 获取最新日期的数据
            dates = set(item.get('date') for item in data_list if item.get('date'))
            if not dates:
                return {}
            
            latest_date = max(dates)
            daily_data = [item for item in data_list if item.get('date') == latest_date]
            date = latest_date
        
        if not daily_data:
            return {}
        
        # 计算市场统计
        total_stocks = len(daily_data)
        gainers = sum(1 for item in daily_data if item.get('pct_chg', 0) > 0)
        losers = sum(1 for item in daily_data if item.get('pct_chg', 0) < 0)
        
        # 计算平均涨跌幅
        total_change = sum(item.get('pct_chg', 0) for item in daily_data)
        avg_change = total_change / total_stocks if total_stocks > 0 else 0
        
        # 找出涨跌幅最大的股票
        sorted_by_change = sorted(daily_data, key=lambda x: x.get('pct_chg', 0), reverse=True)
        
        return {
            'date': date,
            'total_stocks': total_stocks,
            'gainers': gainers,
            'losers': losers,
            'unchanged': total_stocks - gainers - losers,
            'avg_change': round(avg_change, 2),
            'top_gainers': [
                {'symbol': item.get('symbol'), 'change': item.get('pct_chg', 0)}
                for item in sorted_by_change[:3]
            ],
            'top_losers': [
                {'symbol': item.get('symbol'), 'change': item.get('pct_chg', 0)}
                for item in sorted_by_change[-3:]
            ]
        }


def test_data_loader():
    """测试数据加载器"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试AI-Trader数据加载器")
    print("=" * 60)
    
    loader = AITraderDataLoader()
    
    # 测试获取A股数据
    print("\n1. 测试A股数据获取:")
    
    # 查看A股数据概览
    a_market_overview = loader.get_market_overview(market="A")
    if a_market_overview:
        print(f"   A股市场概览 ({a_market_overview.get('date', 'N/A')}):")
        print(f"     总股票数: {a_market_overview.get('total_stocks', 0)}")
        print(f"     上涨: {a_market_overview.get('gainers', 0)}, 下跌: {a_market_overview.get('losers', 0)}")
        print(f"     平均涨跌幅: {a_market_overview.get('avg_change', 0)}%")
    else:
        print("   ⚠️ 无法获取A股市场概览")
    
    # 测试获取具体股票数据
    print("\n2. 测试具体股票数据 (000001 - 平安银行):")
    
    # 获取最近30天的价格数据
    prices = loader.get_historical_prices('000001', days=10, market='A')
    if prices:
        print(f"   最近10天收盘价: {prices}")
        print(f"   最新价格: {prices[-1] if prices else 'N/A'}")
        print(f"   价格变化: {((prices[-1] - prices[0]) / prices[0] * 100 if len(prices) >= 2 else 0):.2f}%")
    else:
        print("   ⚠️ 无法获取价格数据")
    
    # 测试获取成交量
    print("\n3. 测试成交量数据:")
    volumes = loader.get_historical_volumes('000001', days=5, market='A')
    if volumes:
        print(f"   最近5天成交量: {volumes}")
        print(f"   平均成交量: {sum(volumes)/len(volumes):,.0f}")
    else:
        print("   ⚠️ 无法获取成交量数据")
    
    # 测试获取单日数据
    print("\n4. 测试单日数据获取:")
    if a_market_overview and 'date' in a_market_overview:
        latest_date = a_market_overview['date']
        daily_data = loader.get_stock_data('000001', latest_date, market='A')
        if daily_data:
            print(f"   {latest_date} 数据:")
            print(f"     开盘: {daily_data.get('open')}")
            print(f"     收盘: {daily_data.get('close')}")
            print(f"     最高: {daily_data.get('high')}")
            print(f"     最低: {daily_data.get('low')}")
            print(f"     涨跌幅: {daily_data.get('pct_chg')}%")
        else:
            print(f"   ⚠️ 无法获取{latest_date}的数据")
    
    print("\n🎯 AI-Trader数据加载器测试完成!")


if __name__ == "__main__":
    test_data_loader()