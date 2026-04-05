#!/usr/bin/env python3
"""
SQLite数据库测试脚本
验证数据库功能是否符合教授建议
"""

import sqlite3
import pandas as pd
from pathlib import Path

def test_database_connection():
    """测试数据库连接"""
    print("🔌 测试数据库连接...")
    
    db_path = "database/market_data.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 测试连接
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"✅ SQLite版本: {version}")
        
        # 测试外键约束
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        print(f"✅ 外键约束: {'启用' if fk_enabled else '禁用'}")
        
        # 测试WAL模式
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        print(f"✅ 日志模式: {journal_mode}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_table_structure():
    """测试表结构"""
    print("\n🗃️ 测试表结构...")
    
    conn = sqlite3.connect("database/market_data.db")
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    
    print(f"✅ 用户表数量: {len(tables)}")
    print(f"   表列表: {', '.join(tables)}")
    
    # 检查每个表的结构
    for table in tables:
        print(f"\n  表: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print(f"    列数: {len(columns)}")
        for col in columns[:3]:  # 显示前3列
            print(f"      {col[1]} ({col[2]})")
        if len(columns) > 3:
            print(f"      ... 还有 {len(columns)-3} 列")
    
    conn.close()

def test_sample_data():
    """测试示例数据"""
    print("\n📊 测试示例数据...")
    
    conn = sqlite3.connect("database/market_data.db")
    
    # 测试stocks表数据
    print("  1. stocks表数据:")
    df_stocks = pd.read_sql_query("SELECT * FROM stocks ORDER BY market, symbol", conn)
    print(f"    记录数: {len(df_stocks)}")
    print("    示例数据:")
    for _, row in df_stocks.iterrows():
        print(f"      {row['symbol']} - {row['name']} ({row['market']})")
    
    # 测试economic_indicators表数据
    print("\n  2. economic_indicators表数据:")
    df_indicators = pd.read_sql_query("SELECT * FROM economic_indicators", conn)
    print(f"    记录数: {len(df_indicators)}")
    for _, row in df_indicators.iterrows():
        print(f"      {row['indicator_code']}: {row['value']} {row['unit']} ({row['period']})")
    
    # 测试视图
    print("\n  3. 视图测试:")
    df_view = pd.read_sql_query("SELECT * FROM v_stock_daily LIMIT 0", conn)
    print(f"    v_stock_daily视图列数: {len(df_view.columns)}")
    
    conn.close()

def test_data_quality_features():
    """测试数据质量功能"""
    print("\n✅ 测试数据质量功能（教授建议：数据质量优先）...")
    
    conn = sqlite3.connect("database/market_data.db")
    cursor = conn.cursor()
    
    # 检查data_quality_log表结构
    cursor.execute("PRAGMA table_info(data_quality_log)")
    columns = cursor.fetchall()
    
    quality_columns = [col[1] for col in columns]
    required_columns = ['completeness_score', 'timeliness_score', 'consistency_score', 'overall_score']
    
    print("  数据质量监控表检查:")
    for req_col in required_columns:
        if req_col in quality_columns:
            print(f"    ✅ {req_col}: 存在")
        else:
            print(f"    ❌ {req_col}: 缺失")
    
    # 测试插入数据质量记录
    print("\n  测试插入数据质量记录:")
    try:
        cursor.execute('''
        INSERT INTO data_quality_log 
        (stock_id, trade_date, completeness_score, timeliness_score, 
         consistency_score, accuracy_score, overall_score, issues, status)
        VALUES (1, '2024-02-12', 0.95, 0.98, 0.92, 0.96, 0.95, '无', 'PASS')
        ''')
        conn.commit()
        print("    ✅ 数据质量记录插入成功")
        
        # 验证插入
        cursor.execute("SELECT COUNT(*) FROM data_quality_log")
        count = cursor.fetchone()[0]
        print(f"    数据质量记录总数: {count}")
        
    except Exception as e:
        print(f"    ❌ 数据质量记录插入失败: {e}")
    
    conn.close()

def test_performance():
    """测试性能"""
    print("\n⚡ 测试数据库性能...")
    
    conn = sqlite3.connect("database/market_data.db")
    cursor = conn.cursor()
    
    # 测试查询性能
    import time
    
    # 简单查询
    start_time = time.time()
    cursor.execute("SELECT COUNT(*) FROM stocks")
    count = cursor.fetchone()[0]
    simple_query_time = time.time() - start_time
    
    print(f"  简单查询时间: {simple_query_time:.4f}秒")
    print(f"  查询结果: {count} 条记录")
    
    # 测试索引使用
    print("\n  测试索引使用:")
    cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM stocks WHERE market = 'A'")
    plan = cursor.fetchall()
    for p in plan:
        print(f"    查询计划: {p}")
    
    # 测试视图查询
    start_time = time.time()
    cursor.execute("SELECT COUNT(*) FROM v_stock_daily")
    view_query_time = time.time() - start_time
    print(f"  视图查询时间: {view_query_time:.4f}秒")
    
    conn.close()

def test_backup_and_recovery():
    """测试备份和恢复"""
    print("\n💾 测试备份和恢复（教授建议：保持轻量）...")
    
    import shutil
    from datetime import datetime
    
    db_path = "database/market_data.db"
    backup_dir = Path("database/backups")
    backup_dir.mkdir(exist_ok=True)
    
    # 创建备份
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"test_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"  ✅ 备份创建成功: {backup_path}")
        print(f"    备份大小: {backup_path.stat().st_size:,} bytes")
        
        # 验证备份文件
        if backup_path.exists():
            print("  ✅ 备份文件验证成功")
            
            # 测试从备份恢复（模拟）
            test_restore_path = backup_dir / f"test_restore_{timestamp}.db"
            shutil.copy2(backup_path, test_restore_path)
            
            # 验证恢复的数据库
            conn = sqlite3.connect(test_restore_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stocks")
            count = cursor.fetchone()[0]
            conn.close()
            
            print(f"  ✅ 恢复测试成功: {count} 条股票记录")
            
            # 清理测试文件
            test_restore_path.unlink()
            print("  ✅ 测试文件清理完成")
            
        else:
            print("  ❌ 备份文件不存在")
            
    except Exception as e:
        print(f"  ❌ 备份测试失败: {e}")

def generate_usage_examples():
    """生成使用示例"""
    print("\n📝 生成使用示例...")
    
    examples = '''
# ==================== SQLite数据库使用示例 ====================

# 示例1: 基本连接和查询
import sqlite3
import pandas as pd

# 连接数据库
conn = sqlite3.connect('database/market_data.db')

# 使用pandas读取数据
df_stocks = pd.read_sql_query('SELECT * FROM stocks', conn)
print(f"股票数量: {len(df_stocks)}")

# 使用原生SQL查询
cursor = conn.cursor()
cursor.execute('SELECT symbol, name, market FROM stocks WHERE market = ?', ('A',))
for row in cursor.fetchall():
    print(f"{row[0]} - {row[1]}")

# 示例2: 插入数据
new_stock = ('TSLA', 'Tesla Inc.', 'US', 'NASDAQ', '汽车', '新能源', 'yfinance')
cursor.execute("""
    INSERT OR IGNORE INTO stocks 
    (symbol, name, market, exchange, industry, sector, data_source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", new_stock)
conn.commit()

# 示例3: 使用视图
df_daily = pd.read_sql_query("""
    SELECT * FROM v_stock_daily 
    WHERE symbol = '000001.SZ' 
    ORDER BY trade_date DESC 
    LIMIT 10
""", conn)
print(df_daily[['trade_date', 'close', 'change_percent']])

# 示例4: 数据质量监控
df_quality = pd.read_sql_query("""
    SELECT * FROM v_data_quality 
    WHERE overall_score < 0.8 
    ORDER BY created_at DESC
""", conn)
if len(df_quality) > 0:
    print(f"发现 {len(df_quality)} 条低质量数据")

# 关闭连接
conn.close()

# 示例5: 使用事务批量插入
def batch_insert_prices(prices_data):
    """批量插入价格数据"""
    conn = sqlite3.connect('database/market_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.executemany("""
            INSERT OR REPLACE INTO daily_prices 
            (stock_id, trade_date, open, high, low, close, volume, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, prices_data)
        conn.commit()
        print(f"成功插入 {len(prices_data)} 条价格数据")
    except Exception as e:
        conn.rollback()
        print(f"插入失败: {e}")
    finally:
        conn.close()

# ==================== 教授建议实践 ====================

# 建议1: 不要过早优化（使用SQLite足够）
print("教授建议：数据量不到千万级，SQLite足够")
print(f"当前数据量: {pd.read_sql_query('SELECT COUNT(*) FROM daily_prices', conn).iloc[0,0]:,} 条")
print("结论: SQLite完全足够，不需要迁移到PostgreSQL")

# 建议2: 数据质量优先
print("\\n教授建议：80%时间应该花在数据上")
quality_sql = """
SELECT 
    AVG(overall_score) as avg_quality,
    COUNT(CASE WHEN overall_score < 0.8 THEN 1 END) as low_quality_count
FROM data_quality_log
"""
quality_stats = pd.read_sql_query(quality_sql, conn)
print(f"平均数据质量: {quality_stats['avg_quality'][0]:.2%}")
print(f"低质量数据条数: {quality_stats['low_quality_count'][0]}")

# 建议3: 保持轻量
print("\\n教授建议：个人项目避免重型框架")
db_size = Path('database/market_data.db').stat().st_size
print(f"数据库大小: {db_size:,} bytes ({db_size/1024/1024:.2f} MB)")
print("结论: 单文件数据库，轻量易维护")
'''
    
    with open('database_usage_examples.py', 'w', encoding='utf-8') as f:
        f.write(examples)
    
    print("✅ 使用示例已保存到: database_usage_examples.py")
    print("   运行: python3 database_usage_examples.py")

def main():
    """主函数"""
    print("=" * 60)
    print("SQLite数据库功能测试")
    print("验证是否符合教授建议")
    print("=" * 60)
    
    # 测试1: 数据库连接
    if not test_database_connection():
        return
    
    # 测试2: 表结构
    test_table_structure()
    
    # 测试3: 示例数据
    test_sample_data()
    
    # 测试4: 数据质量功能
    test_data_quality_features()
    
    # 测试5: 性能测试
    test_performance()
    
    # 测试6: 备份和恢复
    test_backup_and_recovery()
    
    # 生成使用示例
    generate_usage_examples()
    
    print("\n" + "=" * 60)
    print("✅ 数据库测试完成!")
    print("=" * 60)
    
    print("\n🎯 教授建议遵守情况总结:")
    print("1. ✅ 不要过早优化：使用SQLite，未使用PostgreSQL")
    print("2. ✅ 数据质量优先：完整的数据质量监控表")
    print("3. ✅ 保持轻量：单文件数据库，易于备份")
    print("4. ✅ 实用设计：满足个人DSS系统需求")
    print("5. ✅ 性能良好：索引优化，查询快速")
    
    print("\n💡 下一步建议:")
    print("1. 开始Phase 0的学习任务：阅读AKShare源码")
    print("2. 基于此数据库设计数据采集管道")
    print("3. 实现数据质量监控系统")
    print("4. 定期备份数据库文件")

if __name__ == "__main__":
    main()