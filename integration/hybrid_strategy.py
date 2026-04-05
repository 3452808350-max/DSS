"""
混合策略：DSS技术分析 + AI-Trader算法
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.acquisition.cn_market import CNMarketDataFetcher
from integration.ai_trader_glue import AITraderGlue
from integration.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger(__name__)

class HybridStrategy:
    """
    混合策略类
    结合DSS的技术分析和AI-Trader的AI算法
    """
    
    def __init__(self, use_ai_trader: bool = True):
        """
        初始化混合策略
        
        Args:
            use_ai_trader: 是否使用AI-Trader算法
        """
        # DSS技术分析模块
        self.dss_fetcher = CNMarketDataFetcher(prefered_lib="tushare")
        
        # AI-Trader胶水层
        self.ai_trader_glue = AITraderGlue(use_ai_trader=use_ai_trader)
        
        # 技术分析器
        self.technical_analyzer = TechnicalAnalyzer()
        
        # 策略权重配置
        self.weights = {
            'technical': 0.4,      # 技术分析权重
            'ai_algorithm': 0.4,   # AI算法权重
            'market_sentiment': 0.2 # 市场情绪权重
        }
        
        logger.info("混合策略初始化完成")
    
    def analyze_single_stock(self, symbol: str) -> Dict[str, Any]:
        """
        分析单只股票
        
        Args:
            symbol: 股票代码
            
        Returns:
            综合分析结果
        """
        logger.info(f"开始分析股票: {symbol}")
        
        # 1. 获取市场数据
        market_data = self._get_market_data(symbol)
        if not market_data:
            return self._create_error_result(symbol, "无法获取市场数据")
        
        # 2. DSS技术分析
        technical_analysis = self._technical_analysis(market_data)
        
        # 3. AI-Trader算法分析
        ai_analysis = self._ai_algorithm_analysis(symbol, market_data)
        
        # 4. 市场情绪分析
        sentiment_analysis = self._market_sentiment_analysis(market_data)
        
        # 5. 综合决策
        final_decision = self._make_final_decision(
            technical_analysis,
            ai_analysis,
            sentiment_analysis
        )
        
        # 6. 生成报告
        report = self._generate_report(
            symbol,
            market_data,
            technical_analysis,
            ai_analysis,
            sentiment_analysis,
            final_decision
        )
        
        logger.info(f"股票 {symbol} 分析完成")
        return report
    
    def _get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取市场数据"""
        try:
            # 使用DSS的数据获取器
            quote = self.dss_fetcher.get_stock_quote(symbol)
            if quote:
                return quote
            else:
                logger.warning(f"无法获取股票 {symbol} 的实时报价")
                return None
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None
    
    def _technical_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """技术分析（使用专业分析器）"""
        try:
            # 获取历史数据（这里需要真正的历史数据）
            # 暂时使用模拟数据
            symbol = market_data.get('symbol', '')
            
            # 模拟历史价格数据（实际应该从数据库获取）
            # 这里生成一些模拟数据用于演示
            import numpy as np
            np.random.seed(hash(symbol) % 1000)  # 使用symbol生成种子
            
            # 生成30天的模拟价格数据
            base_price = market_data.get('price', 10)
            historical_prices = list(base_price + np.cumsum(np.random.randn(30) * 0.5))
            
            # 生成模拟成交量
            base_volume = market_data.get('volume', 1000000)
            historical_volumes = list(np.random.randint(int(base_volume * 0.5), 
                                                      int(base_volume * 1.5), 30))
            
            # 使用技术分析器
            technical_result = self.technical_analyzer.generate_technical_signals(
                historical_prices, 
                historical_volumes
            )
            
            # 计算技术得分（基于置信度）
            technical_score = technical_result['confidence'] * 100
            
            return {
                'signals': technical_result['signals'],
                'confidence': technical_result['confidence'],
                'score': technical_score,
                'recommendation': technical_result['recommendation'],
                'indicators': technical_result.get('indicators', {}),
                'data_points': len(historical_prices)
            }
            
        except Exception as e:
            logger.error(f"技术分析失败: {e}")
            # 降级到简化分析
            return self._simple_technical_analysis(market_data)
    
    def _simple_technical_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """简化技术分析（降级方案）"""
        price = market_data.get('price', 0)
        change_percent = market_data.get('change_percent', 0)
        volume = market_data.get('volume', 0)
        
        # 简单的技术信号
        signals = []
        confidence = 0.5
        
        # 价格变化信号
        if change_percent > 2:
            signals.append("强势上涨")
            confidence += 0.2
        elif change_percent > 0:
            signals.append("温和上涨")
            confidence += 0.1
        elif change_percent < -2:
            signals.append("强势下跌")
            confidence -= 0.2
        elif change_percent < 0:
            signals.append("温和下跌")
            confidence -= 0.1
        
        # 成交量信号
        if volume > 10000000:  # 1000万股
            signals.append("高成交量")
            confidence += 0.1
        
        # 确保置信度在0-1之间
        confidence = max(0.1, min(0.9, confidence))
        
        return {
            'signals': signals,
            'confidence': confidence,
            'score': self._calculate_technical_score(change_percent, volume),
            'recommendation': self._get_technical_recommendation(change_percent),
            'indicators': {},
            'data_points': 1,
            'fallback': True
        }
    
    # 这些方法已被专业的技术分析器替代
    
    def _ai_algorithm_analysis(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI算法分析"""
        # 使用AI-Trader胶水层
        ai_analysis = self.ai_trader_glue.analyze_with_ai_trader(symbol, market_data)
        
        if ai_analysis:
            return ai_analysis
        else:
            # AI分析失败，返回默认分析
            return {
                'signal': 'HOLD',
                'confidence': 0.5,
                'reasoning': 'AI分析暂时不可用，使用默认分析',
                'recommendation': '持有',
                'data_source': 'fallback'
            }
    
    def _market_sentiment_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """市场情绪分析（简化版）"""
        # 这里应该实现真正的市场情绪分析
        # 暂时使用简化版本
        
        change_percent = market_data.get('change_percent', 0)
        
        # 简单的情绪判断
        if change_percent > 2:
            sentiment = "极度乐观"
            score = 80
        elif change_percent > 0:
            sentiment = "乐观"
            score = 60
        elif change_percent > -2:
            sentiment = "悲观"
            score = 40
        else:
            sentiment = "极度悲观"
            score = 20
        
        return {
            'sentiment': sentiment,
            'score': score,
            'description': f'基于价格变化({change_percent:.2f}%)的情绪分析'
        }
    
    def _make_final_decision(self, technical: Dict, ai: Dict, sentiment: Dict) -> Dict[str, Any]:
        """综合决策"""
        # 计算加权得分
        technical_score = technical.get('score', 50)
        ai_confidence = ai.get('confidence', 0.5) * 100  # 转换为0-100分
        sentiment_score = sentiment.get('score', 50)
        
        # 加权平均
        final_score = (
            technical_score * self.weights['technical'] +
            ai_confidence * self.weights['ai_algorithm'] +
            sentiment_score * self.weights['market_sentiment']
        )
        
        # 生成最终信号
        if final_score >= 70:
            signal = "STRONG_BUY"
            recommendation = "强烈建议买入"
        elif final_score >= 60:
            signal = "BUY"
            recommendation = "建议买入"
        elif final_score >= 40:
            signal = "HOLD"
            recommendation = "建议持有"
        elif final_score >= 30:
            signal = "SELL"
            recommendation = "建议卖出"
        else:
            signal = "STRONG_SELL"
            recommendation = "强烈建议卖出"
        
        return {
            'final_score': round(final_score, 2),
            'signal': signal,
            'recommendation': recommendation,
            'weights': self.weights,
            'component_scores': {
                'technical': round(technical_score, 2),
                'ai_algorithm': round(ai_confidence, 2),
                'market_sentiment': round(sentiment_score, 2)
            }
        }
    
    def _generate_report(self, symbol: str, market_data: Dict,
                        technical: Dict, ai: Dict, sentiment: Dict,
                        final_decision: Dict) -> Dict[str, Any]:
        """生成分析报告"""
        # 简化技术指标显示
        technical_summary = {
            'signals': technical.get('signals', [])[:3],  # 只显示前3个信号
            'confidence': technical.get('confidence', 0),
            'recommendation': technical.get('recommendation', ''),
            'data_points': technical.get('data_points', 0),
            'fallback': technical.get('fallback', False)
        }
        
        # 如果有技术指标，添加关键指标
        if 'indicators' in technical and technical['indicators']:
            indicators = technical['indicators']
            technical_summary['key_indicators'] = {
                'rsi': indicators.get('rsi'),
                'ma5': indicators.get('ma5'),
                'ma10': indicators.get('ma10'),
                'ma20': indicators.get('ma20')
            }
        
        return {
            'symbol': symbol,
            'timestamp': market_data.get('timestamp', ''),
            'market_data': {
                'price': market_data.get('price', 0),
                'change_percent': market_data.get('change_percent', 0),
                'volume': market_data.get('volume', 0),
                'amount': market_data.get('amount', 0)
            },
            'analysis_components': {
                'technical_analysis': technical_summary,
                'ai_algorithm_analysis': {
                    'signal': ai.get('signal', ''),
                    'confidence': ai.get('confidence', 0),
                    'recommendation': ai.get('recommendation', ''),
                    'data_source': ai.get('data_source', '')
                },
                'market_sentiment_analysis': sentiment
            },
            'final_decision': final_decision,
            'strategy_version': '1.1.0',  # 更新版本号
            'data_sources': ['dss', 'ai_trader_glue', 'technical_analyzer'],
            'analysis_timestamp': ''
        }
    
    def _create_error_result(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'symbol': symbol,
            'error': True,
            'error_message': error_msg,
            'timestamp': '',
            'final_decision': {
                'signal': 'ERROR',
                'recommendation': '分析失败，请检查数据源'
            }
        }
    
    def analyze_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        分析多只股票
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            每只股票的分析结果
        """
        results = {}
        
        for symbol in symbols:
            try:
                result = self.analyze_single_stock(symbol)
                results[symbol] = result
            except Exception as e:
                logger.error(f"分析股票 {symbol} 失败: {e}")
                results[symbol] = self._create_error_result(symbol, str(e))
        
        return results


def test_hybrid_strategy():
    """测试混合策略"""
    import logging
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 测试混合策略")
    print("=" * 60)
    
    # 创建混合策略实例
    strategy = HybridStrategy(use_ai_trader=True)
    
    # 测试单只股票
    print("\n1. 测试单只股票分析 (000001 - 平安银行):")
    result = strategy.analyze_single_stock('000001')
    
    if 'error' in result and result['error']:
        print(f"   ❌ 分析失败: {result['error_message']}")
    else:
        print(f"   ✅ 分析成功!")
        print(f"      最终得分: {result['final_decision']['final_score']}")
        print(f"      信号: {result['final_decision']['signal']}")
        print(f"      建议: {result['final_decision']['recommendation']}")
        
        # 显示组件得分
        print(f"      组件得分:")
        for component, score in result['final_decision']['component_scores'].items():
            print(f"        {component}: {score}")
    
    # 测试多只股票
    print("\n2. 测试多只股票分析:")
    symbols = ['000001', '600519', '601318']  # 平安银行, 贵州茅台, 中国平安
    results = strategy.analyze_multiple_stocks(symbols)
    
    print(f"   成功分析 {len([r for r in results.values() if 'error' not in r])}/{len(symbols)} 只股票")
    
    # 显示简要结果
    for symbol, result in results.items():
        if 'error' not in result:
            signal = result['final_decision']['signal']
            score = result['final_decision']['final_score']
            print(f"      {symbol}: {signal} ({score})")
    
    print("\n🎯 混合策略测试完成!")


if __name__ == "__main__":
    test_hybrid_strategy()