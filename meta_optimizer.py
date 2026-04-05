#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
递归自优化模块 - 系统的自我评估-反馈-改进闭环
基于Vibe Coding方法论：实现递归自优化生成系统

运行方式:
    python meta_optimizer.py
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os

class OptimizationAction(Enum):
    """优化动作类型"""
    ADJUST_PARAMETER = "调整参数"
    SWITCH_STRATEGY = "切换策略"
    SWITCH_DATASOURCE = "切换数据源"
    RETRAIN_MODEL = "重新训练"
    ALERT_HUMAN = "人工介入"
    NO_ACTION = "无需操作"

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    data_quality_score: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_return': self.total_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'num_trades': self.num_trades,
            'data_quality_score': self.data_quality_score
        }

@dataclass
class OptimizationDecision:
    """优化决策"""
    action: OptimizationAction
    reason: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'action': self.action.value,
            'reason': self.reason,
            'parameters': self.parameters,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }

class PerformanceTracker:
    """性能追踪器"""
    
    def __init__(self, history_file: str = "performance_history.json"):
        self.history_file = history_file
        self.history: List[PerformanceMetrics] = []
        self.load_history()
    
    def load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        self.history.append(PerformanceMetrics(
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            total_return=item['total_return'],
                            sharpe_ratio=item['sharpe_ratio'],
                            max_drawdown=item['max_drawdown'],
                            win_rate=item['win_rate'],
                            num_trades=item['num_trades'],
                            data_quality_score=item['data_quality_score']
                        ))
            except Exception as e:
                print(f"加载历史记录失败: {e}")
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump([h.to_dict() for h in self.history], f, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def record(self, metrics: PerformanceMetrics):
        """记录性能指标"""
        self.history.append(metrics)
        self.save_history()
    
    def get_recent(self, days: int = 30) -> List[PerformanceMetrics]:
        """获取最近N天的记录"""
        cutoff = datetime.now() - timedelta(days=days)
        return [h for h in self.history if h.timestamp > cutoff]
    
    def detect_degradation(self, window: int = 7, threshold: float = -0.1) -> bool:
        """
        检测性能退化
        
        Args:
            window: 检测窗口（天）
            threshold: 退化阈值
        
        Returns:
            是否检测到退化
        """
        recent = self.get_recent(window)
        if len(recent) < 2:
            return False
        
        # 计算趋势
        returns = [h.total_return for h in recent]
        trend = np.polyfit(range(len(returns)), returns, 1)[0]
        
        return trend < threshold
    
    def get_trend(self, metric: str = 'total_return', window: int = 30) -> float:
        """获取指标趋势"""
        recent = self.get_recent(window)
        if len(recent) < 2:
            return 0.0
        
        values = [getattr(h, metric) for h in recent]
        return np.polyfit(range(len(values)), values, 1)[0]

class DataSourceEvaluator:
    """数据源评估器"""
    
    def __init__(self):
        self.source_stats: Dict[str, Dict] = {}
    
    def record_quality(self, source_name: str, quality_score: float, latency: float):
        """记录数据源质量"""
        if source_name not in self.source_stats:
            self.source_stats[source_name] = {
                'quality_scores': [],
                'latencies': [],
                'failure_count': 0
            }
        
        self.source_stats[source_name]['quality_scores'].append(quality_score)
        self.source_stats[source_name]['latencies'].append(latency)
    
    def record_failure(self, source_name: str):
        """记录数据源故障"""
        if source_name in self.source_stats:
            self.source_stats[source_name]['failure_count'] += 1
    
    def get_best_source(self) -> Optional[str]:
        """获取最佳数据源"""
        if not self.source_stats:
            return None
        
        scores = {}
        for name, stats in self.source_stats.items():
            if stats['quality_scores']:
                avg_quality = np.mean(stats['quality_scores'][-10:])
                avg_latency = np.mean(stats['latencies'][-10:])
                failure_rate = stats['failure_count'] / max(len(stats['quality_scores']), 1)
                
                # 综合评分
                scores[name] = avg_quality * 0.5 + (1 / (1 + avg_latency)) * 0.3 + (1 - failure_rate) * 0.2
        
        return max(scores, key=scores.get) if scores else None

class MetaOptimizer:
    """
    元优化器 - 递归自优化系统的核心
    
    实现自我评估-反馈-改进的闭环
    """
    
    def __init__(self, 
                 performance_tracker: Optional[PerformanceTracker] = None,
                 datasource_evaluator: Optional[DataSourceEvaluator] = None):
        self.performance_tracker = performance_tracker or PerformanceTracker()
        self.datasource_evaluator = datasource_evaluator or DataSourceEvaluator()
        self.decision_history: List[OptimizationDecision] = []
        self.optimization_rules: List[Callable] = []
    
    def add_optimization_rule(self, rule: Callable):
        """添加优化规则"""
        self.optimization_rules.append(rule)
    
    def evaluate(self, 
                 current_metrics: PerformanceMetrics,
                 strategy_params: Dict[str, Any],
                 active_datasource: str) -> OptimizationDecision:
        """
        评估当前状态并生成优化决策
        
        Args:
            current_metrics: 当前性能指标
            strategy_params: 策略参数
            active_datasource: 当前数据源
        
        Returns:
            优化决策
        """
        # 记录当前性能
        self.performance_tracker.record(current_metrics)
        
        # 执行所有优化规则
        for rule in self.optimization_rules:
            decision = rule(self, current_metrics, strategy_params, active_datasource)
            if decision and decision.action != OptimizationAction.NO_ACTION:
                self.decision_history.append(decision)
                return decision
        
        # 默认决策
        return OptimizationDecision(
            action=OptimizationAction.NO_ACTION,
            reason="所有指标正常，无需优化"
        )
    
    def get_optimization_summary(self) -> Dict:
        """获取优化摘要"""
        recent_decisions = [d for d in self.decision_history 
                          if d.timestamp > datetime.now() - timedelta(days=30)]
        
        action_counts = {}
        for d in recent_decisions:
            action = d.action.value
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            'total_decisions': len(self.decision_history),
            'recent_decisions': len(recent_decisions),
            'action_distribution': action_counts,
            'performance_trend': self.performance_tracker.get_trend('total_return', 30),
            'sharpe_trend': self.performance_tracker.get_trend('sharpe_ratio', 30)
        }

