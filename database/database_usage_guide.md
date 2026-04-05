
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
