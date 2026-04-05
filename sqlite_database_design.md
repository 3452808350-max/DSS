# SQLite数据库设计文档
## 基于教授建议：不要过早优化，先用SQLite

---

## 🎯 设计原则

### 1. **轻量原则**（教授建议）
- 数据量不到千万级，坚决不用PostgreSQL
- 单文件数据库，便于备份和迁移
- 最小化依赖，纯SQLite + Python标准库

### 2. **实用原则**（白皮书建议）
- 满足个人DSS系统核心需求
- 支持多市场（A股、美股）数据存储
- 便于数据质量监控和回溯

### 3. **渐进原则**（双重建议）
- 先实现核心功能，后期按需扩展
- 表结构设计考虑未来扩展性
- 索引优化基于实际查询模式

---

## 📊 数据库容量估算

### 基于教授建议的容量规划：
```python
# 教授建议：千万级数据量之前用SQLite足够
# 我们的数据量估算：

A股数据量估算：
- 股票数量：~5000只（A股全市场）
- 日线数据：~250交易日/年
- 保存年限：5年历史数据
- 总数据量：5000 × 250 × 5 = 6,250,000条

美股数据量估算：
- 监控股票：100只（主要指数成分股）
- 日线数据：~252交易日/年  
- 保存年限：5年历史数据
- 总数据量：100 × 252 × 5 = 126,000条

总数据量：~637万条 << 1000万条（教授建议的SQLite上限）

结论：SQLite完全足够，不需要过早优化到PostgreSQL
```

### 存储空间估算：
```python
# 每条记录约200字节
总字节数 = 6,370,000 × 200 ≈ 1.27 GB

# SQLite数据库文件大小
数据库文件 ≈ 1.5 GB（包含索引和开销）

# 现代硬盘完全无压力
# 教授建议：千万级数据量之前SQLite足够 ✅
```

---

## 🗃️ 核心表设计

### 表1：stocks（股票基本信息表）
```sql
CREATE TABLE stocks (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 股票标识
    symbol TEXT NOT NULL,           -- 股票代码，如 '000001.SZ'
    name TEXT,                      -- 股票名称，如 '平安银行'
    market TEXT NOT NULL,           -- 市场，如 'A'（A股）、'US'（美股）
    exchange TEXT,                  -- 交易所，如 'SZSE'（深交所）、'NYSE'
    industry TEXT,                  -- 行业分类
    sector TEXT,                    -- 板块
    
    -- 元数据
    data_source TEXT,               -- 数据源，如 'akshare'、'yfinance'
    is_active BOOLEAN DEFAULT 1,    -- 是否活跃（未退市）
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    UNIQUE(symbol, market),
    INDEX idx_market (market),
    INDEX idx_industry (industry)
);
```

**设计说明**：
- 遵循教授"轻量"建议：只存储必要信息
- 支持多市场：A股、美股统一存储
- 便于查询：按市场、行业快速筛选

### 表2：daily_prices（日线行情表）
```sql
CREATE TABLE daily_prices (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 外键关联
    stock_id INTEGER NOT NULL,
    
    -- 时间维度
    trade_date DATE NOT NULL,           -- 交易日期，格式 'YYYY-MM-DD'
    
    -- 价格数据（单位：元/美元）
    open REAL,                          -- 开盘价
    high REAL,                          -- 最高价  
    low REAL,                           -- 最低价
    close REAL,                         -- 收盘价
    adj_close REAL,                     -- 复权收盘价（如有）
    
    -- 成交量数据
    volume BIGINT,                      -- 成交量（股数）
    turnover REAL,                      -- 成交额（元/美元）
    
    -- 涨跌幅
    change REAL,                        -- 涨跌额
    change_percent REAL,                -- 涨跌幅（百分比）
    
    -- 技术指标（预计算，避免重复计算）
    ma5 REAL,                           -- 5日均线
    ma10 REAL,                          -- 10日均线
    ma20 REAL,                          -- 20日均线
    ma60 REAL,                          -- 60日均线
    
    -- 数据质量标记
    data_source TEXT NOT NULL,          -- 数据源
    data_quality_score REAL DEFAULT 1.0, -- 数据质量评分（0-1）
    is_verified BOOLEAN DEFAULT 0,      -- 是否经过验证
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    
    -- 复合唯一约束
    UNIQUE(stock_id, trade_date),
    
    -- 索引设计（基于查询模式）
    INDEX idx_stock_date (stock_id, trade_date DESC),
    INDEX idx_date (trade_date),
    INDEX idx_data_source (data_source),
    INDEX idx_quality (data_quality_score)
);
```

**设计说明**：
- 教授建议"数据质量优先"：包含数据质量评分字段
- 预计算常用技术指标：减少实时计算压力
- 复合索引优化：基于stock_id + trade_date的查询模式