# 预定义优化规则
def strategy_failure_rule(optimizer: MetaOptimizer,
                         metrics: PerformanceMetrics,
                         params: Dict[str, Any],
                         datasource: str) -> Optional[OptimizationDecision]:
    """策略失效检测规则"""
    if optimizer.performance_tracker.detect_degradation(window=7, threshold=-0.05):
        return OptimizationDecision(
            action=OptimizationAction.SWITCH_STRATEGY,
            reason="策略性能连续7天下降，可能已失效",
            parameters={'current_return': metrics.total_return},
            confidence=0.7
        )
    return None

def datasource_quality_rule(optimizer: MetaOptimizer,
                           metrics: PerformanceMetrics,
                           params: Dict[str, Any],
                           datasource: str) -> Optional[OptimizationDecision]:
    """数据源质量检测规则"""
    if metrics.data_quality_score < 0.8:
        best_source = optimizer.datasource_evaluator.get_best_source()
        if best_source and best_source != datasource:
            return OptimizationDecision(
                action=OptimizationAction.SWITCH_DATASOURCE,
                reason=f"当前数据源质量评分{metrics.data_quality_score:.2f}低于阈值，切换到更优数据源",
                parameters={'new_datasource': best_source},
                confidence=0.8
            )
    return None

def parameter_optimization_rule(optimizer: MetaOptimizer,
                               metrics: PerformanceMetrics,
                               params: Dict[str, Any],
                               datasource: str) -> Optional[OptimizationDecision]:
    """参数优化规则"""
    # 如果夏普比率低于1，建议调整参数
    if metrics.sharpe_ratio < 1.0 and metrics.num_trades > 10:
        return OptimizationDecision(
            action=OptimizationAction.ADJUST_PARAMETER,
            reason=f"夏普比率{metrics.sharpe_ratio:.2f}低于目标，建议调整策略参数",
            parameters={'target_sharpe': 1.5},
            confidence=0.6
        )
    return None

def human_intervention_rule(optimizer: MetaOptimizer,
                           metrics: PerformanceMetrics,
                           params: Dict[str, Any],
                           datasource: str) -> Optional[OptimizationDecision]:
    """人工介入规则"""
    # 如果最大回撤超过20%，建议人工介入
    if metrics.max_drawdown < -0.2:
        return OptimizationDecision(
            action=OptimizationAction.ALERT_HUMAN,
            reason=f"最大回撤{metrics.max_drawdown*100:.2f}%超过阈值，建议人工审核",
            parameters={'max_drawdown': metrics.max_drawdown},
            confidence=0.9
        )
    return None

