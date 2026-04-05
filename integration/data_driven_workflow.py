"""
数据驱动的胶水编程工作流程
确保所有算法都经过真实数据验证
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import logging
from datetime import datetime
import json

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from integration.real_data_validator import RealDataValidator
from integration.data_quality_assessment import DataQualityAssessment

logger = logging.getLogger(__name__)

class DataDrivenWorkflow:
    """
    数据驱动的胶水编程工作流程管理器
    """
    
    def __init__(self, workflow_name: str = "default"):
        """
        初始化工作流程
        
        Args:
            workflow_name: 工作流程名称
        """
        self.workflow_name = workflow_name
        self.workflow_dir = Path("workflow_results") / workflow_name
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.data_validator = RealDataValidator()
        self.quality_assessor = DataQualityAssessment()
        
        # 工作流程状态
        self.workflow_state = {
            'start_time': datetime.now().isoformat(),
            'current_stage': 'initialized',
            'completed_stages': [],
            'errors': [],
            'results': {}
        }
        
        logger.info(f"数据驱动工作流程 '{workflow_name}' 初始化完成")
    
    def run_full_workflow(self, algorithm_func: Callable, 
                         algorithm_name: str = "unknown_algorithm") -> Dict[str, Any]:
        """
        运行完整的工作流程
        
        Args:
            algorithm_func: 要验证的算法函数
            algorithm_name: 算法名称
            
        Returns:
            工作流程结果
        """
        logger.info(f"开始运行工作流程验证算法: {algorithm_name}")
        
        workflow_results = {
            'algorithm_name': algorithm_name,
            'workflow_name': self.workflow_name,
            'stages': {},
            'final_conclusion': '',
            'recommendations': []
        }
        
        try:
            # 阶段1: 数据收集
            stage1_result = self._stage1_data_collection()
            workflow_results['stages']['data_collection'] = stage1_result
            self._update_workflow_state('data_collection_completed')
            
            # 阶段2: 数据质量评估
            stage2_result = self._stage2_data_quality_assessment(stage1_result['collected_data'])
            workflow_results['stages']['data_quality_assessment'] = stage2_result
            self._update_workflow_state('data_quality_assessment_completed')
            
            # 阶段3: 算法验证
            stage3_result = self._stage3_algorithm_validation(algorithm_func, stage1_result['collected_data'])
            workflow_results['stages']['algorithm_validation'] = stage3_result
            self._update_workflow_state('algorithm_validation_completed')
            
            # 阶段4: 数据依赖分析
            stage4_result = self._stage4_data_dependency_analysis(algorithm_func, stage1_result['collected_data'])
            workflow_results['stages']['data_dependency_analysis'] = stage4_result
            self._update_workflow_state('data_dependency_analysis_completed')
            
            # 阶段5: 生成最终结论
            final_conclusion = self._generate_final_conclusion(
                stage2_result, stage3_result, stage4_result
            )
            workflow_results['final_conclusion'] = final_conclusion
            workflow_results['recommendations'] = self._generate_recommendations(
                stage2_result, stage3_result, stage4_result
            )
            
            # 保存工作流程结果
            self._save_workflow_results(workflow_results)
            
            logger.info(f"工作流程完成: {algorithm_name}")
            
        except Exception as e:
            error_msg = f"工作流程执行失败: {str(e)}"
            logger.error(error_msg)
            self.workflow_state['errors'].append(error_msg)
            workflow_results['error'] = error_msg
        
        return workflow_results
    
    def _stage1_data_collection(self) -> Dict[str, Any]:
        """阶段1: 数据收集"""
        logger.info("阶段1: 收集真实市场数据")
        
        collected_data = self.data_validator.collect_daily_data()
        
        return {
            'stage': 'data_collection',
            'timestamp': datetime.now().isoformat(),
            'collected_data': collected_data,
            'summary': collected_data['summary']
        }
    
    def _stage2_data_quality_assessment(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """阶段2: 数据质量评估"""
        logger.info("阶段2: 评估数据质量")
        
        assessments = []
        
        # 评估每只股票的数据质量
        for symbol, stock_data in collected_data['stocks'].items():
            assessment = self.quality_assessor.assess_market_data(stock_data)
            assessments.append({
                'symbol': symbol,
                'assessment': assessment
            })
        
        # 计算总体数据质量
        quality_scores = [a['assessment']['overall_score'] for a in assessments]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        quality_grades = [a['assessment']['quality_grade'] for a in assessments]
        
        return {
            'stage': 'data_quality_assessment',
            'timestamp': datetime.now().isoformat(),
            'assessments': assessments,
            'summary': {
                'average_quality_score': round(avg_quality, 2),
                'quality_grades_distribution': {
                    grade: quality_grades.count(grade)
                    for grade in set(quality_grades)
                },
                'data_quality_status': '优秀' if avg_quality >= 80 else '良好' if avg_quality >= 70 else '合格' if avg_quality >= 60 else '需要改进'
            }
        }
    
    def _stage3_algorithm_validation(self, algorithm_func: Callable, 
                                   collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """阶段3: 算法验证"""
        logger.info("阶段3: 验证算法")
        
        # 准备测试数据
        test_data = list(collected_data['stocks'].values())
        
        # 运行算法验证
        validation_results = self.data_validator.validate_algorithm(
            algorithm_func,
            validation_days=1,  # 使用当天数据
            min_success_rate=0.7
        )
        
        return {
            'stage': 'algorithm_validation',
            'timestamp': datetime.now().isoformat(),
            'validation_results': validation_results,
            'summary': {
                'algorithm_valid': validation_results.get('valid', False),
                'success_rate': validation_results.get('success_rate', 0),
                'total_tests': validation_results.get('total_tests', 0),
                'successful_tests': validation_results.get('successful_tests', 0)
            }
        }
    
    def _stage4_data_dependency_analysis(self, algorithm_func: Callable,
                                       collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """阶段4: 数据依赖分析"""
        logger.info("阶段4: 分析算法数据依赖")
        
        # 准备测试数据
        test_data = list(collected_data['stocks'].values())
        
        # 分析数据依赖
        dependency_result = self.quality_assessor.assess_algorithm_data_dependency(
            algorithm_func, test_data
        )
        
        return {
            'stage': 'data_dependency_analysis',
            'timestamp': datetime.now().isoformat(),
            'dependency_result': dependency_result,
            'summary': {
                'data_dependency_level': dependency_result.get('data_dependency', '未知'),
                'quality_threshold': dependency_result.get('quality_threshold', 0),
                'recommendation': dependency_result.get('recommendation', '')
            }
        }
    
    def _generate_final_conclusion(self, quality_result: Dict[str, Any],
                                 validation_result: Dict[str, Any],
                                 dependency_result: Dict[str, Any]) -> str:
        """生成最终结论"""
        # 提取关键指标
        avg_quality = quality_result['summary']['average_quality_score']
        algorithm_valid = validation_result['summary']['algorithm_valid']
        success_rate = validation_result['summary']['success_rate']
        data_dependency = dependency_result['summary']['data_dependency_level']
        
        # 生成结论
        conclusions = []
        
        # 数据质量结论
        if avg_quality >= 80:
            conclusions.append("数据质量优秀，适合算法验证")
        elif avg_quality >= 70:
            conclusions.append("数据质量良好，基本满足算法需求")
        elif avg_quality >= 60:
            conclusions.append("数据质量合格，但有待改进")
        else:
            conclusions.append("数据质量不足，需要改进数据源")
        
        # 算法验证结论
        if algorithm_valid:
            conclusions.append(f"算法验证通过，成功率{success_rate:.1%}")
        else:
            conclusions.append(f"算法验证失败，成功率{success_rate:.1%}")
        
        # 数据依赖结论
        if data_dependency == '高':
            conclusions.append("算法对数据质量高度敏感")
        elif data_dependency == '中':
            conclusions.append("算法对数据质量中度敏感")
        else:
            conclusions.append("算法对数据质量低度敏感")
        
        return " | ".join(conclusions)
    
    def _generate_recommendations(self, quality_result: Dict[str, Any],
                                validation_result: Dict[str, Any],
                                dependency_result: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 数据质量建议
        avg_quality = quality_result['summary']['average_quality_score']
        if avg_quality < 70:
            recommendations.append("提升数据质量，确保数据准确性、完整性和及时性")
        
        # 算法验证建议
        if not validation_result['summary']['algorithm_valid']:
            recommendations.append("优化算法逻辑，提高在真实数据上的表现")
        
        # 数据依赖建议
        data_dependency = dependency_result['summary']['data_dependency_level']
        if data_dependency == '高':
            recommendations.append("增加算法的鲁棒性，降低对数据质量的依赖")
        
        # 通用建议
        recommendations.append("持续收集和验证真实市场数据")
        recommendations.append("定期回测算法在不同市场环境下的表现")
        
        return recommendations
    
    def _update_workflow_state(self, stage: str):
        """更新工作流程状态"""
        self.workflow_state['current_stage'] = stage
        self.workflow_state['completed_stages'].append(stage)
    
    def _save_workflow_results(self, results: Dict[str, Any]):
        """保存工作流程结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.workflow_dir / f"workflow_results_{timestamp}.json"
        
        # 添加工作流程状态
        results['workflow_state'] = self.workflow_state
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"工作流程结果已保存到: {filename}")
    
    def generate_workflow_report(self, workflow_results: Dict[str, Any]) -> str:
        """生成工作流程报告"""
        report_lines = []
        
        report_lines.append("=" * 70)
        report_lines.append(f"数据驱动的胶水编程工作流程报告")
        report_lines.append("=" * 70)
        report_lines.append(f"工作流程: {workflow_results.get('workflow_name', '未知')}")
        report_lines.append(f"算法名称: {workflow_results.get('algorithm_name', '未知')}")
        report_lines.append(f"执行时间: {workflow_results.get('workflow_state', {}).get('start_time', '未知')}")
        report_lines.append("")
        
        # 各阶段摘要
        report_lines.append("各阶段执行摘要:")
        report_lines.append("-" * 40)
        
        stages = workflow_results.get('stages', {})
        for stage_name, stage_result in stages.items():
            stage_summary = stage_result.get('summary', {})
            
            if stage_name == 'data_collection':
                report_lines.append(f"1. 数据收集:")
                report_lines.append(f"   收集股票数: {stage_summary.get('total_stocks', 0)}")
                report_lines.append(f"   成功收集: {stage_summary.get('successful_collections', 0)}")
            
            elif stage_name == 'data_quality_assessment':
                report_lines.append(f"2. 数据质量评估:")
                report_lines.append(f"   平均质量分数: {stage_summary.get('average_quality_score', 0)}")
                report_lines.append(f"   数据质量状态: {stage_summary.get('data_quality_status', '未知')}")
            
            elif stage_name == 'algorithm_validation':
                report_lines.append(f"3. 算法验证:")
                report_lines.append(f"   验证结果: {'通过' if stage_summary.get('algorithm_valid') else '失败'}")
                report_lines.append(f"   成功率: {stage_summary.get('success_rate', 0):.1%}")
                report_lines.append(f"   测试总数: {stage_summary.get('total_tests', 0)}")
            
            elif stage_name == 'data_dependency_analysis':
                report_lines.append(f"4. 数据依赖分析:")
                report_lines.append(f"   数据依赖度: {stage_summary.get('data_dependency_level', '未知')}")
                report_lines.append(f"   质量阈值: {stage_summary.get('quality_threshold', 0)}")
        
        # 最终结论
        report_lines.append("")
        report_lines.append("最终结论:")
        report_lines.append("-" * 40)
        report_lines.append(workflow_results.get('final_conclusion', '无结论'))
        
        # 改进建议
        report_lines.append("")
        report_lines.append("改进建议:")
        report_lines.append("-" * 40)
        for i, recommendation in enumerate(workflow_results.get('recommendations', []), 1):
            report_lines.append(f"{i}. {recommendation}")
        
        # 错误信息（如果有）
        errors = workflow_results.get('workflow_state', {}).get('errors', [])
        if errors:
            report_lines.append("")
            report_lines.append("执行错误:")
            report_lines.append("-" * 40)
            for error in errors:
                report_lines.append(f"⚠️ {error}")
        
        report_lines.append("")
        report_lines.append("=" * 70)
        report_lines.append("报告生成完成")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)


