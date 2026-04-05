"""
真实数据验证框架
确保胶水编程的算法在真实市场数据上有效
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.acquisition.cn_market import CNMarketDataFetcher

logger = logging.getLogger(__name__)

class RealDataValidator:
    """
    真实数据验证器
    收集、存储、验证真实市场数据
    """
    
    def __init__(self, data_dir: str = "real_market_data"):
        """
        初始化真实数据验证器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 数据获取器
        self.fetcher = CNMarketDataFetcher(prefered_lib="tushare")
        
        # 监控的股票列表（代表性股票）
        self.watchlist = [
            '000001',  # 平安银行 - 金融
            '600519',  # 贵州茅台 - 消费
            '601318',  # 中国平安 - 保险
            '300750',  # 宁德时代 - 新能源
            '000858',  # 五粮液 - 消费
            '600036',  # 招商银行 - 金融
            '002415',  # 海康威视 - 科技
            '000002',  # 万科A - 地产
        ]
        
        logger.info(f"真实数据验证器初始化完成，监控{len(self.watchlist)}只股票")
    
    def collect_daily_data(self) -> Dict[str, Any]:
        """
        收集每日真实市场数据
        
        Returns:
            收集的数据统计
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        collected_data = {
            'timestamp': timestamp,
            'date': date_str,
            'stocks': {},
            'summary': {
                'total_stocks': len(self.watchlist),
                'successful_collections': 0,
                'failed_collections': 0
            }
        }
        
        logger.info(f"开始收集{date_str}的市场数据...")
        
        for symbol in self.watchlist:
            try:
                # 获取实时数据
                quote = self.fetcher.get_stock_quote(symbol)
                
                if quote:
                    collected_data['stocks'][symbol] = quote
                    collected_data['summary']['successful_collections'] += 1
                    
                    logger.debug(f"成功收集 {symbol} 数据")
                else:
                    collected_data['summary']['failed_collections'] += 1
                    logger.warning(f"无法获取 {symbol} 数据")
                    
            except Exception as e:
                collected_data['summary']['failed_collections'] += 1
                logger.error(f"收集 {symbol} 数据时出错: {e}")
        
        # 保存数据
        self._save_daily_data(collected_data)
        
        logger.info(f"数据收集完成: {collected_data['summary']}")
        return collected_data
    
    def _save_daily_data(self, data: Dict[str, Any]):
        """保存每日数据"""
        filename = self.data_dir / f"market_data_{data['timestamp']}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"数据已保存到: {filename}")
    
    def load_historical_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        加载历史数据
        
        Args:
            days: 加载最近多少天的数据
            
        Returns:
            历史数据列表
        """
        historical_data = []
        
        # 查找数据文件
        data_files = sorted(self.data_dir.glob("market_data_*.json"))
        
        if not data_files:
            logger.warning("没有找到历史数据文件")
            return historical_data
        
        # 加载最近的数据
        recent_files = data_files[-min(days, len(data_files)):]
        
        for file in recent_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    historical_data.append(data)
            except Exception as e:
                logger.error(f"加载文件 {file} 失败: {e}")
        
        logger.info(f"加载了 {len(historical_data)} 天的历史数据")
        return historical_data
    
    def validate_algorithm(self, algorithm_func, 
                          validation_days: int = 7,
                          min_success_rate: float = 0.7) -> Dict[str, Any]:
        """
        验证算法在真实数据上的表现
        
        Args:
            algorithm_func: 要验证的算法函数
            validation_days: 验证天数
            min_success_rate: 最低成功率
            
        Returns:
            验证结果
        """
        logger.info(f"开始验证算法，使用最近{validation_days}天数据")
        
        # 加载历史数据
        historical_data = self.load_historical_data(validation_days)
        
        if len(historical_data) < 3:
            return {
                'valid': False,
                'reason': f'数据不足，只有{len(historical_data)}天数据',
                'recommendation': '需要收集更多数据'
            }
        
        validation_results = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'daily_results': [],
            'algorithm_name': algorithm_func.__name__ if hasattr(algorithm_func, '__name__') else 'unknown'
        }
        
        # 对每天的数据进行验证
        for day_data in historical_data:
            daily_result = self._validate_single_day(algorithm_func, day_data)
            validation_results['daily_results'].append(daily_result)
            
            if daily_result['valid']:
                validation_results['successful_tests'] += 1
            else:
                validation_results['failed_tests'] += 1
            
            validation_results['total_tests'] += 1
        
        # 计算总体成功率
        success_rate = validation_results['successful_tests'] / validation_results['total_tests'] if validation_results['total_tests'] > 0 else 0
        
        # 生成验证结论
        validation_results['success_rate'] = round(success_rate, 3)
        validation_results['valid'] = success_rate >= min_success_rate
        
        if validation_results['valid']:
            validation_results['conclusion'] = f"算法验证通过，成功率{success_rate:.1%}"
        else:
            validation_results['conclusion'] = f"算法验证失败，成功率{success_rate:.1%}，低于要求{min_success_rate:.1%}"
        
        logger.info(f"算法验证完成: {validation_results['conclusion']}")
        return validation_results
    
    def _validate_single_day(self, algorithm_func, day_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证单日数据"""
        date = day_data.get('date', 'unknown')
        
        try:
            # 对每只股票应用算法
            stock_results = {}
            
            for symbol, stock_data in day_data.get('stocks', {}).items():
                try:
                    # 应用算法
                    algorithm_result = algorithm_func(stock_data)
                    
                    # 验证算法结果（这里需要根据具体算法定义验证逻辑）
                    is_valid = self._validate_algorithm_result(algorithm_result, stock_data)
                    
                    stock_results[symbol] = {
                        'valid': is_valid,
                        'algorithm_output': algorithm_result,
                        'market_data': {
                            'price': stock_data.get('price'),
                            'change_percent': stock_data.get('change_percent')
                        }
                    }
                    
                except Exception as e:
                    stock_results[symbol] = {
                        'valid': False,
                        'error': str(e)
                    }
            
            # 计算当日成功率
            valid_count = sum(1 for r in stock_results.values() if r.get('valid', False))
            total_count = len(stock_results)
            daily_success_rate = valid_count / total_count if total_count > 0 else 0
            
            return {
                'date': date,
                'valid': daily_success_rate >= 0.5,  # 当日成功率超过50%算有效
                'success_rate': round(daily_success_rate, 3),
                'valid_count': valid_count,
                'total_count': total_count,
                'stock_results': stock_results
            }
            
        except Exception as e:
            logger.error(f"验证{date}数据时出错: {e}")
            return {
                'date': date,
                'valid': False,
                'error': str(e)
            }
    
    def _validate_algorithm_result(self, algorithm_result: Dict[str, Any], 
                                 market_data: Dict[str, Any]) -> bool:
        """
        验证算法结果（需要根据具体算法定制）
        
        这里是一个示例验证逻辑：
        1. 算法必须返回signal字段
        2. signal必须是预定义的值
        3. 算法必须有confidence字段且在一定范围内
        """
        try:
            # 检查必要字段
            required_fields = ['signal', 'confidence', 'recommendation']
            for field in required_fields:
                if field not in algorithm_result:
                    logger.warning(f"算法结果缺少必要字段: {field}")
                    return False
            
            # 验证signal值
            valid_signals = ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
            if algorithm_result['signal'] not in valid_signals:
                logger.warning(f"无效的signal值: {algorithm_result['signal']}")
                return False
            
            # 验证confidence范围
            confidence = algorithm_result['confidence']
            if not (0 <= confidence <= 1):
                logger.warning(f"confidence值超出范围: {confidence}")
                return False
            
            # 可以根据市场数据进一步验证
            # 例如：如果价格大涨但算法给出强烈卖出信号，可能需要进一步检查
            
            return True
            
        except Exception as e:
            logger.error(f"验证算法结果时出错: {e}")
            return False
    
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """生成验证报告"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("真实数据验证报告")
        report_lines.append("=" * 60)
        report_lines.append(f"算法名称: {validation_results.get('algorithm_name', '未知')}")
        report_lines.append(f"验证天数: {validation_results.get('total_tests', 0)}")
        report_lines.append(f"成功率: {validation_results.get('success_rate', 0):.1%}")
        report_lines.append(f"验证结论: {validation_results.get('conclusion', '')}")
        report_lines.append("")
        
        # 每日详细结果
        report_lines.append("每日验证结果:")
        report_lines.append("-" * 40)
        
        for daily in validation_results.get('daily_results', []):
            date = daily.get('date', '未知日期')
            valid = "✅" if daily.get('valid') else "❌"
            success_rate = daily.get('success_rate', 0)
            report_lines.append(f"{date}: {valid} 成功率: {success_rate:.1%}")
        
        return "\n".join(report_lines)
    
    def collect_market_sentiment_data(self):
        """
        收集市场情绪数据（示例框架）
        实际实现需要集成新闻API、社交媒体API等
        """
        # TODO: 集成真实的市场情绪数据源
        # 1. 财经新闻API（新浪财经、东方财富等）
        # 2. 社交媒体API（微博、雪球等）
        # 3. 专业财经数据（Wind、同花顺等）
        
        logger.info("市场情绪数据收集功能待实现")
        return {
            'status': 'not_implemented',
            'message': '需要集成真实数据源'
        }


# 测试函数
def test_real_data_validator():
    """测试真实数据验证器"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试真实数据验证器")
    print("=" * 60)
    
    validator = RealDataValidator()
    
    # 1. 收集实时数据
    print("\n1. 收集实时市场数据:")
    collected_data = validator.collect_daily_data()
    print(f"   成功收集: {collected_data['summary']['successful_collections']}只股票")
    print(f"   失败: {collected_data['summary']['failed_collections']}只股票")
    
    # 2. 加载历史数据
    print("\n2. 加载历史数据:")
    historical_data = validator.load_historical_data(days=5)
    print(f"   加载了 {len(historical_data)} 天的数据")
    
    # 3. 定义一个测试算法
    def test_algorithm(market_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试算法：简单的基于涨跌幅的信号"""
        change_percent = market_data.get('change_percent', 0)
        
        if change_percent > 2:
            signal = 'STRONG_BUY'
            confidence = 0.8
        elif change_percent > 0:
            signal = 'BUY'
            confidence = 0.6
        elif change_percent > -2:
            signal = 'HOLD'
            confidence = 0.5
        elif change_percent > -5:
            signal = 'SELL'
            confidence = 0.6
        else:
            signal = 'STRONG_SELL'
            confidence = 0.8
        
        return {
            'signal': signal,
            'confidence': confidence,
            'recommendation': f'基于涨跌幅{change_percent:.2f}%的信号'
        }
    
    # 4. 验证算法
    print("\n3. 验证测试算法:")
    validation_results = validator.validate_algorithm(
        test_algorithm,
        validation_days=3,
        min_success_rate=0.6
    )
    
    # 5. 生成报告
    report = validator.generate_validation_report(validation_results)
    print(report)
    
    print("\n🎯 真实数据验证器测试完成!")


if __name__ == "__main__":
    test_real_data_validator()