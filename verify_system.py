#!/usr/bin/env python3
"""
DSS项目新系统验证脚本（无pandas版本）
用于验证项目在新系统上的基本功能
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def test_database():
    """测试数据库功能"""
    print("=" * 60)
    print("🗄️  数据库功能测试")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('database/market_data.db')
        cursor = conn.cursor()
        
        # 测试1: 连接
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"✅ SQLite版本: {version}")
        
        # 测试2: 表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ 表数量: {len(tables)} ({', '.join(tables)})")
        
        # 测试3: 数据查询
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cursor.fetchone()[0]
        print(f"✅ 股票数量: {stock_count}")
        
        cursor.execute("SELECT symbol, name, market FROM stocks ORDER BY market, symbol")
        print("   股票列表:")
        for row in cursor.fetchall():
            print(f"     {row[0]} - {row[1]} ({row[2]})")
        
        # 测试4: 数据插入
        cursor.execute('''
            INSERT OR REPLACE INTO data_quality_log 
            (stock_id, trade_date, completeness_score, timeliness_score, 
             consistency_score, accuracy_score, overall_score, issues, status, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (1, datetime.now().strftime('%Y-%m-%d'), 0.95, 0.98, 0.92, 0.96, 0.95, 
              '新系统验证测试', 'PASS', 'system_test'))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM data_quality_log")
        quality_count = cursor.fetchone()[0]
        print(f"✅ 数据质量记录: {quality_count}")
        
        conn.close()
        print("\n🎉 数据库测试全部通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构完整性"""
    print("\n" + "=" * 60)
    print("📁 文件结构测试")
    print("=" * 60)
    
    required_files = [
        'database/market_data.db',
        'database/init_database.py',
        'integration/hybrid_strategy.py',
        'integration/technical_analyzer.py',
        'data/acquisition/cn_market.py',
        'main.py',
    ]
    
    required_dirs = [
        'database',
        'integration',
        'data',
        'learning',
    ]
    
    all_good = True
    
    print("必需文件:")
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✅ {file} ({size:,} bytes)")
        else:
            print(f"  ❌ {file} 缺失")
            all_good = False
    
    print("\n必需目录:")
    for dir in required_dirs:
        if os.path.isdir(dir):
            count = len([f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))])
            print(f"  ✅ {dir}/ ({count} 个文件)")
        else:
            print(f"  ❌ {dir}/ 缺失")
            all_good = False
    
    if all_good:
        print("\n🎉 文件结构完整！")
    else:
        print("\n⚠️  部分文件缺失")
    
    return all_good

def test_python_modules():
    """测试Python模块"""
    print("\n" + "=" * 60)
    print("🐍 Python模块测试")
    print("=" * 60)
    
    # 必需模块
    required_modules = [
        ('sqlite3', '数据库支持'),
        ('json', 'JSON处理'),
        ('urllib.request', '网络请求'),
        ('datetime', '日期时间'),
        ('pathlib', '路径处理'),
    ]
    
    # 可选模块
    optional_modules = [
        ('pandas', '数据分析'),
        ('numpy', '数值计算'),
        ('requests', 'HTTP请求'),
    ]
    
    print("必需模块:")
    all_required = True
    for module, desc in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module} - {desc}")
        except ImportError:
            print(f"  ❌ {module} - {desc}")
            all_required = False
    
    print("\n可选模块:")
    for module, desc in optional_modules:
        try:
            __import__(module)
            print(f"  ✅ {module} - {desc}")
        except ImportError:
            print(f"  ⚠️  {module} - {desc} (未安装)")
    
    if all_required:
        print("\n🎉 所有必需模块可用！")
        return True
    else:
        print("\n❌ 部分必需模块缺失")
        return False

def test_network():
    """测试网络连接"""
    print("\n" + "=" * 60)
    print("🌐 网络连接测试")
    print("=" * 60)
    
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://api.github.com/zen',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode('utf-8')
            print(f"✅ 网络连接正常")
            print(f"   响应: {data}")
            return True
    except Exception as e:
        print(f"⚠️  网络连接受限: {e}")
        return False

def generate_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("📊 测试报告总结")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'hostname': os.uname().nodename,
            'python_version': sys.version.split()[0],
            'platform': sys.platform,
        },
        'project_path': os.getcwd(),
        'tests': {}
    }
    
    # 运行所有测试
    report['tests']['database'] = test_database()
    report['tests']['file_structure'] = test_file_structure()
    report['tests']['python_modules'] = test_python_modules()
    report['tests']['network'] = test_network()
    
    # 总结
    print("\n" + "=" * 60)
    print("🎯 测试总结")
    print("=" * 60)
    
    passed = sum(report['tests'].values())
    total = len(report['tests'])
    
    print(f"通过测试: {passed}/{total}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    for test, result in report['tests'].items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {test}")
    
    # 功能评估
    print("\n" + "=" * 60)
    print("💡 功能评估")
    print("=" * 60)
    
    if report['tests']['database'] and report['tests']['file_structure']:
        print("✅ 核心功能: 数据库和文件系统完全正常")
        print("✅ 基础功能: 可以在无pandas环境下运行")
        print("⚠️  高级功能: 需要安装pandas、numpy、tushare")
        print("\n📝 建议:")
        print("  1. 如需完整功能，请联系管理员安装pandas等依赖")
        print("  2. 当前环境足以进行数据库操作和基础开发")
        print("  3. SQLite数据库功能完全正常，可继续使用")
    else:
        print("❌ 核心功能存在问题，需要修复")
    
    # 保存报告
    report_file = f"system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告已保存: {report_file}")
    
    return report

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 DSS项目新系统验证")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目路径: {os.getcwd()}")
    print(f"Python版本: {sys.version.split()[0]}")
    print("=" * 60)
    
    report = generate_report()
    
    print("\n" + "=" * 60)
    print("✅ 验证完成！")
    print("=" * 60)
    
    # 退出码
    if all(report['tests'].values()):
        sys.exit(0)
    else:
        sys.exit(1)