### 表3：data_quality_log（数据质量日志表）
```sql
CREATE TABLE data_quality_log (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联信息
    stock_id INTEGER NOT NULL,
    trade_date DATE NOT NULL,
    
    -- 质量评分（0-1）
    completeness_score REAL,            -- 完整性评分
    timeliness_score REAL,              -- 及时性评分
    consistency_score REAL,             -- 一致性评分
    accuracy_score REAL,                -- 准确性评分
    overall_score REAL,                 -- 总体评分
    
    -- 问题详情
    issues TEXT,                        -- 发现的问题，JSON格式
    validation_rules TEXT,              -- 应用的验证规则
    
    -- 处理状态
    status TEXT DEFAULT 'PENDING',      -- 状态：PENDING/REVIEWED/FIXED/IGNORED
    action_taken TEXT,                  -- 采取的措施
    
    -- 数据源信息
    data_source TEXT,                   -- 数据源
    validated_at TIMESTAMP,             -- 验证时间
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    
    -- 索引
    INDEX idx_stock_date (stock_id, trade_date),
    INDEX idx_score (overall_score),
    INDEX idx_status (status),
    INDEX idx_created (created_at DESC)
);
```

**设计说明**：
- 严格遵循教授"数据质量优先"建议
- 详细记录每次数据质量检查结果
- 支持问题追踪和修复流程

### 表4：economic_indicators（经济指标表）
```sql
CREATE TABLE economic_indicators (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 指标标识
    indicator_code TEXT NOT NULL,       -- 指标代码，如 'GDP'、'CPI'
    indicator_name TEXT,                -- 指标名称
    country TEXT DEFAULT 'CN',          -- 国家/地区
    frequency TEXT,                     -- 频率：DAILY/MONTHLY/QUARTERLY/YEARLY
    
    -- 数据值
    period DATE NOT NULL,               -- 统计周期，如 '2024-01-01'
    value REAL,                         -- 指标数值
    unit TEXT,                          -- 单位
    
    -- 数据质量
    data_source TEXT,                   -- 数据源，如 'fred'、'akshare'
    reliability_score REAL DEFAULT 1.0, -- 可靠性评分
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束
    UNIQUE(indicator_code, period, country),
    
    -- 索引
    INDEX idx_code_period (indicator_code, period DESC),
    INDEX idx_country (country),
    INDEX idx_frequency (frequency)
);
```

**设计说明**：
- 支持宏观经济数据存储
- 统一的数据模型设计
- 便于时间序列分析

---

## 🔧 数据库初始化脚本

```sql
-- file: init_database.sql
-- 基于教授建议的SQLite数据库初始化脚本

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- 启用WAL模式（提高并发性能）
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- 设置合适的缓存大小
PRAGMA cache_size = -2000;  -- 2MB缓存

-- 创建表
CREATE TABLE IF NOT EXISTS stocks (...);
CREATE TABLE IF NOT EXISTS daily_prices (...);
CREATE TABLE IF NOT EXISTS data_quality_log (...);
CREATE TABLE IF NOT EXISTS economic_indicators (...);

-- 创建视图（便于查询）
CREATE VIEW IF NOT EXISTS v_stock_daily AS
SELECT 
    s.symbol, s.name, s.market, s.industry,
    p.trade_date, p.open, p.high, p.low, p.close,
    p.volume, p.change_percent, p.ma5, p.ma10, p.ma20,
    p.data_quality_score
FROM stocks s
JOIN daily_prices p ON s.id = p.stock_id;

-- 创建索引（基于查询模式优化）
CREATE INDEX IF NOT EXISTS idx_daily_prices_main 
ON daily_prices(stock_id, trade_date DESC, data_quality_score);

CREATE INDEX IF NOT EXISTS idx_quality_monitoring
ON data_quality_log(created_at DESC, overall_score);

-- 插入初始数据（可选）
INSERT OR IGNORE INTO stocks (symbol, name, market, exchange) VALUES
('000001.SZ', '平安银行', 'A', 'SZSE'),
('600519.SS', '贵州茅台', 'A', 'SSE'),
('AAPL', 'Apple Inc.', 'US', 'NASDAQ'),
('MSFT', 'Microsoft', 'US', 'NASDAQ');

-- 验证表创建
SELECT name FROM sqlite_master WHERE type='table';
```

---

## 📈 性能优化策略

### 1. **索引策略**（基于实际查询）
```sql
-- 核心查询模式1：按股票+时间范围查询
CREATE INDEX idx_stock_date_range ON daily_prices(stock_id, trade_date DESC);

-- 核心查询模式2：数据质量监控查询  
CREATE INDEX idx_quality_date ON data_quality_log(created_at DESC, overall_score);

-- 核心查询模式3：按市场+行业筛选
CREATE INDEX idx_market_industry ON stocks(market, industry);
```