def create_default_optimizer() -> MetaOptimizer:
    """创建默认优化器（预配置所有规则）"""
    optimizer = MetaOptimizer()
    
    # 添加所有优化规则
    optimizer.add_optimization_rule(strategy_failure_rule)
    optimizer.add_optimization_rule(datasource_quality_rule)
    optimizer.add_optimization_rule(parameter_optimization_rule)
    optimizer.add_optimization_rule(human_intervention_rule)
    
    return optimizer

# 验证检查点
if __name__ == "__main__":
    print("=" * 60)
    print("递归自优化模块 - 验证测试")
    print("=" * 60)
    
    # 创建优化器
    optimizer = create_default_optimizer()
    
    # 测试1：正常性能
    print("\n🔄 测试1: 正常性能评估")
    normal_metrics = PerformanceMetrics(
        timestamp=datetime.now(),
        total_return=0.15,
        sharpe_ratio=1.5,
        max_drawdown=-0.05,
        win_rate=0.6,
        num_trades=50,
        data_quality_score=0.95
    )
    
    decision = optimizer.evaluate(
        normal_metrics,
        {'fast_period': 5, 'slow_period': 20},
        'AKShare'
    )
    print(f"  决策: {decision.action.value}")
    print(f"  原因: {decision.reason}")
    
    # 测试2：策略失效检测
    print("\n🔄 测试2: 策略失效检测")
    # 模拟性能下降
    for i in range(10):
        bad_metrics = PerformanceMetrics(
            timestamp=datetime.now() - timedelta(days=10-i),
            total_return=0.15 - i * 0.02,  # 持续下降
            sharpe_ratio=1.5 - i * 0.1,
            max_drawdown=-0.05 - i * 0.01,
            win_rate=0.6 - i * 0.02,
            num_trades=50,
            data_quality_score=0.95
        )
        optimizer.performance_tracker.record(bad_metrics)
    
    decision = optimizer.evaluate(
        bad_metrics,
        {'fast_period': 5, 'slow_period': 20},
        'AKShare'
    )
    print(f"  决策: {decision.action.value}")
    print(f"  原因: {decision.reason}")
    print(f"  置信度: {decision.confidence}")
    
    # 测试3：数据源切换
    print("\n🔄 测试3: 数据源质量检测")
    optimizer.datasource_evaluator.record_quality('AKShare', 0.7, 0.5)
    optimizer.datasource_evaluator.record_quality('OpenBB', 0.95, 0.3)
    
    low_quality_metrics = PerformanceMetrics(
        timestamp=datetime.now(),
        total_return=0.05,
        sharpe_ratio=0.8,
        max_drawdown=-0.1,
        win_rate=0.5,
        num_trades=30,
        data_quality_score=0.75  # 低质量
    )
    
    decision = optimizer.evaluate(
        low_quality_metrics,
        {'fast_period': 5, 'slow_period': 20},
        'AKShare'
    )
    print(f"  决策: {decision.action.value}")
    print(f"  原因: {decision.reason}")
    if decision.parameters:
        print(f"  建议参数: {decision.parameters}")
    
    # 测试4：人工介入
    print("\n🔄 测试4: 人工介入检测")
    high_risk_metrics = PerformanceMetrics(
        timestamp=datetime.now(),
        total_return=-0.1,
        sharpe_ratio=-0.5,
        max_drawdown=-0.25,  # 高回撤
        win_rate=0.3,
        num_trades=20,
        data_quality_score=0.9
    )
    
    decision = optimizer.evaluate(
        high_risk_metrics,
        {'fast_period': 5, 'slow_period': 20},
        'AKShare'
    )
    print(f"  决策: {decision.action.value}")
    print(f"  原因: {decision.reason}")
    
    # 测试5：优化摘要
    print("\n🔄 测试5: 优化摘要")
    summary = optimizer.get_optimization_summary()
    print(f"  总决策数: {summary['total_decisions']}")
    print(f"  近期决策数: {summary['recent_decisions']}")
    print(f"  决策分布: {summary['action_distribution']}")
    print(f"  收益趋势: {summary['performance_trend']:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ 所有验证测试完成")
    print("=" * 60)
    print("\n递归自优化循环说明:")
    print("  1. 性能追踪器持续记录系统性能")
    print("  2. 优化规则定期评估当前状态")
    print("  3. 当检测到问题时，自动生成优化决策")
    print("  4. 决策执行后，继续监控效果")
    print("  5. 形成自我评估-反馈-改进的闭环")
