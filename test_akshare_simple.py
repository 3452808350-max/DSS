#!/usr/bin/env python3
"""
测试AKShare安装和基本功能
"""

import sys
import subprocess

def check_python_environment():
    """检查Python环境"""
    print("🔍 检查Python环境...")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    # 检查pip
    try:
        import pip
        print(f"pip版本: {pip.__version__}")
        return True
    except ImportError:
        print("❌ pip未安装")
        return False

def install_akshare():
    """尝试安装AKShare"""
    print("\n📦 尝试安装AKShare...")
    
    # 方法1: 使用系统包管理器
    print("方法1: 使用apt安装...")
    try:
        result = subprocess.run(['apt', 'install', '-y', 'python3-akshare'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 通过apt安装成功")
            return True
        else:
            print(f"❌ apt安装失败: {result.stderr[:100]}")
    except Exception as e:
        print(f"❌ apt命令执行失败: {e}")
    
    # 方法2: 使用pip从源码安装
    print("\n方法2: 使用pip从源码安装...")
    try:
        # 先安装必要的依赖
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'pandas', 'requests'], 
                      check=False)
        
        # 尝试安装akshare
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'akshare'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 通过pip安装成功")
            return True
        else:
            print(f"❌ pip安装失败: {result.stderr[:200]}")
    except Exception as e:
        print(f"❌ pip安装过程出错: {e}")
    
    return False

def test_akshare_functionality():
    """测试AKShare功能"""
    print("\n🧪 测试AKShare功能...")
    
    try:
        import akshare as ak
        print(f"✅ AKShare导入成功，版本: {ak.__version__}")
        
        # 测试1: 获取A股实时行情
        print("\n测试1: 获取A股实时行情...")
        try:
            df = ak.stock_zh_a_spot_em()
            print(f"   成功获取 {len(df)} 只股票实时数据")
            print(f"   数据列: {', '.join(list(df.columns)[:6])}...")
            
            # 显示前几只股票
            print(f"   示例数据:")
            for i in range(min(3, len(df))):
                stock = df.iloc[i]
                print(f"     {stock['代码']} {stock['名称']}: {stock['最新价']} ({stock['涨跌幅']}%)")
        except Exception as e:
            print(f"   实时行情测试失败: {e}")
        
        # 测试2: 获取单只股票历史数据
        print("\n测试2: 获取平安银行历史数据...")
        try:
            df = ak.stock_zh_a_hist(
                symbol='000001',
                period='daily',
                start_date='20240101',
                end_date='20240212',
                adjust='qfq'
            )
            print(f"   成功获取 {len(df)} 条历史数据")
            print(f"   数据范围: {df.iloc[0]['日期']} 到 {df.iloc[-1]['日期']}")
            print(f"   最新收盘价: {df.iloc[-1]['收盘']}")
        except Exception as e:
            print(f"   历史数据测试失败: {e}")
        
        # 测试3: 获取财务数据
        print("\n测试3: 获取财务数据接口...")
        try:
            # 测试获取资产负债表接口
            print("   测试资产负债表接口...")
            # 这里只是测试接口是否存在，不实际调用（可能需要特定参数）
            if hasattr(ak, 'stock_financial_report_sina'):
                print("   资产负债表接口可用")
            else:
                print("   资产负债表接口不可用")
        except Exception as e:
            print(f"   财务数据测试失败: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ AKShare导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ AKShare测试过程中出错: {e}")
        return False

def create_akshare_usage_example():
    """创建AKShare使用示例"""
    print("\n📝 创建AKShare使用示例...")
    
    example_code = '''#!/usr/bin/env python3
"""
AKShare使用示例 - 基于外部专家建议白皮书
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def get_a_stock_data(symbol, days=30):
    """获取A股数据"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    try:
        # 获取历史数据
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'  # 前复权
        )
        
        print(f"✅ 成功获取 {symbol} 的 {len(df)} 条数据")
        print(f"   时间范围: {df.iloc[0]['日期']} 到 {df.iloc[-1]['日期']}")
        print(f"   最新收盘价: {df.iloc[-1]['收盘']}")
        
        return df
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return None

def get_a_stock_realtime():
    """获取A股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        
        print(f"✅ 成功获取 {len(df)} 只股票实时数据")
        print("   涨幅前5:")
        top_gainers = df.nlargest(5, '涨跌幅')
        for _, row in top_gainers.iterrows():
            print(f"     {row['代码']} {row['名称']}: {row['最新价']} ({row['涨跌幅']}%)")
        
        return df
        
    except Exception as e:
        print(f"❌ 获取实时数据失败: {e}")
        return None

def get_macro_economic_data():
    """获取宏观经济数据"""
    try:
        # 获取CPI数据
        cpi_df = ak.macro_china_cpi()
        print(f"✅ 获取CPI数据: {len(cpi_df)} 条记录")
        
        # 获取GDP数据
        gdp_df = ak.macro_china_gdp()
        print(f"✅ 获取GDP数据: {len(gdp_df)} 条记录")
        
        return {
            'cpi': cpi_df,
            'gdp': gdp_df
        }
        
    except Exception as e:
        print(f"❌ 获取宏观经济数据失败: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("AKShare数据获取示例")
    print("=" * 60)
    
    # 示例1: 获取单只股票数据
    print("\\n1. 获取平安银行(000001)最近30天数据:")
    pingan_data = get_a_stock_data('000001', days=30)
    
    # 示例2: 获取实时行情
    print("\\n2. 获取A股实时行情:")
    realtime_data = get_a_stock_realtime()
    
    # 示例3: 获取宏观经济数据
    print("\\n3. 获取宏观经济数据:")
    macro_data = get_macro_economic_data()
    
    print("\\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)
'''
    
    with open('akshare_example.py', 'w', encoding='utf-8') as f:
        f.write(example_code)
    
    print("✅ 已创建 akshare_example.py")
    print("   运行: python3 akshare_example.py")

def main():
    """主函数"""
    print("=" * 60)
    print("AKShare安装与功能测试")
    print("=" * 60)
    
    # 检查环境
    has_pip = check_python_environment()
    
    # 测试AKShare是否已安装
    try:
        import akshare as ak
        print("\n✅ AKShare已安装!")
        test_akshare_functionality()
        create_akshare_usage_example()
        return
    except ImportError:
        print("\n❌ AKShare未安装")
    
    # 如果没有pip，提供手动安装指南
    if not has_pip:
        print("\n📋 手动安装指南:")
        print("1. 安装pip:")
        print("   sudo apt update")
        print("   sudo apt install python3-pip")
        print("")
        print("2. 安装AKShare:")
        print("   pip3 install akshare --user")
        print("")
        print("3. 验证安装:")
        print("   python3 -c \"import akshare; print(akshare.__version__)\"")
        return
    
    # 尝试安装
    if install_akshare():
        # 测试功能
        if test_akshare_functionality():
            create_akshare_usage_example()
    else:
        print("\n❌ 所有安装方法都失败了")
        print("\n💡 替代方案:")
        print("1. 使用虚拟环境:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        print("   pip install akshare")
        print("")
        print("2. 使用conda环境:")
        print("   conda create -n dss python=3.9")
        print("   conda activate dss")
        print("   pip install akshare")
        print("")
        print("3. 联系系统管理员安装必要的依赖")

if __name__ == "__main__":
    main()