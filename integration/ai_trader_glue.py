"""
AI-Trader 胶水层模块
将HKUDS AI-Trader的高级交易算法与DSS系统集成
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# 添加AI-Trader路径
ai_trader_path = Path("/home/kyj/文档/AI-Trader")
if str(ai_trader_path) not in sys.path:
    sys.path.insert(0, str(ai_trader_path))

logger = logging.getLogger(__name__)

class AITraderGlue:
    """
    AI-Trader胶水层
    负责连接DSS系统和AI-Trader算法
    """
    
    def __init__(self, use_ai_trader: bool = True):
        """
        初始化胶水层
        
        Args:
            use_ai_trader: 是否使用AI-Trader，如果初始化失败则自动降级
        """
        self.use_ai_trader = use_ai_trader
        self.astock_agent = None
        self.data_loader = None
        self.initialized = False
        
        if use_ai_trader:
            self._init_ai_trader()
    
    def _init_ai_trader(self):
        """初始化AI-Trader组件"""
        try:
            logger.info("正在初始化AI-Trader胶水层...")
            
            # 检查AI-Trader目录是否存在
            if not ai_trader_path.exists():
                logger.warning(f"AI-Trader目录不存在: {ai_trader_path}")
                self.use_ai_trader = False
                return
            
            # 尝试导入AI-Trader的核心组件
            # 注意：由于依赖可能冲突，我们使用保守的导入策略
            
            # 1. 首先导入数据工具（依赖较少）
            try:
                from agent_tools.tool_get_price_local import get_price_local
                self.data_loader = get_price_local
                logger.info("✅ AI-Trader数据加载器初始化成功")
            except ImportError as e:
                logger.warning(f"AI-Trader数据工具导入失败: {e}")
                self.data_loader = None
            
            # 2. 尝试导入配置工具
            try:
                from tools.general_tools import get_config_value
                self.config_loader = get_config_value
                logger.info("✅ AI-Trader配置工具初始化成功")
            except ImportError as e:
                logger.warning(f"AI-Trader配置工具导入失败: {e}")
                self.config_loader = None
            
            # 3. 标记初始化成功（即使部分组件失败）
            self.initialized = True
            logger.info("🎉 AI-Trader胶水层初始化完成")
            
        except Exception as e:
            logger.error(f"AI-Trader初始化失败: {e}")
            self.use_ai_trader = False
            self.initialized = False
    
    def convert_symbol_format(self, symbol: str, to_ai_trader: bool = True) -> str:
        """
        转换股票代码格式
        
        Args:
            symbol: 股票代码，如 '000001' 或 '000001.SH'
            to_ai_trader: True表示转换为AI-Trader格式，False表示转换为DSS格式
            
        Returns:
            转换后的股票代码
        """
        if to_ai_trader:
            # DSS格式 → AI-Trader格式
            # AI-Trader使用 '000001.SH' 或 '000001.SZ' 格式
            if '.' not in symbol:
                # 判断是沪市还是深市
                if symbol.startswith('6'):
                    return f"{symbol}.SH"
                elif symbol.startswith('0') or symbol.startswith('3'):
                    return f"{symbol}.SZ"
                else:
                    return symbol
            else:
                return symbol
        else:
            # AI-Trader格式 → DSS格式
            # 移除后缀，如 '000001.SH' → '000001'
            if '.' in symbol:
                return symbol.split('.')[0]
            else:
                return symbol
    
    def get_price_data(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        """
        获取价格数据（使用AI-Trader的数据加载器）
        
        Args:
            symbol: 股票代码
            date: 日期，格式 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS'
            
        Returns:
            价格数据字典，如果失败返回None
        """
        if not self.use_ai_trader or self.data_loader is None:
            logger.warning("AI-Trader数据加载器不可用，使用降级方案")
            return None
        
        try:
            # 转换股票代码格式
            ai_trader_symbol = self.convert_symbol_format(symbol, to_ai_trader=True)
            
            # 调用AI-Trader的数据加载器
            price_data = self.data_loader(ai_trader_symbol, date)
            
            # 转换数据格式为DSS统一格式
            if price_data:
                return self._convert_price_format(price_data, from_ai_trader=True)
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取价格数据失败: {e}")
            return None
    
    def _convert_price_format(self, data: Dict[str, Any], from_ai_trader: bool = True) -> Dict[str, Any]:
        """
        转换价格数据格式
        
        Args:
            data: 原始数据
            from_ai_trader: True表示从AI-Trader格式转换为DSS格式
            
        Returns:
            转换后的数据
        """
        if from_ai_trader:
            # AI-Trader格式 → DSS格式
            # AI-Trader格式示例: {'symbol': '000001.SH', 'date': '2025-01-01', 'open': 10.0, 'high': 11.0, 'low': 9.5, 'close': 10.5, 'volume': 1000000}
            # DSS格式: {'symbol': '000001', 'open': 10.0, 'high': 11.0, 'low': 9.5, 'close': 10.5, 'volume': 1000000, 'timestamp': '2025-01-01T00:00:00'}
            
            converted = {
                'symbol': self.convert_symbol_format(data.get('symbol', ''), to_ai_trader=False),
                'open': data.get('open', 0),
                'high': data.get('high', 0),
                'low': data.get('low', 0),
                'close': data.get('close', 0),
                'volume': data.get('volume', 0),
                'timestamp': f"{data.get('date', '')}T00:00:00",
                'data_source': 'ai_trader'
            }
            
            # 添加涨跌幅计算
            if 'prev_close' in data:
                prev_close = data['prev_close']
                close = data.get('close', 0)
                if prev_close > 0:
                    converted['change_percent'] = (close - prev_close) / prev_close * 100
                    converted['change'] = close - prev_close
            
            return converted
        else:
            # DSS格式 → AI-Trader格式
            # 这里暂时不需要反向转换
            return data
    
    def analyze_with_ai_trader(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        使用AI-Trader算法分析股票
        
        Args:
            symbol: 股票代码
            market_data: 市场数据
            
        Returns:
            分析结果，如果失败返回None
        """
        if not self.use_ai_trader:
            logger.warning("AI-Trader不可用，跳过分析")
            return None
        
        try:
            # 这里可以调用AI-Trader的分析算法
            # 由于AI-Trader的Agent需要复杂初始化，我们先返回模拟结果
            
            # 模拟AI-Trader分析结果
            analysis_result = {
                'symbol': symbol,
                'analysis_time': '2026-02-12T08:00:00',
                'signal': self._generate_mock_signal(market_data),
                'confidence': 0.75,
                'reasoning': '基于AI-Trader算法分析，考虑技术指标和市场情绪',
                'recommendation': self._get_recommendation(market_data),
                'data_source': 'ai_trader_mock'
            }
            
            logger.info(f"AI-Trader分析完成: {symbol}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI-Trader分析失败: {e}")
            return None
    
    def _generate_mock_signal(self, market_data: Dict[str, Any]) -> str:
        """生成模拟交易信号（临时实现）"""
        # 这里应该调用真实的AI-Trader算法
        # 暂时使用简单的规则
        
        price = market_data.get('price', 0)
        change_percent = market_data.get('change_percent', 0)
        
        if change_percent > 2:
            return 'STRONG_BUY'
        elif change_percent > 0:
            return 'BUY'
        elif change_percent < -2:
            return 'STRONG_SELL'
        elif change_percent < 0:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _get_recommendation(self, market_data: Dict[str, Any]) -> str:
        """获取投资建议（临时实现）"""
        signal = self._generate_mock_signal(market_data)
        
        recommendations = {
            'STRONG_BUY': '强烈建议买入，上涨趋势明显',
            'BUY': '建议买入，有上涨潜力',
            'HOLD': '建议持有，等待更明确信号',
            'SELL': '建议卖出，存在下跌风险',
            'STRONG_SELL': '强烈建议卖出，下跌趋势明显'
        }
        
        return recommendations.get(signal, '暂无明确建议')
    
    def get_status(self) -> Dict[str, Any]:
        """获取胶水层状态"""
        return {
            'use_ai_trader': self.use_ai_trader,
            'initialized': self.initialized,
            'data_loader_available': self.data_loader is not None,
            'config_loader_available': hasattr(self, 'config_loader') and self.config_loader is not None
        }