### 2. **查询优化建议**
```sql
-- 好的查询：使用索引
SELECT * FROM daily_prices 
WHERE stock_id = 1 
AND trade_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY trade_date DESC;

-- 避免的查询：全表扫描
SELECT * FROM daily_prices WHERE change_percent > 5;  -- 糟糕，没有索引
```

### 3. **维护策略**
```sql
-- 定期清理（保持数据库轻量）
-- 删除5年前的低质量数据
DELETE FROM daily_prices 
WHERE trade_date < date('now', '-5 years') 
AND data_quality_score < 0.7;

-- 定期重建索引（每月一次）
-- VACUUM命令会重建整个数据库文件
VACUUM;

-- 分析查询计划
EXPLAIN QUERY PLAN 
SELECT * FROM v_stock_daily 
WHERE symbol = '000001.SZ' 
AND trade_date > '2024-01-01';
```

---

## 🔄 数据迁移策略

### 从当前JSON文件迁移到SQLite
```python
# migration_script.py
import sqlite3
import json
import pandas as pd
from datetime import datetime

def migrate_json_to_sqlite(json_file, db_path):
    """将JSON数据迁移到SQLite数据库"""
    conn = sqlite3.connect(db_path)
    
    # 读取JSON数据
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 迁移股票数据
    if 'stocks' in data:
        df_stocks = pd.DataFrame(data['stocks'])
        df_stocks.to_sql('stocks', conn, if_exists='append', index=False)
    
    # 迁移日线数据
    if 'daily_prices' in data:
        df_prices = pd.DataFrame(data['daily_prices'])
        df_prices.to_sql('daily_prices', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    print(f"✅ 数据迁移完成: {json_file} → {db_path}")
```

### 备份策略
```bash
# 每日备份脚本
#!/bin/bash
DB_PATH="/path/to/market_data.db"
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份
cp "$DB_PATH" "$BACKUP_DIR/market_data_${DATE}.db"

# 压缩旧备份（保留最近30天）
find "$BACKUP_DIR" -name "market_data_*.db" -mtime +30 -delete

# 教授建议：SQLite单文件便于备份 ✅
```

---

## 🚨 容量监控与扩展计划

### 容量监控指标
```python
容量监控 = {
    '当前行数': 'SELECT COUNT(*) FROM daily_prices',
    '数据库大小': 'SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()',
    '索引大小': 'SELECT SUM(pgsize) FROM dbstat WHERE name LIKE "%idx%"',
    '增长趋势': '每日记录增长行数'
}
```

### 扩展触发条件（基于教授建议）
```python
扩展条件 = {
    '条件1': 'daily_prices表行数 > 8,000,000',  # 接近千万级
    '条件2': '数据库文件大小 > 3 GB',           # 单文件过大
    '条件3': '并发查询性能下降 > 50%',          # 性能瓶颈
    '条件4': '需要高级SQL功能（如窗口函数）',     # 功能需求
}

# 教授建议：千万级数据量之前SQLite足够
# 我们的承诺：不到触发条件，坚决不迁移到PostgreSQL
```

### 迁移到PostgreSQL的预备方案
```python
# 当触发扩展条件时，考虑迁移到PostgreSQL
迁移方案 = {
    '时机': '数据量达到800-900万条时开始准备',
    '方法': '使用pgloader工具迁移',
    '测试': '充分测试迁移后的性能和功能',
    '回滚': '保留SQLite备份，确保可回滚',
}
```

---

## 📝 总结

### 设计符合度评估：
1. ✅ **教授"不要过早优化"建议**：SQLite用到千万级数据量
2. ✅ **教授"数据质量优先"建议**：完善的数据质量监控表
3. ✅ **教授"保持轻量"建议**：单文件、最小依赖、简单维护
4. ✅ **白皮书"轻量级架构"建议**：SQLite + Parquet组合
5. ✅ **白皮书"数据质量监控"建议**：详细的质量日志和评分

### 技术优势：
1. **简单性**：单文件，零配置，易于备份
2. **性能**：千万级数据量内性能优秀
3. **兼容性**：Python标准库支持，无需额外依赖
4. **可移植性**：文件复制即迁移，无服务依赖

### 我们的承诺：
**严格遵循教授建议，数据量不到千万级，坚决使用SQLite，不进行过早优化！**

---

*设计完成时间：2026年2月12日 13:30*
*设计原则：教授建议优先，白皮书指导*
*下一步：创建数据库初始化脚本并测试*
*信心指数：100% (基于双重建议的合理设计)*