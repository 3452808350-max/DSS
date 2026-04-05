#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量监控模块
基于Vibe Coding方法论

功能:
- 数据完整性检查
- 数据及时性检查
- 异常值检测
- 价格合理性验证

运行方式:
    python data_quality.py --symbol 000001
    python data_quality.py --check-all
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = PROJECT_ROOT / "database" / "stocks.db"


class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
    
    def check_completeness(self, df: pd.DataFrame) -> float:
        """
        检查数据完整性
        返回完整率 (0-1)
        """
        if df.empty:
            return 0.0
        
        total_cells = df.shape[0] * df.shape[1]
        non_null = df.count().sum()
        return non_null / total_cells
    
    def check_timeliness(self, df: pd.DataFrame) -> float:
        """
        检查数据及时性
        返回是否最新 (0-1)
        """
        if df.empty or 'date' not in df.columns:
            return 0.0
        
        latest = pd.to_datetime(df['date'].max())
        now = datetime.now()
        
        # 如果最新数据是今天或昨天，认为及时
        days_diff = (now - latest).days
        if days_diff <= 1:
            return 1.0
        elif days_diff <= 3:
            return 0.7
        elif days_diff <= 7:
            return 0.3
        else:
            return 0.0
    
    def check_outliers(self, df: pd.DataFrame) -> float:
        """
        检查异常值
        返回正常率 (0-1)
        """
        if df.empty or 'close' not in df.columns:
            return 1.0
        
        prices = df['close'].dropna()
        if len(prices) == 0:
            return 1.0
        
        # 使用 IQR 方法检测异常值
        Q1 = prices.quantile(0.25)
        Q3 = prices.quantile(0.75)
        IQR = Q3 - Q1
        
        lower = Q1 - 3 * IQR
        upper = Q3 + 3 * IQR
        
        outliers = (prices < lower) | (prices > upper)
        return 1 - outliers.mean()
    
    def check_price_reasonableness(self, df: pd.DataFrame) -> float:
        """
        检查价格合理性
        """
        if df.empty or 'close' not in df.columns:
            return 0.0
        
        prices = df['close'].dropna()
        if len(prices) == 0:
            return 0.0
        
        # 价格应该在合理范围内 (对于A股: 0.01 - 10000)
        valid = (prices > 0.01) & (prices < 10000)
        return valid.mean()
    
    def check_volume(self, df: pd.DataFrame) -> float:
        """
        检查成交量合理性
        """
        if df.empty or 'volume' not in df.columns:
            return 0.0
        
        volumes = df['volume'].dropna()
        if len(volumes) == 0:
            return 0.0
        
        # 成交量应该 > 0
        valid = volumes > 0
        return valid.mean()
    
    def check_gaps(self, df: pd.DataFrame) -> float:
        """
        检查数据是否有跳空缺口过大
        """
        if df.empty or 'close' not in df.columns:
            return 1.0
        
        prices = df['close'].dropna()
        if len(prices) < 2:
            return 1.0
        
        # 计算日收益率
        returns = prices.pct_change().abs()
        
        # 超过 20% 的跳空视为异常
        anomalies = returns > 0.20
        return 1 - anomalies.mean()
    
    def validate(self, symbol: str, days: int = 90) -> Dict:
        """
        执行完整的数据质量检查
        
        Returns:
            dict: 质量报告
        """
        # 读取数据
        conn = sqlite3.connect(str(self.db_path))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 处理股票代码格式
        code_query = symbol
        if not symbol.startswith('sh.') and not symbol.startswith('sz.'):
            # 转换为 baostock 格式
            if symbol.startswith('6'):
                code_query = f"sh.{symbol}"
            else:
                code_query = f"sz.{symbol}"
        
        df = pd.read_sql(f"""
            SELECT * FROM daily_prices 
            WHERE code = '{code_query}'
            AND date >= '{start_date.strftime('%Y-%m-%d')}'
            ORDER BY date
        """, conn)
        conn.close()
        
        if df.empty:
            return {
                'symbol': symbol,
                'status': 'NO_DATA',
                'score': 0.0,
                'message': '数据库中无数据'
            }
        
        # 执行各项检查
        results = {
            'symbol': symbol,
            'data_count': len(df),
            'date_range': f"{df['date'].min()} ~ {df['date'].max()}",
            'completeness': self.check_completeness(df),
            'timeliness': self.check_timeliness(df),
            'outliers': self.check_outliers(df),
            'price_reasonableness': self.check_price_reasonableness(df),
            'volume': self.check_volume(df),
            'gaps': self.check_gaps(df),
        }
        
        # 计算综合分数
        weights = {
            'completeness': 0.2,
            'timeliness': 0.25,
            'outliers': 0.15,
            'price_reasonableness': 0.2,
            'volume': 0.1,
            'gaps': 0.1
        }
        
        total_score = sum(
            results[key] * weights[key] 
            for key in weights
        )
        
        results['score'] = total_score
        
        # 判断状态
        if total_score >= 0.9:
            results['status'] = 'EXCELLENT'
        elif total_score >= 0.75:
            results['status'] = 'GOOD'
        elif total_score >= 0.6:
            results['status'] = 'FAIR'
        else:
            results['status'] = 'POOR'
        
        return results
    
    def print_report(self, results: Dict):
        """打印质量报告"""
        print("=" * 60)
        print(f"📊 数据质量报告: {results['symbol']}")
        print("=" * 60)
        print(f"📅 数据范围: {results.get('date_range', 'N/A')}")
        print(f"📈 数据条数: {results.get('data_count', 0)}")
        print()
        
        checks = [
            ('completeness', '数据完整性'),
            ('timeliness', '数据及时性'),
            ('outliers', '异常值检测'),
            ('price_reasonableness', '价格合理性'),
            ('volume', '成交量有效性'),
            ('gaps', '跳空缺口检测'),
        ]
        
        for key, name in checks:
            score = results.get(key, 0)
            status = "✅" if score >= 0.9 else "⚠️" if score >= 0.7 else "❌"
            print(f"  {status} {name}: {score:.1%}")
        
        print()
        print("-" * 60)
        print(f"🏆 综合得分: {results['score']:.1%} ({results['status']})")
        print("=" * 60)
    
    def check_all(self, symbols: List[str] = None) -> List[Dict]:
        """批量检查所有股票"""
        if symbols is None:
            # 从数据库获取所有股票
            conn = sqlite3.connect(str(self.db_path))
            df = pd.read_sql("SELECT DISTINCT code FROM daily_prices", conn)
            conn.close()
            symbols = df['code'].tolist()
        
        print(f"\n🔍 批量检查 {len(symbols)} 只股票...")
        print("=" * 60)
        
        results = []
        for symbol in symbols:
            result = self.validate(symbol)
            results.append(result)
            
            # 快速显示
            status_icon = {
                'EXCELLENT': '✅',
                'GOOD': '🟢',
                'FAIR': '🟡',
                'POOR': '🔴',
                'NO_DATA': '⚪'
            }.get(result['status'], '❓')
            
            print(f"  {status_icon} {symbol}: {result['score']:.0%} ({result['status']})")
        
        # 统计
        excellent = sum(1 for r in results if r['status'] == 'EXCELLENT')
        good = sum(1 for r in results if r['status'] == 'GOOD')
        fair = sum(1 for r in results if r['status'] == 'FAIR')
        poor = sum(1 for r in results if r['status'] == 'POOR')
        no_data = sum(1 for r in results if r['status'] == 'NO_DATA')
        
        print()
        print("📊 统计:")
        print(f"  ✅ 优秀: {excellent}")
        print(f"  🟢 良好: {good}")
        print(f"  🟡 一般: {fair}")
        print(f"  🔴 较差: {poor}")
        print(f"  ⚪ 无数据: {no_data}")
        
        return results


def test():
    """测试数据质量监控"""
    print("🧪 测试数据质量监控...")
    print()
    
    monitor = DataQualityMonitor()
    
    # 测试单只股票
    print("📌 测试单只股票:")
    result = monitor.validate('000001')
    monitor.print_report(result)
    
    # 批量检查
    print("\n📌 批量检查:")
    monitor.check_all(['000001', '600519', 'AAPL'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='数据质量监控')
    parser.add_argument('--symbol', type=str, help='股票代码')
    parser.add_argument('--days', type=int, default=90, help='检查天数')
    parser.add_argument('--check-all', action='store_true', help='检查所有股票')
    
    args = parser.parse_args()
    
    monitor = DataQualityMonitor()
    
    if args.symbol:
        result = monitor.validate(args.symbol, args.days)
        monitor.print_report(result)
    elif args.check_all:
        monitor.check_all()
    else:
        test()
