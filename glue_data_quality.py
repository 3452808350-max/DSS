#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量监控模块 - 可执行的验证检查点
基于Vibe Coding方法论：每个规则可独立提示修改

运行方式:
    python glue_data_quality.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Callable, List, Optional
from dataclasses import dataclass
from enum import Enum

class CheckStatus(Enum):
    """检查状态"""
    PASS = "✓ PASS"
    FAIL = "✗ FAIL"
    ERROR = "⚠ ERROR"

@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: CheckStatus
    score: float
    threshold: float
    message: str
    details: Optional[dict] = None

class DataQualityRule:
    """数据质量规则基类"""
    
    def __init__(self, name: str, check_func: Callable, threshold: float, description: str = ""):
        self.name = name
        self.check_func = check_func
        self.threshold = threshold
        self.description = description
    
    def execute(self, df: pd.DataFrame) -> CheckResult:
        """执行检查"""
        try:
            score = self.check_func(df)
            passed = score >= self.threshold
            
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS if passed else CheckStatus.FAIL,
                score=score,
                threshold=self.threshold,
                message=f"{self.description}: {score:.2%} (阈值: {self.threshold:.2%})"
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=CheckStatus.ERROR,
                score=0.0,
                threshold=self.threshold,
                message=f"检查执行错误: {str(e)}"
            )

class DataQualityMonitor:
    """
    数据质量监控器（Vibe Coding：可独立提示修改）
    
    可通过自然语言提示AI修改：
    - "添加价格异常值检测规则"
    - "修改完整性检查阈值为98%"
    """
    
    def __init__(self):
        self.rules: List[DataQualityRule] = []
    
    def add_rule(self, rule: DataQualityRule):
        """添加质量规则"""
        self.rules.append(rule)
    
    def validate(self, df: pd.DataFrame) -> List[CheckResult]:
        """执行所有质量检查"""
        results = []
        for rule in self.rules:
            result = rule.execute(df)
            results.append(result)
        return results
    
    def validate_critical(self, df: pd.DataFrame) -> bool:
        """
        验证关键规则（必须全部通过）
        
        Returns:
            是否所有关键规则都通过
        """
        results = self.validate(df)
        critical_results = [r for r in results if r.name.startswith('critical_')]
        return all(r.status == CheckStatus.PASS for r in critical_results)
    
    def print_report(self, results: List[CheckResult]):
        """打印质量报告"""
        print("=" * 60)
        print("📊 数据质量报告")
        print("=" * 60)
        
        pass_count = sum(1 for r in results if r.status == CheckStatus.PASS)
        fail_count = sum(1 for r in results if r.status == CheckStatus.FAIL)
        error_count = sum(1 for r in results if r.status == CheckStatus.ERROR)
        
        for result in results:
            status_icon = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"{status_icon} {result.name:30s} | {result.message}")
        
        print("-" * 60)
        print(f"总计: {pass_count} 通过 | {fail_count} 失败 | {error_count} 错误")
        print("=" * 60)

# 预定义规则工厂
def create_stock_data_monitor() -> DataQualityMonitor:
    """
    创建股票数据质量监控器（预配置）
    
    Returns:
        配置好的监控器实例
    """
    monitor = DataQualityMonitor()
    
    # 1. 完整性检查
    monitor.add_rule(DataQualityRule(
        name="critical_completeness",
        check_func=lambda df: 1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1]),
        threshold=0.98,
        description="数据完整性"
    ))
    
    # 2. 及时性检查
    monitor.add_rule(DataQualityRule(
        name="critical_timeliness",
        check_func=lambda df: 1.0 if len(df) > 0 and 
            (datetime.now() - pd.to_datetime(df['date'].iloc[-1])).days <= 1 
            else 0.0,
        threshold=1.0,
        description="数据及时性"
    ))
    
    # 3. 价格合理性检查
    monitor.add_rule(DataQualityRule(
        name="critical_price_validity",
        check_func=lambda df: ((df['close'] > 0) & (df['close'] < 100000)).mean(),
        threshold=1.0,
        description="价格有效性"
    ))
    
    # 4. 异常值检查
    monitor.add_rule(DataQualityRule(
        name="outlier_check",
        check_func=lambda df: 1 - (df['close'] > df['close'].quantile(0.995)).mean(),
        threshold=0.995,
        description="异常值比例"
    ))
    
    # 5. 成交量检查
    monitor.add_rule(DataQualityRule(
        name="volume_validity",
        check_func=lambda df: ((df['volume'] >= 0) & (df['volume'] < 1e12)).mean(),
        threshold=1.0,
        description="成交量有效性"
    ))
    
    # 6. 价格连续性检查
    monitor.add_rule(DataQualityRule(
        name="price_continuity",
        check_func=lambda df: 1 - (df['close'].diff().abs() > df['close'] * 0.2).mean(),
        threshold=0.99,
        description="价格连续性（单日波动<20%）"
    ))
    
    # 7. 数据量检查
    monitor.add_rule(DataQualityRule(
        name="data_volume",
        check_func=lambda df: min(len(df) / 100, 1.0),  # 至少100条数据
        threshold=0.5,
        description="数据量充足性"
    ))
    
    return monitor

