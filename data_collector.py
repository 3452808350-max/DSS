#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集器 - 统一数据接口
基于Vibe Coding方法论

功能:
- 多数据源统一接口 (baostock, yfinance)
- SQLite 本地存储
- 增量更新
- 数据质量验证

运行方式:
    python data_collector.py --symbol 000001 --days 90
    python data_collector.py --update-daily
    python data_collector.py --test
"""

import baostock as bs
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance 未安装，美股数据功能受限")
import sqlite3
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = PROJECT_ROOT / "database" / "stocks.db"


class StockDataCollector:
    """股票数据采集器 - 统一接口"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._ensure_db_dir()
        self._init_database()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 股票基本信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                code TEXT PRIMARY KEY,
                name TEXT,
                market TEXT,
                list_date TEXT,
                updated_at TEXT
            )
        """)
        
        # 日线行情表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                source TEXT,
                updated_at TEXT,
                UNIQUE(code, date)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_code_date 
            ON daily_prices(code, date)
        """)
        
        conn.commit()
        conn.close()
    
    def fetch_baostock(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """
        从 baostock 获取 A股数据
        
        Args:
            symbol: 股票代码，如 "000001"
            days: 获取天数
        
        Returns:
            DataFrame with columns: date, code, open, high, low, close, volume
        """
        # 转换代码格式
        if symbol.startswith('6'):
            bs_code = f"sh.{symbol}"
        else:
            bs_code = f"sz.{symbol}"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 登录 baostock
        lg = bs.login()
        if lg.error_code != '0':
            raise RuntimeError(f"baostock login failed: {lg.error_msg}")
        
        # 获取数据
        rs = bs.query_history_k_data_plus(
            bs_code,
            'date,code,open,high,low,close,volume,amount',
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            frequency='d'
        )
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if not data_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        df['source'] = 'baostock'
        
        return df
    
    def fetch_yfinance(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """
        从 yfinance 获取美股数据
        
        Args:
            symbol: 股票代码，如 "AAPL"
            days: 获取天数
        
        Returns:
            DataFrame
        """
        if not YFINANCE_AVAILABLE:
            print("  ⚠️  yfinance 未安装，跳过")
            return pd.DataFrame()
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d")
        
            if df.empty:
                return pd.DataFrame()
            
            df = df.reset_index()
            df['code'] = symbol.upper()
            df['source'] = 'yfinance'
            
            # 统一列名
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            return df[['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'source']]
        except Exception as e:
            print(f"  ❌ yfinance 获取失败: {e}")
            return pd.DataFrame()
    
    def save_to_db(self, df: pd.DataFrame, code: str):
        """保存数据到 SQLite"""
        if df.empty:
            print(f"  ⚠️  无数据可保存: {code}")
            return
        
        conn = sqlite3.connect(str(self.db_path))
        
        # 确保 code 列存在
        if 'code' not in df.columns:
            df['code'] = code
        
        df['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 使用 INSERT OR REPLACE 实现 upsert
        for _, row in df.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO daily_prices 
                (code, date, open, high, low, close, volume, source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['code'], row['date'], 
                float(row.get('open', 0) or 0),
                float(row.get('high', 0) or 0),
                float(row.get('low', 0) or 0),
                float(row.get('close', 0) or 0),
                float(row.get('volume', 0) or 0),
                row.get('source', 'unknown'),
                row['updated_at']
            ))
        
        conn.commit()
        conn.close()
    
    def get_from_db(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """从数据库读取数据"""
        conn = sqlite3.connect(str(self.db_path))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = pd.read_sql(f"""
            SELECT * FROM daily_prices 
            WHERE code = '{symbol}' 
            AND date >= '{start_date.strftime('%Y-%m-%d')}'
            ORDER BY date
        """, conn)
        
        conn.close()
        return df
    
    def collect_stock(self, symbol: str, market: str = 'cn', days: int = 90) -> pd.DataFrame:
        """
        采集单只股票数据
        
        Args:
            symbol: 股票代码
            market: 市场类型 ('cn' 或 'us')
            days: 天数
        
        Returns:
            DataFrame
        """
        print(f"  📥 采集 {symbol} ({market}) 最近 {days} 天数据...")
        
        try:
            if market == 'cn':
                df = self.fetch_baostock(symbol, days)
            else:
                df = self.fetch_yfinance(symbol, days)
            
            if not df.empty:
                self.save_to_db(df, symbol)
                print(f"  ✅ 成功获取 {len(df)} 条数据")
            else:
                print(f"  ⚠️  未获取到数据")
            
            return df
            
        except Exception as e:
            print(f"  ❌ 采集失败: {e}")
            return pd.DataFrame()
    
    def update_watchlist(self, symbols: List[str], market: str = 'cn'):
        """
        批量更新关注列表
        
        Args:
            symbols: 股票代码列表
            market: 市场类型
        """
        print(f"\n🔄 批量更新 {len(symbols)} 只股票...")
        
        success = 0
        for symbol in symbols:
            df = self.collect_stock(symbol, market)
            if not df.empty:
                success += 1
        
        print(f"\n📊 更新完成: {success}/{len(symbols)} 成功")
    
    def get_latest_date(self, symbol: str) -> Optional[str]:
        """获取数据库中最新日期"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT MAX(date) FROM daily_prices WHERE code = ?
        """, (symbol,))
        result = cursor.fetchone()[0]
        conn.close()
        return result


# A股关注列表
CN_WATCHLIST = [
    '000001',  # 平安银行
    '000002',  # 万科A
    '600519',  # 贵州茅台
    '601318',  # 中国平安
    '600036',  # 招商银行
    '000858',  # 五粮液
    '002415',  # 海康威视
    '300750',  # 宁德时代
]

# 美股关注列表
US_WATCHLIST = [
    'AAPL',    # 苹果
    'MSFT',    # 微软
    'GOOGL',   # 谷歌
    'AMZN',    # 亚马逊
    'TSLA',    # 特斯拉
]


def test():
    """测试数据采集器"""
    print("🧪 测试数据采集器...")
    print("=" * 50)
    
    collector = StockDataCollector()
    
    # 测试 A股
    print("\n📌 测试 A股 (000001):")
    df = collector.collect_stock('000001', 'cn', 30)
    if not df.empty:
        print(f"  最新数据: {df['date'].iloc[-1]} ¥{df['close'].iloc[-1]}")
    
    # 测试美股
    print("\n📌 测试美股 (AAPL):")
    df = collector.collect_stock('AAPL', 'us', 30)
    if not df.empty:
        print(f"  最新数据: {df['date'].iloc[-1]} ${df['close'].iloc[-1]}")
    
    # 测试批量更新
    print("\n📌 测试批量更新:")
    collector.update_watchlist(['000001', '600519'], 'cn')
    
    print("\n" + "=" * 50)
    print("✅ 测试完成!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='股票数据采集器')
    parser.add_argument('--symbol', type=str, help='股票代码')
    parser.add_argument('--market', type=str, default='cn', choices=['cn', 'us'], help='市场类型')
    parser.add_argument('--days', type=int, default=90, help='获取天数')
    parser.add_argument('--update-daily', action='store_true', help='更新每日关注列表')
    parser.add_argument('--test', action='store_true', help='运行测试')
    
    args = parser.parse_args()
    
    if args.test:
        test()
    elif args.update_daily:
        collector = StockDataCollector()
        collector.update_watchlist(CN_WATCHLIST, 'cn')
        collector.update_watchlist(US_WATCHLIST, 'us')
    elif args.symbol:
        collector = StockDataCollector()
        collector.collect_stock(args.symbol, args.market, args.days)
    else:
        parser.print_help()