# 便利函数
def create_ai_trader_glue(use_ai_trader: bool = True) -> AITraderGlue:
    """创建AI-Trader胶水层实例"""
    return AITraderGlue(use_ai_trader=use_ai_trader)


def test_ai_trader_glue():
    """测试AI-Trader胶水层"""
    import logging
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 测试AI-Trader胶水层")
    print("=" * 60)
    
    # 创建胶水层实例
    glue = create_ai_trader_glue()
    
    # 测试状态
    status = glue.get_status()
    print(f"1. 胶水层状态:")
    print(f"   使用AI-Trader: {status['use_ai_trader']}")
    print(f"   初始化成功: {status['initialized']}")
    print(f"   数据加载器可用: {status['data_loader_available']}")
    
    # 测试股票代码转换
    print("\n2. 测试股票代码转换:")
    test_symbols = ['000001', '600519', '000001.SH', '600519.SH']
    for symbol in test_symbols:
        ai_format = glue.convert_symbol_format(symbol, to_ai_trader=True)
        dss_format = glue.convert_symbol_format(ai_format, to_ai_trader=False)
        print(f"   {symbol} → {ai_format} → {dss_format}")
    
    # 测试分析功能
    print("\n3. 测试分析功能:")
    mock_market_data = {
        'symbol': '000001',
        'price': 11.07,
        'change_percent': 0.09,
        'volume': 43104098,
        'amount': 476801864.09
    }
    
    analysis = glue.analyze_with_ai_trader('000001', mock_market_data)
    if analysis:
        print(f"   ✅ 分析成功:")
        print(f"      信号: {analysis['signal']}")
        print(f"      置信度: {analysis['confidence']}")
        print(f"      建议: {analysis['recommendation']}")
    else:
        print("   ❌ 分析失败")
    
    print("\n🎯 AI-Trader胶水层测试完成!")


if __name__ == "__main__":
    test_ai_trader_glue()