class DataQualityAlert:
    """数据质量告警系统"""
    
    def __init__(self, monitor: DataQualityMonitor):
        self.monitor = monitor
        self.alert_history: List[Dict] = []
    
    def check_and_alert(self, df: pd.DataFrame, alert_callback: Optional[Callable] = None):
        """
        检查并触发告警
        
        Args:
            df: 待检查数据
            alert_callback: 告警回调函数，接收失败结果列表
        """
        results = self.monitor.validate(df)
        failures = [r for r in results if r.status != CheckStatus.PASS]
        
        if failures:
            alert_info = {
                'timestamp': datetime.now(),
                'failures': failures,
                'data_shape': df.shape
            }
            self.alert_history.append(alert_info)
            
            if alert_callback:
                alert_callback(failures)
            else:
                # 默认告警输出
                print("\n🚨 数据质量告警")
                print("-" * 40)
                for f in failures:
                    print(f"  ✗ {f.name}: {f.message}")
        
        return len(failures) == 0
    
    def get_alert_summary(self, days: int = 7) -> Dict:
        """获取告警摘要"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_alerts = [a for a in self.alert_history if a['timestamp'] > cutoff]
        
        return {
            'total_alerts': len(recent_alerts),
            'unique_issues': len(set(
                f.name for a in recent_alerts for f in a['failures']
            )),
            'alert_frequency': len(recent_alerts) / days
        }

# 验证检查点
if __name__ == "__main__":
    print("=" * 60)
    print("数据质量监控模块 - 验证测试")
    print("=" * 60)
    
    # 创建监控器
    monitor = create_stock_data_monitor()
    
    # 测试1：正常数据
    print("\n📊 测试1: 正常数据质量检查")
    normal_data = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
        'open': np.random.uniform(10, 15, 100),
        'close': np.random.uniform(10, 15, 100),
        'high': np.random.uniform(15, 16, 100),
        'low': np.random.uniform(9, 10, 100),
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    # 确保high >= close >= low
    normal_data['high'] = np.maximum(normal_data['high'], normal_data['close'])
    normal_data['low'] = np.minimum(normal_data['low'], normal_data['close'])
    
    results = monitor.validate(normal_data)
    monitor.print_report(results)
    
    # 测试2：异常数据
    print("\n📊 测试2: 异常数据质量检查")
    bad_data = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=50, freq='D'),
        'open': [10] * 50,
        'close': [10] * 25 + [np.nan] * 25,  # 缺失值
        'high': [15] * 50,
        'low': [9] * 50,
        'volume': [1000000] * 50
    })
    
    results = monitor.validate(bad_data)
    monitor.print_report(results)
    
    # 测试3：告警系统
    print("\n📊 测试3: 告警系统测试")
    alert_system = DataQualityAlert(monitor)
    
    def custom_alert(failures):
        print(f"\n🚨 自定义告警: 发现 {len(failures)} 个问题")
    
    alert_system.check_and_alert(bad_data, custom_alert)
    
    summary = alert_system.get_alert_summary(days=1)
    print(f"\n告警摘要: {summary}")
    
    # 测试4：关键规则验证
    print("\n📊 测试4: 关键规则验证")
    is_valid = monitor.validate_critical(normal_data)
    print(f"  关键规则验证结果: {'✓ 通过' if is_valid else '✗ 失败'}")
    
    print("\n" + "=" * 60)
    print("✅ 所有验证测试完成")
    print("=" * 60)