# 测试函数
def test_data_driven_workflow():
    """测试数据驱动的工作流程"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试数据驱动的工作流程")
    print("=" * 70)
    
    # 定义一个测试算法
    def test_trading_algorithm(market_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试交易算法"""
        price = market_data.get('price', 0)
        change_percent = market_data.get('change_percent', 0)
        volume = market_data.get('volume', 0)
        
        # 简单的交易逻辑
        if change_percent > 2 and volume > 10000000:
            signal = 'STRONG_BUY'
            confidence = 0.8
        elif change_percent > 0:
            signal = 'BUY'
            confidence = 0.6
        elif change_percent > -2:
            signal = 'HOLD'
            confidence = 0.5
        else:
            signal = 'SELL'
            confidence = 0.6
        
        return {
            'signal': signal,
            'confidence': confidence,
            'recommendation': f'基于价格{price}，涨跌幅{change_percent:.2f}%',
            'algorithm_version': '1.0'
        }
    
    # 创建并运行工作流程
    workflow = DataDrivenWorkflow(workflow_name="测试交易算法验证")
    
    workflow_results = workflow.run_full_workflow(
        algorithm_func=test_trading_algorithm,
        algorithm_name="简单趋势跟踪算法"
    )
    
    # 生成报告
    if 'error' not in workflow_results:
        report = workflow.generate_workflow_report(workflow_results)
        print(report)
    else:
        print(f"工作流程执行失败: {workflow_results['error']}")
    
    print("\n🎯 数据驱动的工作流程测试完成!")


if __name__ == "__main__":
    test_data_driven_workflow()