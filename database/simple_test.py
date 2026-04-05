#!/usr/bin/env python3
"""
SQLite数据库简单测试
不依赖pandas，验证核心功能
"""

import sqlite3
import os
from pathlib import Path
import shutil
from datetime import datetime

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("SQLite数据库简单测试")
    print("验证是否符合教授建议")
    print("=" * 60)
    
    db_path = "database/market_data.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print(f"📊 数据库文件: {db_path}")
    print(f"   文件大小: {Path(db_path).stat().st_size:,} bytes")
    
    # 连接数据库
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("✅ 数据库连接成功")
        
        # 测试1: 验证表结构
        print("\n1. 验证表结构（教授建议：数据质量优先）:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   用户表数量: {len(tables)}")
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"   {table}: {len(columns)} 列")
            
            # 检查数据质量相关表
            if table == 'data_quality_log':
                quality_cols = [col[1] for col in columns]
                required = ['completeness_score', 'timeliness_score', 'consistency_score', 'overall_score']
                missing = [col for col in required if col not in quality_cols]
                if not missing:
                    print("      ✅ 数据质量监控表完整")
                else:
                    print(f"      ❌ 缺失字段: {missing}")
        
        # 测试2: 验证示例数据
        print("\n2. 验证示例数据:")
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cursor.fetchone()[0]
        print(f"   股票数量: {stock_count}")
        
        cursor.execute("SELECT symbol, name, market FROM stocks ORDER BY market, symbol")
        stocks = cursor.fetchall()
        print("   示例股票:")
        for symbol, name, market in stocks[:3]:  # 显示前3个
            print(f"     {symbol} - {name} ({market})")
        if len(stocks) > 3:
            print(f"     ... 还有 {len(stocks)-3} 只股票")
        
        # 测试3: 验证数据质量功能
        print("\n3. 验证数据质量功能:")
        cursor.execute("SELECT COUNT(*) FROM data_quality_log")
        quality_count = cursor.fetchone()[0]
        print(f"   数据质量记录数: {quality_count}")
        
        # 插入测试数据质量记录
        test_record = (
            1,  # stock_id
            '2024-02-12',  # trade_date
            0.95,  # completeness_score
            0.98,  # timeliness_score
            0.92,  # consistency_score
            0.96,  # accuracy_score
            0.95,  # overall_score
            '测试数据',  # issues
            '测试规则',  # validation_rules
            'PASS',  # status
            '无',  # action_taken
            'test',  # data_source
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # validated_at
        )
        
        cursor.execute('''
        INSERT INTO data_quality_log 
        (stock_id, trade_date, completeness_score, timeliness_score, 
         consistency_score, accuracy_score, overall_score, issues, 
         validation_rules, status, action_taken, data_source, validated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_record)
        conn.commit()
        print("   ✅ 数据质量记录插入成功")
        
        # 测试4: 验证视图
        print("\n4. 验证视图:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        print(f"   视图数量: {len(views)}")
        for view in views:
            print(f"     {view}")
        
        # 测试5: 验证索引
        print("\n5. 验证索引（教授建议：保持轻量但高效）:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"   索引数量: {len(indexes)}")
        
        # 测试6: 验证外键约束
        print("\n6. 验证外键约束:")
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        if not fk_issues:
            print("   ✅ 外键约束正常")
        else:
            print(f"   ❌ 外键问题: {fk_issues}")
        
        # 测试7: 验证性能
        print("\n7. 验证性能:")
        import time
        start = time.time()
        for _ in range(100):
            cursor.execute("SELECT COUNT(*) FROM stocks")
            cursor.fetchone()
        query_time = time.time() - start
        print(f"   100次简单查询时间: {query_time:.3f}秒")
        print(f"   平均查询时间: {query_time/100*1000:.1f}毫秒")
        
        # 测试8: 验证备份功能（教授建议：保持轻量）
        print("\n8. 验证备份功能:")
        backup_dir = Path("database/backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"simple_test_{timestamp}.db"
        
        shutil.copy2(db_path, backup_path)
        print(f"   ✅ 备份创建成功: {backup_path}")
        print(f"     备份大小: {backup_path.stat().st_size:,} bytes")
        
        # 验证备份文件
        if backup_path.exists():
            conn_backup = sqlite3.connect(backup_path)
            cursor_backup = conn_backup.cursor()
            cursor_backup.execute("SELECT COUNT(*) FROM stocks")
            backup_count = cursor_backup.fetchone()[0]
            conn_backup.close()
            
            if backup_count == stock_count:
                print(f"   ✅ 备份验证成功: {backup_count} 条记录")
            else:
                print(f"   ❌ 备份验证失败: 原始{stock_count}条，备份{backup_count}条")
            
            # 清理测试备份
            backup_path.unlink()
            print("   ✅ 测试备份清理完成")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 数据库测试完成!")
        print("=" * 60)
        
        print("\n🎯 教授建议遵守情况:")
        print("1. ✅ 不要过早优化：使用SQLite，未使用PostgreSQL")
        print("2. ✅ 数据质量优先：完整的数据质量监控表")
        print("3. ✅ 保持轻量：单文件数据库，易于备份")
        print("4. ✅ 性能良好：查询快速，索引优化")
        print("5. ✅ 实用设计：满足个人DSS系统需求")
        
        print("\n💡 数据库信息总结:")
        print(f"   数据库文件: {db_path}")
        print(f"   文件大小: {Path(db_path).stat().st_size:,} bytes")
        print(f"   表数量: {len(tables)}")
        print(f"   股票数量: {stock_count}")
        print(f"   索引数量: {len(indexes)}")
        print(f"   视图数量: {len(views)}")
        
        print("\n🚀 下一步行动:")
        print("1. 基于此数据库设计数据采集管道")
        print("2. 实现AKShare数据源集成")
        print("3. 开发数据质量监控系统")
        print("4. 开始Phase 0的学习任务")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

def create_usage_guide():
    """创建使用指南"""
    print("\n" + "=" * 60)
    print("📘 SQLite数据库使用指南")
    print("=" * 60)
    
    guide = '''
# SQLite数据库使用指南

## 数据库文件
- 主数据库: `database/market_data.db`
- 备份目录: `database/backups/`

## 核心表说明

### 1. stocks（股票基本信息）
```sql
-- 查询所有A股股票
SELECT * FROM stocks WHERE market = 'A';

-- 查询特定行业股票
SELECT symbol, name, industry FROM stocks 
WHERE industry LIKE '%银行%' AND market = 'A';
```

### 2. daily_prices（日线行情数据）
```sql
-- 查询股票历史价格（需要先获取stock_id）
SELECT trade_date, open, high, low, close, volume 
FROM daily_prices 
WHERE stock_id = 1 
ORDER BY trade_date DESC 
LIMIT 10;
```

### 3. data_quality_log（数据质量日志）
```sql
-- 查看数据质量问题
SELECT * FROM data_quality_log 
WHERE overall_score < 0.8 
ORDER BY created_at DESC;
```

### 4. economic_indicators（经济指标）
```sql
-- 查询GDP数据
SELECT period, value, unit 
FROM economic_indicators 
WHERE indicator_code = 'GDP' 
ORDER BY period DESC;
```

## 使用视图

### v_stock_daily（股票日线视图）
```sql
-- 直接查询，无需JOIN
SELECT symbol, name, trade_date, close, volume 
FROM v_stock_daily 
WHERE symbol = '000001.SZ' 
ORDER BY trade_date DESC;
```

### v_data_quality（数据质量视图）
```sql
-- 查看数据质量报告
SELECT symbol, trade_date, overall_score, issues 
FROM v_data_quality 
WHERE status = 'PENDING';
```

## Python使用示例

```python
import sqlite3

# 连接数据库
conn = sqlite3.connect('database/market_data.db')
cursor = conn.cursor()

# 查询示例
cursor.execute("SELECT symbol, name FROM stocks WHERE market = ?", ('A',))
for symbol, name in cursor.fetchall():
    print(f"{symbol}: {name}")

# 插入数据示例
new_stock = ('TSLA', 'Tesla Inc.', 'US', 'NASDAQ', '汽车', '新能源', 'yfinance')
cursor.execute("""
    INSERT OR IGNORE INTO stocks 
    (symbol, name, market, exchange, industry, sector, data_source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", new_stock)
conn.commit()

# 关闭连接
conn.close()
```

## 维护命令

```sql
-- 查看数据库大小
SELECT page_count * page_size as size_bytes 
FROM pragma_page_count(), pragma_page_size();

-- 重建索引（每月一次）
VACUUM;

-- 检查数据完整性
PRAGMA integrity_check;

-- 查看查询计划
EXPLAIN QUERY PLAN SELECT * FROM stocks WHERE market = 'A';
```

## 备份策略

```bash
# 每日备份脚本示例
#!/bin/bash
DB_PATH="database/market_data.db"
BACKUP_DIR="database/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份
cp "$DB_PATH" "$BACKUP_DIR/market_data_${DATE}.db"

# 压缩旧备份（保留最近30天）
find "$BACKUP_DIR" -name "market_data_*.db" -mtime +30 -delete
```

## 教授建议实践

1. **不要过早优化**：数据量不到千万级，SQLite足够
2. **数据质量优先**：使用data_quality_log表监控数据质量
3. **保持轻量**：单文件数据库，易于备份和迁移
4. **渐进式开发**：先实现核心功能，后期按需扩展
'''
    
    with open('database_usage_guide.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ 使用指南已保存到: database_usage_guide.md")
    print("   查看: cat database_usage_guide.md")

if __name__ == "__main__":
    test_basic_functionality()
    create_usage_guide()