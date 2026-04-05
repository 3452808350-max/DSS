"""
数据质量评估体系
评估胶水编程中使用的数据质量
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import numpy as np
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DataQualityAssessment:
    """
    数据质量评估器
    评估各种数据源的质量
    """
    
    def __init__(self):
        """初始化数据质量评估器"""
        self.quality_metrics = {
            'completeness': 0,      # 数据完整性
            'accuracy': 0,          # 数据准确性
            'timeliness': 0,        # 数据及时性
            'consistency': 0,       # 数据一致性
            'relevance': 0          # 数据相关性
        }
        
        logger.info("数据质量评估器初始化完成")
    
    def assess_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估市场数据质量
        
        Args:
            market_data: 市场数据
            
        Returns:
            质量评估结果
        """
        assessment = {
            'overall_score': 0,
            'metrics': {},
            'issues': [],
            'recommendations': []
        }
        
        # 1. 完整性评估
        completeness_score = self._assess_completeness(market_data)
        assessment['metrics']['completeness'] = completeness_score
        
        # 2. 准确性评估
        accuracy_score = self._assess_accuracy(market_data)
        assessment['metrics']['accuracy'] = accuracy_score
        
        # 3. 及时性评估
        timeliness_score = self._assess_timeliness(market_data)
        assessment['metrics']['timeliness'] = timeliness_score
        
        # 4. 一致性评估
        consistency_score = self._assess_consistency(market_data)
        assessment['metrics']['consistency'] = consistency_score
        
        # 5. 相关性评估
        relevance_score = self._assess_relevance(market_data)
        assessment['metrics']['relevance'] = relevance_score
        
        # 计算总体分数
        weights = {
            'completeness': 0.25,
            'accuracy': 0.30,
            'timeliness': 0.20,
            'consistency': 0.15,
            'relevance': 0.10
        }
        
        overall_score = sum(
            assessment['metrics'][metric] * weight
            for metric, weight in weights.items()
        )
        
        assessment['overall_score'] = round(overall_score, 2)
        
        # 生成质量等级
        if overall_score >= 80:
            assessment['quality_grade'] = 'A - 优秀'
        elif overall_score >= 70:
            assessment['quality_grade'] = 'B - 良好'
        elif overall_score >= 60:
            assessment['quality_grade'] = 'C - 合格'
        elif overall_score >= 50:
            assessment['quality_grade'] = 'D - 需要改进'
        else:
            assessment['quality_grade'] = 'F - 不合格'
        
        # 生成改进建议
        assessment['recommendations'] = self._generate_recommendations(assessment['metrics'])
        
        return assessment
    
    def _assess_completeness(self, data: Dict[str, Any]) -> float:
        """评估数据完整性"""
        required_fields = [
            'symbol', 'price', 'change_percent', 'volume',
            'open', 'high', 'low', 'previous_close'
        ]
        
        present_fields = 0
        for field in required_fields:
            if field in data and data[field] is not None:
                present_fields += 1
        
        completeness = (present_fields / len(required_fields)) * 100
        return round(completeness, 2)
    
    def _assess_accuracy(self, data: Dict[str, Any]) -> float:
        """评估数据准确性"""
        accuracy_score = 70  # 基础分
        
        # 检查价格合理性
        price = data.get('price', 0)
        if price <= 0:
            accuracy_score -= 30
        elif price > 10000:  # 假设股票价格不会超过10000元
            accuracy_score -= 20
        
        # 检查涨跌幅合理性
        change_percent = data.get('change_percent', 0)
        if abs(change_percent) > 20:  # 涨跌幅超过20%需要特别关注
            accuracy_score -= 10
        
        # 检查成交量合理性
        volume = data.get('volume', 0)
        if volume < 0:
            accuracy_score -= 20
        
        return max(0, min(100, accuracy_score))
    
    def _assess_timeliness(self, data: Dict[str, Any]) -> float:
        """评估数据及时性"""
        timeliness_score = 80  # 基础分
        
        # 检查时间戳
        timestamp = data.get('timestamp', '')
        if timestamp:
            try:
                data_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_diff = datetime.now() - data_time
                
                # 根据时间差扣分
                if time_diff > timedelta(hours=24):
                    timeliness_score -= 50
                elif time_diff > timedelta(hours=6):
                    timeliness_score -= 30
                elif time_diff > timedelta(hours=1):
                    timeliness_score -= 10
            except:
                timeliness_score -= 20  # 时间戳格式错误
        else:
            timeliness_score -= 30  # 没有时间戳
        
        return max(0, min(100, timeliness_score))
    
    def _assess_consistency(self, data: Dict[str, Any]) -> float:
        """评估数据一致性"""
        consistency_score = 75  # 基础分
        
        # 检查价格一致性
        price = data.get('price', 0)
        open_price = data.get('open', 0)
        high = data.get('high', 0)
        low = data.get('low', 0)
        previous_close = data.get('previous_close', 0)
        
        # 价格应该在当日高低点之间
        if not (low <= price <= high):
            consistency_score -= 20
        
        # 开盘价应该在昨日收盘价附近（考虑涨跌幅限制）
        if previous_close > 0:
            expected_range = previous_close * 0.9, previous_close * 1.1  # ±10%
            if not (expected_range[0] <= open_price <= expected_range[1]):
                consistency_score -= 15
        
        return max(0, min(100, consistency_score))
    
    def _assess_relevance(self, data: Dict[str, Any]) -> float:
        """评估数据相关性"""
        relevance_score = 85  # 基础分
        
        # 检查是否有相关分析字段
        relevant_fields = ['change', 'amount', 'turnover', 'pe_ratio', 'pb_ratio']
        present_relevant = sum(1 for field in relevant_fields if field in data)
        
        relevance_score += (present_relevant / len(relevant_fields)) * 15
        
        return min(100, relevance_score)
    
    def _generate_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if metrics['completeness'] < 90:
            recommendations.append("增加缺失的数据字段")
        
        if metrics['accuracy'] < 80:
            recommendations.append("验证数据准确性，检查异常值")
        
        if metrics['timeliness'] < 80:
            recommendations.append("更新数据时间戳，确保数据及时性")
        
        if metrics['consistency'] < 80:
            recommendations.append("检查数据一致性，修复矛盾数据")
        
        if metrics['relevance'] < 80:
            recommendations.append("添加更多相关分析字段")
        
        if not recommendations:
            recommendations.append("数据质量良好，继续保持")
        
        return recommendations
    
    def assess_algorithm_data_dependency(self, algorithm_func, 
                                       test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估算法对数据质量的依赖程度
        
        Args:
            algorithm_func: 算法函数
            test_data: 测试数据
            
        Returns:
            数据依赖评估结果
        """
        logger.info("评估算法数据依赖度")
        
        results = []
        
        for data in test_data:
            # 评估数据质量
            quality_assessment = self.assess_market_data(data)
            
            # 运行算法
            try:
                algorithm_result = algorithm_func(data)
                algorithm_success = True
            except Exception as e:
                algorithm_result = {'error': str(e)}
                algorithm_success = False
            
            results.append({
                'data_quality': quality_assessment['overall_score'],
                'algorithm_success': algorithm_success,
                'quality_details': quality_assessment
            })
        
        # 分析数据质量与算法成功率的关系
        successful_runs = [r for r in results if r['algorithm_success']]
        failed_runs = [r for r in results if not r['algorithm_success']]
        
        avg_quality_success = np.mean([r['data_quality'] for r in successful_runs]) if successful_runs else 0
        avg_quality_fail = np.mean([r['data_quality'] for r in failed_runs]) if failed_runs else 0
        
        # 计算数据质量阈值
        quality_threshold = self._calculate_quality_threshold(results)
        
        return {
            'total_tests': len(results),
            'successful_tests': len(successful_runs),
            'failed_tests': len(failed_runs),
            'success_rate': len(successful_runs) / len(results) if results else 0,
            'avg_quality_success': round(avg_quality_success, 2),
            'avg_quality_fail': round(avg_quality_fail, 2),
            'quality_threshold': round(quality_threshold, 2),
            'data_dependency': '高' if (avg_quality_success - avg_quality_fail) > 20 else '中' if (avg_quality_success - avg_quality_fail) > 10 else '低',
            'recommendation': self._generate_data_dependency_recommendation(avg_quality_success, avg_quality_fail, quality_threshold)
        }
    
    def _calculate_quality_threshold(self, results: List[Dict]) -> float:
        """计算数据质量阈值"""
        if not results:
            return 60.0
        
        # 找到算法成功所需的最低数据质量
        successful_qualities = [r['data_quality'] for r in results if r['algorithm_success']]
        
        if not successful_qualities:
            return 0.0
        
        # 使用成功运行中最低的质量作为阈值
        return min(successful_qualities)
    
    def _generate_data_dependency_recommendation(self, avg_success: float, 
                                               avg_fail: float, 
                                               threshold: float) -> str:
        """生成数据依赖度建议"""
        quality_diff = avg_success - avg_fail
        
        if quality_diff > 30:
            return "算法对数据质量高度敏感，必须确保数据质量高于阈值"
        elif quality_diff > 15:
            return "算法对数据质量中度敏感，建议优化数据质量"
        elif quality_diff > 5:
            return "算法对数据质量低度敏感，但数据质量仍有影响"
        else:
            return "算法对数据质量不敏感，但高质量数据仍有帮助"
    
    def generate_quality_report(self, assessments: List[Dict[str, Any]]) -> str:
        """生成质量报告"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("数据质量评估报告")
        report_lines.append("=" * 60)
        
        for i, assessment in enumerate(assessments, 1):
            report_lines.append(f"\n数据源 {i}:")
            report_lines.append(f"  总体分数: {assessment['overall_score']} - {assessment['quality_grade']}")
            report_lines.append(f"  详细指标:")
            for metric, score in assessment['metrics'].items():
                report_lines.append(f"    {metric}: {score}")
            
            if assessment['issues']:
                report_lines.append(f"  问题:")
                for issue in assessment['issues']:
                    report_lines.append(f"    - {issue}")
            
            report_lines.append(f"  改进建议:")
            for rec in assessment['recommendations']:
                report_lines.append(f"    - {rec}")
        
        return "\n".join(report_lines)


# 测试函数
def test_data_quality_assessment():
    """测试数据质量评估"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试数据质量评估")
    print("=" * 60)
    
    assessor = DataQualityAssessment()
    
    # 测试数据
    test_data = [
        {
            'symbol': '000001',
            'price': 11.07,
            'change_percent': 0.09,
            'volume': 43104098,
            'open': 11.00,
            'high': 11.20,
            'low': 10.90,
            'previous_close': 11.06,
            'timestamp': '2026-02-12T10:30:00'
        },
        {
            'symbol': '600519',
            'price': 1504.33,
            'change_percent': -0.03,
            'volume': 1954321,
            'open': 1510.00,
            'high': 1520.00,
            'low': 1500.00,
            'previous_close': 1504.80,
            'timestamp': '2026-02-12T10:30:00'
        },
        {
            'symbol': 'TEST',
            'price': -10.00,  # 错误数据
            'change_percent': 999.99,  # 异常数据
            'timestamp': '2025-01-01T00:00:00'  # 过时数据
        }
    ]
    
    print("\n1. 评估数据质量:")
    assessments = []
    for data in test_data:
        assessment = assessor.assess_market_data(data)
        assessments.append(assessment)
        
        print(f"  {data['symbol']}: {assessment['overall_score']}分 - {assessment['quality_grade']}")
    
    # 生成详细报告
    report = assessor.generate_quality_report(assessments)
    print(f"\n{report}")
    
    # 测试算法数据依赖评估
    print("\n2. 测试算法数据依赖评估:")
    
    def sample_algorithm(data):
        """示例算法"""
        if data['price'] <= 0:
            raise ValueError("价格无效")
        return {'signal': 'BUY' if data['change_percent'] > 0 else 'SELL'}
    
    dependency_result = assessor.assess_algorithm_data_dependency(sample_algorithm, test_data)
    
    print(f"  总测试数: {dependency_result['total_tests']}")
    print(f"  成功率: {dependency_result['success_rate']:.1%}")
    print(f"  成功时平均数据质量: {dependency_result['avg_quality_success']}")
    print(f"  失败时平均数据质量: {dependency_result['avg_quality_fail']}")
    print(f"  数据质量阈值: {dependency_result['quality_threshold']}")
    print(f"  数据依赖度: {dependency_result['data_dependency']}")
    print(f"  建议: {dependency_result['recommendation']}")
    
    print("\n🎯 数据质量评估测试完成!")


if __name__ == "__main__":
    test_data_quality_assessment()