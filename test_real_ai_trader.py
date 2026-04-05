#!/usr/bin/env python3
"""
测试真实的AI-Trader数据获取
"""

import sys
from pathlib import Path
import logging

# 添加AI-Trader路径
ai_trader_path = Path("/home/kyj/文档/AI-Trader")
if str(ai_trader_path) not in sys.path:
    sys.path.insert(0, str(ai_trader_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_data_loading():
    """测试真实数据加载"""
    print("🧪 测试真实的AI-Trader数据获取")
    print("=" * 60)
    
    try:
        # 导入AI-Trader的数据工具
        from agent_tools.tool_get_price_local import get_price_local
        
        print("✅ AI-Trader数据工具导入成功")
        
        # 测试获取A股数据
        print("\n1. 测试A股数据获取 (000001.SH - 平安银行):")
        try:
            # AI-Trader使用 '000001.SH' 格式
            result = get_price_local('000001.SH', '2026-02-11')
            print(f"   结果类型: {type(result)}")
            if isinstance(result, dict):
                print(f"   数据键: {list(result.keys())}")
                if 'symbol' in result:
                    print(f"   股票: {result['symbol']}")
                if 'date' in result:
                    print(f"   日期: {result['date']}")
                if 'close' in result:
                    print(f"   收盘价: {result['close']}")
            else:
                print(f"   返回结果: {result}")
        except Exception as e:
            print(f"   ❌ A股数据获取失败: {e}")
        
        # 测试获取美股数据
        print("\n2. 测试美股数据获取 (AAPL - 苹果):")
        try:
            result = get_price_local('AAPL', '2026-02-11')
            print(f"   结果类型: {type(result)}")
            if isinstance(result, dict):
                print(f"   数据键: {list(result.keys())}")
                if 'symbol' in result:
                    print(f"   股票: {result['symbol']}")
                if 'close' in result:
                    print(f"   收盘价: ${result['close']}")
        except Exception as e:
            print(f"   ❌ 美股数据获取失败: {e}")
        
        # 测试查看数据文件
        print("\n3. 查看AI-Trader数据文件:")
        try:
            import json
            from pathlib import Path
            
            # 查看A股数据文件
            a_stock_data_path = ai_trader_path / "data" / "A_stock" / "merged.jsonl"
            if a_stock_data_path.exists():
                print(f"   A股数据文件: {a_stock_data_path}")
                print(f"   文件大小: {a_stock_data_path.stat().st_size:,} 字节")
                
                # 读取前几行
                with open(a_stock_data_path, 'r', encoding='utf-8') as f:
                    lines = []
                    for i in range(3):
                        line = f.readline()
                        if line:
                            lines.append(line.strip())
                    
                    if lines:
                        print(f"   前3行数据示例:")
                        for i, line in enumerate(lines):
                            try:
                                data = json.loads(line)
                                symbol = data.get('symbol', 'N/A')
                                date = data.get('date', 'N/A')
                                close = data.get('close', 'N/A')
                                print(f"      {i+1}. {symbol} - {date}: {close}")
                            except:
                                print(f"      {i+1}. {line[:50]}...")
            else:
                print(f"   ⚠️ A股数据文件不存在: {a_stock_data_path}")
                
        except Exception as e:
            print(f"   ❌ 查看数据文件失败: {e}")
        
        print("\n🎯 AI-Trader真实数据测试完成!")
        
    except ImportError as e:
        print(f"❌ 导入AI-Trader工具失败: {e}")
        print("请检查依赖是否安装完整")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_ai_trader_config():
    """测试AI-Trader配置"""
    print("\n🔧 测试AI-Trader配置工具")
    print("=" * 60)
    
    try:
        from tools.general_tools import get_config_value
        
        # 测试获取配置
        test_keys = ['LOG_FILE', 'SIGNATURE', 'INIT_DATE']
        for key in test_keys:
            try:
                value = get_config_value(key)
                print(f"   {key}: {value}")
            except Exception as e:
                print(f"   {key}: 获取失败 - {e}")
                
    except ImportError as e:
        print(f"❌ 导入配置工具失败: {e}")
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")

if __name__ == "__main__":
    test_real_data_loading()
    test_ai_trader_config()