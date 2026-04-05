#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源胶水层 - 统一接口封装
基于Vibe Coding方法论：每个模块可独立提示修改

运行方式:
    python glue_datasource.py
"""

import akshare as ak
import yfinance as yf
import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

class DataSource(ABC):
    """
    数据源抽象基类（Vibe Coding友好设计）
    
    可通过自然语言提示AI修改：
    - "给AKShare添加重试机制"
    - "给YFinance添加代理支持"
    """
    
    @abstractmethod
    def fetch(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            days: 获取天数
        
        Returns:
            标准化DataFrame (date, open, close, high, low, volume)
        """
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """验证股票代码是否有效"""
        pass

class AKShareSource(DataSource):
    """AKShare数据源（A股）"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    def fetch(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """获取A股数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 胶水代码：调用AKShare，标准化输出
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq"
        )
        
        return self._standardize(df)
    
    def _standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名（胶水转换）"""
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        })
        df['date'] = pd.to_datetime(df['date'])
        return df[['date', 'open', 'close', 'high', 'low', 'volume']]
    
    def validate_symbol(self, symbol: str) -> bool:
        """验证A股代码"""
        try:
            df = ak.stock_zh_a_spot_em()
            return symbol in df['代码'].values
        except:
            return False

class YFinanceSource(DataSource):
    """YFinance数据源（美股）"""
    
    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy
    
    def fetch(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """获取美股数据"""
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d", proxy=self.proxy)
        
        return self._standardize(df)
    
    def _standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名（与AKShare保持一致）"""
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'Close': 'close',
            'High': 'high',
            'Low': 'low',
            'Volume': 'volume'
        })
        return df[['date', 'open', 'close', 'high', 'low', 'volume']]
    
    def validate_symbol(self, symbol: str) -> bool:
        """验证美股代码"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'symbol' in info
        except:
            return False

class DataSourceFactory:
    """数据源工厂（胶水代码）"""
    
    _sources = {
        'A股': AKShareSource,
        '美股': YFinanceSource,
    }
    
    @classmethod
    def create(cls, market: str, **kwargs) -> DataSource:
        """
        创建数据源实例
        
        Args:
            market: 市场类型 ('A股', '美股')
            **kwargs: 传递给数据源的参数
        
        Returns:
            数据源实例
        """
        if market not in cls._sources:
            raise ValueError(f"不支持的市场: {market}。支持: {list(cls._sources.keys())}")
        
        return cls._sources[market](**kwargs)
    
    @classmethod
    def register(cls, name: str, source_class: type):
        """注册新的数据源（扩展点）"""
        cls._sources[name] = source_class

class UnifiedDataManager:
    """统一数据管理器（胶水代码）"""
    
    def __init__(self):
        self._sources: dict[str, DataSource] = {}
    
    def add_source(self, name: str, source: DataSource):
        """添加数据源"""
        self._sources[name] = source
    
    def fetch(self, market: str, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        统一获取数据接口
        
        Args:
            market: 市场类型
            symbol: 股票代码
            days: 获取天数
        
        Returns:
            标准化DataFrame
        """
        if market not in self._sources:
            # 自动创建默认数据源
            self._sources[market] = DataSourceFactory.create(market)
        
        return self._sources[market].fetch(symbol, days)
    
    def fetch_multi(self, requests: list[dict]) -> dict[str, pd.DataFrame]:
        """
        批量获取数据
        
        Args:
            requests: 请求列表 [{'market': 'A股', 'symbol': '000001', 'days': 30}, ...]
        
        Returns:
            结果字典 {'000001': DataFrame, ...}
        """
        results = {}
        for req in requests:
            key = f"{req['market']}:{req['symbol']}"
            results[key] = self.fetch(
                req['market'], 
                req['symbol'], 
                req.get('days', 30)
            )
        return results

# 验证检查点
if __name__ == "__main__":
    print("=" * 60)
    print("数据源胶水层 - 验证测试")
    print("=" * 60)
    
    # 测试1：AKShare数据源
    print("\n📊 测试1: AKShare数据源 (A股)")
    try:
        ak_source = AKShareSource()
        data = ak_source.fetch("000001", days=10)
        print(f"  ✓ 数据获取成功，共 {len(data)} 条记录")
        print(f"  ✓ 数据列: {list(data.columns)}")
        assert 'close' in data.columns
        print("  ✓ 数据格式验证通过")
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
    
    # 测试2：YFinance数据源
    print("\n📊 测试2: YFinance数据源 (美股)")
    try:
        yf_source = YFinanceSource()
        data = yf_source.fetch("AAPL", days=10)
        print(f"  ✓ 数据获取成功，共 {len(data)} 条记录")
        print(f"  ✓ 数据列: {list(data.columns)}")
        assert 'close' in data.columns
        print("  ✓ 数据格式验证通过")
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
    
    # 测试3：统一数据管理器
    print("\n📊 测试3: 统一数据管理器")
    try:
        manager = UnifiedDataManager()
        
        # 批量获取
        requests = [
            {'market': 'A股', 'symbol': '000001', 'days': 5},
            {'market': '美股', 'symbol': 'AAPL', 'days': 5},
        ]
        results = manager.fetch_multi(requests)
        print(f"  ✓ 批量获取成功，共 {len(results)} 个结果")
        for key, df in results.items():
            print(f"    - {key}: {len(df)} 条记录")
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
    
    # 测试4：数据源工厂
    print("\n📊 测试4: 数据源工厂")
    try:
        source = DataSourceFactory.create('A股')
        print(f"  ✓ 工厂创建成功: {type(source).__name__}")
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 所有验证测试完成")
    print("=" * 60)
