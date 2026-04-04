"""
技术分析器 - 为混合策略提供专业的技术分析
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """
    技术分析器
    提供各种技术指标计算
    """
    
    def __init__(self):
        """初始化技术分析器"""
        logger.info("技术分析器初始化完成")
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """
        计算相对强弱指数 (RSI)
        
        Args:
            prices: 价格列表（最近的价格在最后）
            period: RSI周期，默认14
            
        Returns:
            RSI值，如果数据不足返回None
        """
        if len(prices) < period + 1:
            logger.warning(f"数据不足计算RSI，需要至少{period+1}个价格，当前{len(prices)}个")
            return None
        
        # 计算价格变化
        deltas = np.diff(prices)
        
        # 分离上涨和下跌
        up = deltas.copy()
        down = deltas.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        down = np.abs(down)
        
        # 计算平均上涨和下跌
        avg_gain = np.mean(up[-period:])
        avg_loss = np.mean(down[-period:])
        
        # 避免除零
        if avg_loss == 0:
            return 100.0
        
        # 计算RS
        rs = avg_gain / avg_loss
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def calculate_moving_average(self, prices: List[float], period: int) -> Optional[float]:
        """
        计算移动平均线
        
        Args:
            prices: 价格列表
            period: 移动平均周期
            
        Returns:
            移动平均值，如果数据不足返回None
        """
        if len(prices) < period:
            logger.warning(f"数据不足计算{period}日移动平均，需要至少{period}个价格")
            return None
        
        return round(np.mean(prices[-period:]), 2)
    
    def calculate_macd(self, prices: List[float], 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Optional[Dict[str, float]]:
        """
        计算MACD指标
        
        Args:
            prices: 价格列表
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            MACD指标字典，包含MACD、信号线和柱状图
        """
        if len(prices) < slow_period + signal_period:
            logger.warning(f"数据不足计算MACD，需要至少{slow_period + signal_period}个价格")
            return None
        
        # 计算EMA
        def calculate_ema(data, period):
            weights = np.exp(np.linspace(-1., 0., period))
            weights /= weights.sum()
            
            ema = np.convolve(data, weights, mode='full')[:len(data)]
            ema[:period] = ema[period]
            return ema
        
        # 计算快线和慢线EMA
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        # 计算MACD线
        macd_line = ema_fast - ema_slow
        
        # 计算信号线
        signal_line = calculate_ema(macd_line, signal_period)
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        return {
            'macd': round(macd_line[-1], 4),
            'signal': round(signal_line[-1], 4),
            'histogram': round(histogram[-1], 4),
            'cross': 'bullish' if histogram[-1] > 0 else 'bearish'
        }
    
    def calculate_bollinger_bands(self, prices: List[float], 
                                 period: int = 20, 
                                 std_dev: float = 2.0) -> Optional[Dict[str, float]]:
        """
        计算布林带
        
        Args:
            prices: 价格列表
            period: 移动平均周期
            std_dev: 标准差倍数
            
        Returns:
            布林带指标字典
        """
        if len(prices) < period:
            logger.warning(f"数据不足计算布林带，需要至少{period}个价格")
            return None
        
        # 计算移动平均
        sma = np.mean(prices[-period:])
        
        # 计算标准差
        std = np.std(prices[-period:])
        
        # 计算上下轨
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        # 计算当前价格相对于布林带的位置
        current_price = prices[-1]
        bb_position = (current_price - lower_band) / (upper_band - lower_band) * 100
        
        return {
            'upper': round(upper_band, 2),
            'middle': round(sma, 2),
            'lower': round(lower_band, 2),
            'width': round((upper_band - lower_band) / sma * 100, 2),  # 带宽百分比
            'position': round(bb_position, 2),  # 价格在布林带中的位置百分比
            'squeeze': 'yes' if (upper_band - lower_band) / sma < 0.1 else 'no'  # 是否收缩
        }
    
    def calculate_atr(self, prices: List[float], period: int = 14) -> Optional[float]:
        """
        计算平均真实波幅 (ATR)
        
        Args:
            prices: 价格列表
            period: ATR周期，默认14
            
        Returns:
            ATR值，如果数据不足返回None
        """
        if len(prices) < period + 1:
            logger.warning(f"数据不足计算ATR，需要至少{period+1}个价格")
            return None
        
        # 计算真实波幅 (True Range)
        true_ranges = []
        for i in range(1, len(prices)):
            high_low = abs(prices[i] - prices[i-1])
            true_ranges.append(high_low)
        
        # 计算ATR（简单移动平均）
        atr = np.mean(true_ranges[-period:])
        
        return round(atr, 4)
    
    def calculate_adx(self, prices: List[float], period: int = 14) -> Optional[Dict[str, float]]:
        """
        计算平均趋向指数 (ADX) - 用于判断趋势强度
        
        Args:
            prices: 价格列表
            period: ADX周期，默认14
            
        Returns:
            ADX指标字典，包含ADX、+DI、-DI值
        """
        if len(prices) < period * 2:
            logger.warning(f"数据不足计算ADX，需要至少{period*2}个价格")
            return None
        
        prices = np.array(prices)
        n = len(prices)
        
        # 计算+DM和-DM
        plus_dm = np.zeros(n - 1)
        minus_dm = np.zeros(n - 1)
        
        for i in range(1, n):
            up_move = prices[i] - prices[i-1]
            down_move = prices[i-1] - prices[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i-1] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i-1] = down_move
        
        # 计算真实波幅
        tr = np.abs(np.diff(prices))
        
        # 平滑处理
        def smooth(data, period):
            smoothed = np.zeros(len(data))
            smoothed[period-1] = np.sum(data[:period])
            for i in range(period, len(data)):
                smoothed[i] = smoothed[i-1] - smoothed[i-1]/period + data[i]
            return smoothed
        
        smoothed_plus_dm = smooth(plus_dm, period)
        smoothed_minus_dm = smooth(minus_dm, period)
        smoothed_tr = smooth(tr, period)
        
        # 计算+DI和-DI
        plus_di = np.zeros(len(plus_dm))
        minus_di = np.zeros(len(minus_dm))
        
        for i in range(len(plus_dm)):
            if smoothed_tr[i] > 0:
                plus_di[i] = (smoothed_plus_dm[i] / smoothed_tr[i]) * 100
                minus_di[i] = (smoothed_minus_dm[i] / smoothed_tr[i]) * 100
        
        # 计算DX
        dx = np.zeros(len(plus_di))
        for i in range(len(plus_di)):
            if (plus_di[i] + minus_di[i]) > 0:
                dx[i] = (abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i])) * 100
        
        # 计算ADX（DX的平滑）
        adx = np.mean(dx[-period:])
        avg_plus_di = np.mean(plus_di[-period:])
        avg_minus_di = np.mean(minus_di[-period:])
        
        return {
            'adx': round(adx, 2),
            'plus_di': round(avg_plus_di, 2),
            'minus_di': round(avg_minus_di, 2),
            'trend_strength': 'strong' if adx > 25 else 'weak' if adx < 20 else 'moderate',
            'trend_direction': 'bullish' if avg_plus_di > avg_minus_di else 'bearish'
        }
    
    def detect_sideways_market(self, prices: List[float], 
                               volumes: Optional[List[int]] = None,
                               lookback: int = 20) -> Dict[str, Any]:
        """
        检测股票是否处于横盘状态
        
        横盘检测指标：
        - 价格波动率（ATR/价格）
        - 布林带宽度
        - ADX趋势强度
        - 价格区间持续时间
        
        Args:
            prices: 价格列表
            volumes: 成交量列表（可选）
            lookback: 回顾周期，默认20
            
        Returns:
            横盘检测结果字典
        """
        if len(prices) < lookback:
            return {
                'is_sideways': False,
                'confidence': 0.0,
                'reason': '数据不足',
                'details': {}
            }
        
        recent_prices = prices[-lookback:]
        
        # 1. 计算价格波动率（使用ATR）
        atr = self.calculate_atr(prices, period=14)
        avg_price = np.mean(recent_prices)
        volatility_ratio = (atr / avg_price * 100) if atr and avg_price > 0 else None
        
        # 波动率评分：波动率越低，横盘可能性越高
        volatility_score = 0
        if volatility_ratio is not None:
            if volatility_ratio < 1.5:
                volatility_score = 100  # 极低波动
            elif volatility_ratio < 2.5:
                volatility_score = 80
            elif volatility_ratio < 3.5:
                volatility_score = 60
            elif volatility_ratio < 5:
                volatility_score = 40
            else:
                volatility_score = 20
        
        # 2. 计算布林带宽度
        bb = self.calculate_bollinger_bands(prices, period=20)
        bb_score = 0
        bb_width = bb['width'] if bb else None
        
        if bb_width is not None:
            if bb_width < 5:
                bb_score = 100  # 极度收缩
            elif bb_width < 10:
                bb_score = 80   # 横盘区间
            elif bb_width < 15:
                bb_score = 50
            else:
                bb_score = 20
        
        # 3. 计算ADX判断趋势强度
        adx_result = self.calculate_adx(prices, period=14)
        adx_score = 0
        adx_value = adx_result['adx'] if adx_result else None
        
        if adx_value is not None:
            if adx_value < 20:
                adx_score = 100  # 无趋势
            elif adx_value < 25:
                adx_score = 70
            elif adx_value < 35:
                adx_score = 40
            else:
                adx_score = 10  # 强趋势
        
        # 4. 计算价格区间持续时间
        price_range = max(recent_prices) - min(recent_prices)
        price_range_pct = (price_range / avg_price) * 100 if avg_price > 0 else 0
        
        # 判断价格是否在一定区间内
        range_score = 0
        if price_range_pct < 5:
            range_score = 100
        elif price_range_pct < 8:
            range_score = 70
        elif price_range_pct < 12:
            range_score = 50
        else:
            range_score = 20
        
        # 5. 计算横盘持续时间（连续天数在区间内）
        # 简化：统计最近价格是否在布林带中轨附近震荡
        if bb:
            middle = bb['middle']
            bandwidth = bb['width']
            oscillation_count = 0
            for i, p in enumerate(recent_prices[-10:]):  # 最近10天
                # 判断是否在中轨附近（带宽的30%范围内）
                deviation = abs(p - middle) / middle * 100 if middle > 0 else 0
                if deviation < bandwidth * 0.3:
                    oscillation_count += 1
            oscillation_score = oscillation_count * 10
        else:
            oscillation_score = 50
        
        # 综合评分
        scores = {
            'volatility_score': volatility_score,
            'bb_score': bb_score,
            'adx_score': adx_score,
            'range_score': range_score,
            'oscillation_score': oscillation_score
        }
        
        # 加权平均
        weights = {
            'volatility_score': 0.25,
            'bb_score': 0.25,
            'adx_score': 0.20,
            'range_score': 0.15,
            'oscillation_score': 0.15
        }
        
        total_score = sum(scores[k] * weights[k] for k in scores if scores[k] is not None)
        valid_weights = sum(weights[k] for k in scores if scores[k] is not None)
        final_score = total_score / valid_weights if valid_weights > 0 else 0
        
        # 判断是否横盘
        is_sideways = final_score >= 60
        
        # 估算横盘持续时间
        if is_sideways:
            # 向前追溯，找到横盘开始的时间点
            sideways_duration = self._estimate_sideways_duration(prices, final_score)
        else:
            sideways_duration = 0
        
        # 计算突破概率
        breakthrough_probability = self._calculate_breakthrough_probability(
            final_score, adx_value, volatility_ratio, volumes
        )
        
        # 生成建议操作
        recommendation = self._generate_sideways_recommendation(
            is_sideways, sideways_duration, breakthrough_probability, final_score
        )
        
        return {
            'is_sideways': is_sideways,
            'confidence': round(final_score / 100, 2),
            'sideways_duration': sideways_duration,  # 估算的横盘天数
            'breakthrough_probability': round(breakthrough_probability, 2),
            'recommendation': recommendation,
            'details': {
                'volatility_ratio': round(volatility_ratio, 2) if volatility_ratio else None,
                'bollinger_width': round(bb_width, 2) if bb_width else None,
                'adx': adx_value,
                'price_range_pct': round(price_range_pct, 2),
                'avg_price': round(avg_price, 2),
                'scores': scores,
                'final_score': round(final_score, 2)
            }
        }
    
    def _estimate_sideways_duration(self, prices: List[float], score: float) -> int:
        """
        估算横盘持续天数
        
        Args:
            prices: 价格列表
            score: 横盘评分
            
        Returns:
            估算的横盘持续天数
        """
        if len(prices) < 20:
            return 0
        
        # 计算移动平均和标准差
        window = 10
        durations = []
        
        for i in range(window, len(prices)):
            segment = prices[i-window:i]
            mean_price = np.mean(segment)
            std_price = np.std(segment)
            cv = (std_price / mean_price) * 100 if mean_price > 0 else 100
            
            # 变异系数小于5%视为横盘
            if cv < 5:
                durations.append(i)
        
        # 返回连续横盘的天数
        if not durations:
            return 0
        
        # 找最长的连续段
        max_duration = 1
        current_duration = 1
        for i in range(1, len(durations)):
            if durations[i] == durations[i-1] + 1:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 1
        
        return min(max_duration, len(prices))
    
    def _calculate_breakthrough_probability(self, 
                                            sideways_score: float,
                                            adx: Optional[float],
                                            volatility_ratio: Optional[float],
                                            volumes: Optional[List[int]]) -> float:
        """
        计算突破概率
        
        Args:
            sideways_score: 横盘评分
            adx: ADX值
            volatility_ratio: 波动率
            volumes: 成交量列表
            
        Returns:
            突破概率 (0-1)
        """
        # 基础突破概率：横盘时间越长，突破概率越高
        base_prob = min(sideways_score / 100 * 0.5 + 0.3, 0.9)
        
        # ADX调整：ADX上升预示趋势形成
        if adx is not None:
            if adx > 30:
                base_prob += 0.15
            elif adx > 25:
                base_prob += 0.08
            elif adx < 15:
                base_prob -= 0.1
        
        # 波动率调整：低波动后突破更可能
        if volatility_ratio is not None:
            if volatility_ratio < 2:
                base_prob += 0.1
            elif volatility_ratio > 4:
                base_prob -= 0.05
        
        # 成交量调整：成交量萎缩后突破更可能
        if volumes and len(volumes) >= 10:
            recent_vol = np.mean(volumes[-5:])
            earlier_vol = np.mean(volumes[-10:-5])
            if recent_vol < earlier_vol * 0.7:  # 成交量萎缩
                base_prob += 0.1
            elif recent_vol > earlier_vol * 1.3:  # 成交量放大
                base_prob += 0.15  # 可能已经突破
        
        return max(0.1, min(0.95, base_prob))
    
    def _generate_sideways_recommendation(self, 
                                          is_sideways: bool,
                                          duration: int,
                                          breakthrough_prob: float,
                                          score: float) -> str:
        """
        生成横盘状态下的操作建议
        
        Args:
            is_sideways: 是否横盘
            duration: 横盘持续时间
            breakthrough_prob: 突破概率
            score: 横盘评分
            
        Returns:
            操作建议字符串
        """
        if not is_sideways:
            return "非横盘状态，正常交易"
        
        recommendations = []
        
        if duration < 5:
            recommendations.append("横盘初期")
            recommendations.append("观望为主，等待方向明确")
        elif duration < 15:
            recommendations.append(f"横盘{duration}天")
            if breakthrough_prob > 0.6:
                recommendations.append("突破概率较高，可考虑埋伏")
            else:
                recommendations.append("继续观望")
        else:
            recommendations.append(f"横盘{duration}天，整理充分")
            if breakthrough_prob > 0.7:
                recommendations.append("突破在即，密切关注")
                recommendations.append("建议：设置突破提醒，放量突破时跟进")
            elif breakthrough_prob > 0.5:
                recommendations.append("突破概率中等，可轻仓试探")
            else:
                recommendations.append("横盘持续，可能继续整理")
        
        # 添加风险提示
        if score > 80:
            recommendations.append("⚠️ 极度收敛，波动将至")
        elif score > 70:
            recommendations.append("注意成交量变化")
        
        return " | ".join(recommendations)
    
    def calculate_support_resistance(self, prices: List[float], 
                                    lookback: int = 20) -> Dict[str, Any]:
        """
        计算支撑位和阻力位
        
        Args:
            prices: 价格列表
            lookback: 回顾周期
            
        Returns:
            支撑阻力位字典
        """
        if len(prices) < lookback:
            lookback = len(prices)
        
        recent_prices = prices[-lookback:]
        
        # 简单的支撑阻力位计算
        high = max(recent_prices)
        low = min(recent_prices)
        current = recent_prices[-1]
        
        # 计算关键水平
        pivot = (high + low + current) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        return {
            'pivot': round(pivot, 2),
            'resistance1': round(r1, 2),
            'resistance2': round(r2, 2),
            'support1': round(s1, 2),
            'support2': round(s2, 2),
            'current_position': 'above_pivot' if current > pivot else 'below_pivot'
        }
    
    def calculate_volume_analysis(self, volumes: List[int], 
                                 prices: List[float]) -> Dict[str, Any]:
        """
        成交量分析
        
        Args:
            volumes: 成交量列表
            prices: 价格列表
            
        Returns:
            成交量分析结果
        """
        if len(volumes) < 2 or len(prices) < 2:
            return {'error': '数据不足'}
        
        # 计算成交量指标
        avg_volume = np.mean(volumes)
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # 价格变化
        price_change = prices[-1] - prices[-2]
        
        # 量价关系
        if price_change > 0 and volume_ratio > 1.2:
            volume_price = '价涨量增 - 强势'
        elif price_change > 0 and volume_ratio < 0.8:
            volume_price = '价涨量缩 - 谨慎'
        elif price_change < 0 and volume_ratio > 1.2:
            volume_price = '价跌量增 - 弱势'
        elif price_change < 0 and volume_ratio < 0.8:
            volume_price = '价跌量缩 - 观望'
        else:
            volume_price = '量价平衡'
        
        return {
            'volume_ratio': round(volume_ratio, 2),
            'volume_status': '高成交量' if volume_ratio > 1.2 else '低成交量' if volume_ratio < 0.8 else '正常成交量',
            'volume_price_relation': volume_price,
            'avg_volume': int(avg_volume),
            'current_volume': current_volume
        }
    
    def generate_technical_signals(self, prices: List[float], 
                                  volumes: List[int]) -> Dict[str, Any]:
        """
        生成综合技术信号
        
        Args:
            prices: 价格列表（至少30个数据点）
            volumes: 成交量列表（与价格对应）
            
        Returns:
            综合技术分析结果
        """
        signals = []
        confidence = 0.5
        
        # 检查数据充足性
        if len(prices) < 30:
            logger.warning("数据不足进行完整技术分析")
            return {
                'signals': ['数据不足'],
                'confidence': 0.3,
                'recommendation': '需要更多数据'
            }
        
        # 1. RSI分析
        rsi = self.calculate_rsi(prices)
        if rsi is not None:
            if rsi > 70:
                signals.append(f"RSI超买({rsi})")
                confidence -= 0.15
            elif rsi < 30:
                signals.append(f"RSI超卖({rsi})")
                confidence += 0.15
            elif rsi > 50:
                signals.append(f"RSI偏强({rsi})")
                confidence += 0.05
            else:
                signals.append(f"RSI偏弱({rsi})")
                confidence -= 0.05
        
        # 2. 移动平均分析
        ma5 = self.calculate_moving_average(prices, 5)
        ma10 = self.calculate_moving_average(prices, 10)
        ma20 = self.calculate_moving_average(prices, 20)
        
        current_price = prices[-1]
        
        if ma5 and ma10:
            if current_price > ma5 > ma10:
                signals.append("多头排列")
                confidence += 0.2
            elif current_price < ma5 < ma10:
                signals.append("空头排列")
                confidence -= 0.2
        
        # 3. MACD分析
        macd = self.calculate_macd(prices)
        if macd:
            if macd['cross'] == 'bullish':
                signals.append("MACD金叉")
                confidence += 0.1
            else:
                signals.append("MACD死叉")
                confidence -= 0.1
        
        # 4. 布林带分析
        bb = self.calculate_bollinger_bands(prices)
        if bb:
            if current_price > bb['upper']:
                signals.append("突破上轨")
                confidence -= 0.1
            elif current_price < bb['lower']:
                signals.append("突破下轨")
                confidence += 0.1
            elif bb['position'] > 80:
                signals.append("接近上轨")
                confidence -= 0.05
            elif bb['position'] < 20:
                signals.append("接近下轨")
                confidence += 0.05
        
        # 5. 成交量分析
        if len(volumes) >= 2:
            volume_analysis = self.calculate_volume_analysis(volumes, prices)
            signals.append(volume_analysis['volume_price_relation'])
        
        # 6. 横盘检测
        sideways_result = self.detect_sideways_market(prices, volumes)
        
        if sideways_result['is_sideways']:
            sideways_signal = f"横盘状态({sideways_result['sideways_duration']}天)"
            signals.append(sideways_signal)
            signals.append(f"突破概率{int(sideways_result['breakthrough_probability']*100)}%")
            
            # 横盘状态下调整置信度
            # 如果突破概率高，可以保留原有信号
            # 如果横盘持续，降低信号强度
            if sideways_result['breakthrough_probability'] < 0.5:
                confidence *= 0.7  # 降低置信度
        
        # 生成建议
        if sideways_result['is_sideways']:
            # 横盘状态下使用横盘建议
            recommendation = sideways_result['recommendation']
        elif confidence >= 0.7:
            recommendation = "强烈买入"
        elif confidence >= 0.6:
            recommendation = "买入"
        elif confidence >= 0.4:
            recommendation = "持有"
        elif confidence >= 0.3:
            recommendation = "卖出"
        else:
            recommendation = "强烈卖出"
        
        result = {
            'signals': signals,
            'confidence': round(confidence, 2),
            'recommendation': recommendation,
            'indicators': {
                'rsi': rsi,
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'macd': macd,
                'bollinger_bands': bb
            }
        }
        
        # 添加横盘检测结果
        if sideways_result['is_sideways']:
            result['sideways_detection'] = sideways_result
        
        return result
    
# 测试函数
def test_technical_analyzer():
    """测试技术分析器"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试技术分析器")
    print("=" * 60)
    
    analyzer = TechnicalAnalyzer()
    
    # 生成测试数据
    np.random.seed(42)
    test_prices = list(100 + np.cumsum(np.random.randn(100) * 2))
    test_volumes = list(np.random.randint(1000000, 5000000, 100))
    
    print(f"测试数据: {len(test_prices)}个价格，{len(test_volumes)}个成交量")
    
    # 测试RSI
    rsi = analyzer.calculate_rsi(test_prices)
    print(f"\n1. RSI: {rsi}")
    
    # 测试移动平均
    ma20 = analyzer.calculate_moving_average(test_prices, 20)
    print(f"2. 20日移动平均: {ma20}")
    
    # 测试MACD
    macd = analyzer.calculate_macd(test_prices)
    if macd:
        print(f"3. MACD: {macd['macd']}, 信号线: {macd['signal']}, 柱状图: {macd['histogram']}")
    
    # 测试布林带
    bb = analyzer.calculate_bollinger_bands(test_prices)
    if bb:
        print(f"4. 布林带: 上轨={bb['upper']}, 中轨={bb['middle']}, 下轨={bb['lower']}")
        print(f"   位置: {bb['position']}%, 收缩: {bb['squeeze']}")
    
    # 测试综合信号
    signals = analyzer.generate_technical_signals(test_prices, test_volumes)
    print(f"\n5. 综合技术信号:")
    print(f"   信号列表: {signals['signals'][:5]}...")
    print(f"   置信度: {signals['confidence']}")
    print(f"   建议: {signals['recommendation']}")
    
    # 测试横盘检测
    print(f"\n6. 横盘检测测试:")
    
    # 测试横盘市场数据（低波动）
    sideways_prices = list(100 + np.random.randn(50) * 0.5)  # 小波动
    sideways_volumes = list(np.random.randint(1000000, 2000000, 50))  # 低成交量
    sideways_result = analyzer.detect_sideways_market(sideways_prices, sideways_volumes)
    print(f"   横盘市场测试:")
    print(f"     是否横盘: {sideways_result['is_sideways']}")
    print(f"     置信度: {sideways_result['confidence']}")
    print(f"     横盘持续: {sideways_result['sideways_duration']}天")
    print(f"     突破概率: {sideways_result['breakthrough_probability']}")
    print(f"     建议: {sideways_result['recommendation']}")
    
    # 测试趋势市场数据（高波动）
    trending_prices = list(100 + np.cumsum(np.random.randn(50) * 2))  # 大波动
    trending_volumes = list(np.random.randint(3000000, 5000000, 50))  # 高成交量
    trending_result = analyzer.detect_sideways_market(trending_prices, trending_volumes)
    print(f"\n   趋势市场测试:")
    print(f"     是否横盘: {trending_result['is_sideways']}")
    print(f"     置信度: {trending_result['confidence']}")
    print(f"     建议: {trending_result['recommendation']}")
    
    # 测试ATR
    atr = analyzer.calculate_atr(test_prices)
    print(f"\n7. ATR测试: {atr}")
    
    # 测试ADX
    adx = analyzer.calculate_adx(test_prices)
    if adx:
        print(f"8. ADX测试: ADX={adx['adx']}, +DI={adx['plus_di']}, -DI={adx['minus_di']}")
        print(f"   趋势强度: {adx['trend_strength']}, 方向: {adx['trend_direction']}")
    
    print("\n🎯 技术分析器测试完成!")


if __name__ == "__main__":
    test_technical_analyzer()