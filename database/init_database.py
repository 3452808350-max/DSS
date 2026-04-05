#!/usr/bin/env python3
"""
SQLite数据库初始化脚本
基于教授建议：不要过早优化，先用SQLite
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, db_path: str = "market_data.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        self.db_dir = Path(db_path).parent
        self.db_dir.mkdir(exist_ok=True)
        
        print(f"📊 初始化SQLite数据库: {db_path}")
        print(f"   数据库目录: {self.db_dir.absolute()}")
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 启用数据库优化设置
            self._enable_optimizations(cursor)
            
            # 创建表
            self._create_tables(cursor)
            
            # 创建视图
            self._create_views(cursor)
            
            # 创建索引
            self._create_indexes(cursor)
            
            # 插入示例数据
            self._insert_sample_data(cursor)
            
            conn.commit()
            
            # 验证数据库
            self._verify_database(cursor)
            
            print(f"✅ 数据库初始化完成: {self.db_path}")
            print(f"   数据库大小: {self._get_db_size()} bytes")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 数据库初始化失败: {e}")
            raise
        finally:
            conn.close()
    
    def _enable_optimizations(self, cursor):
        """启用数据库优化设置"""
        print("  启用数据库优化设置...")
        
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 启用WAL模式（提高并发性能）
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        
        # 设置合适的缓存大小
        cursor.execute("PRAGMA cache_size = -2000")  # 2MB缓存
        
        # 设置临时存储位置
        cursor.execute("PRAGMA temp_store = MEMORY")
        
        print("  数据库优化设置完成")
    
    def _create_tables(self, cursor):
        """创建数据库表"""
        print("  创建数据库表...")
        
        # 1. stocks表（股票基本信息）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT,
            market TEXT NOT NULL,
            exchange TEXT,
            industry TEXT,
            sector TEXT,
            data_source TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, market)
        )
        ''')
        print("    ✅ stocks表创建完成")
        
        # 2. daily_prices表（日线行情数据）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id INTEGER NOT NULL,
            trade_date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume BIGINT,
            turnover REAL,
            change REAL,
            change_percent REAL,
            ma5 REAL,
            ma10 REAL,
            ma20 REAL,
            ma60 REAL,
            data_source TEXT NOT NULL,
            data_quality_score REAL DEFAULT 1.0,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks(id),
            UNIQUE(stock_id, trade_date)
        )
        ''')
        print("    ✅ daily_prices表创建完成")
        
        # 3. data_quality_log表（数据质量日志）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_quality_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id INTEGER NOT NULL,
            trade_date DATE NOT NULL,
            completeness_score REAL,
            timeliness_score REAL,
            consistency_score REAL,
            accuracy_score REAL,
            overall_score REAL,
            issues TEXT,
            validation_rules TEXT,
            status TEXT DEFAULT 'PENDING',
            action_taken TEXT,
            data_source TEXT,
            validated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks(id)
        )
        ''')
        print("    ✅ data_quality_log表创建完成")
        
        # 4. economic_indicators表（经济指标）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS economic_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_code TEXT NOT NULL,
            indicator_name TEXT,
            country TEXT DEFAULT 'CN',
            frequency TEXT,
            period DATE NOT NULL,
            value REAL,
            unit TEXT,
            data_source TEXT,
            reliability_score REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, period, country)
        )
        ''')
        print("    ✅ economic_indicators表创建完成")
        
        print("  所有表创建完成")
    
    def _create_views(self, cursor):
        """创建视图"""
        print("  创建视图...")
        
        # 股票日线数据视图（便于查询）
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS v_stock_daily AS
        SELECT 
            s.id as stock_id,
            s.symbol,
            s.name,
            s.market,
            s.industry,
            p.trade_date,
            p.open,
            p.high,
            p.low,
            p.close,
            p.adj_close,
            p.volume,
            p.turnover,
            p.change,
            p.change_percent,
            p.ma5,
            p.ma10,
            p.ma20,
            p.ma60,
            p.data_source,
            p.data_quality_score,
            p.is_verified
        FROM stocks s
        JOIN daily_prices p ON s.id = p.stock_id
        ''')
        print("    ✅ v_stock_daily视图创建完成")
        
        # 数据质量监控视图
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS v_data_quality AS
        SELECT 
            s.symbol,
            s.name,
            q.trade_date,
            q.completeness_score,
            q.timeliness_score,
            q.consistency_score,
            q.accuracy_score,
            q.overall_score,
            q.issues,
            q.status,
            q.validated_at,
            q.created_at
        FROM data_quality_log q
        JOIN stocks s ON q.stock_id = s.id
        ''')
        print("    ✅ v_data_quality视图创建完成")
        
        print("  所有视图创建完成")
    
    def _create_indexes(self, cursor):
        """创建索引"""
        print("  创建索引...")
        
        # stocks表索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stocks_industry ON stocks(industry)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol)')
        print("    ✅ stocks表索引创建完成")
        
        # daily_prices表索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_daily_prices_main 
        ON daily_prices(stock_id, trade_date DESC)
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_prices_date ON daily_prices(trade_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_prices_quality ON daily_prices(data_quality_score)')
        print("    ✅ daily_prices表索引创建完成")
        
        # data_quality_log表索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_quality_log_main 
        ON data_quality_log(stock_id, trade_date)
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_log_score ON data_quality_log(overall_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_log_status ON data_quality_log(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_log_created ON data_quality_log(created_at DESC)')
        print("    ✅ data_quality_log表索引创建完成")
        
        # economic_indicators表索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_economic_main 
        ON economic_indicators(indicator_code, period DESC)
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_economic_country ON economic_indicators(country)')
        print("    ✅ economic_indicators表索引创建完成")
        
        print("  所有索引创建完成")
    
    def _insert_sample_data(self, cursor):
        """插入示例数据"""
        print("  插入示例数据...")
        
        # 插入示例股票数据
        sample_stocks = [
            ('000001.SZ', '平安银行', 'A', 'SZSE', '银行', '金融', 'akshare'),
            ('600519.SS', '贵州茅台', 'A', 'SSE', '白酒', '消费', 'akshare'),
            ('601318.SS', '中国平安', 'A', 'SSE', '保险', '金融', 'akshare'),
            ('AAPL', 'Apple Inc.', 'US', 'NASDAQ', '科技', '信息技术', 'yfinance'),
            ('MSFT', 'Microsoft', 'US', 'NASDAQ', '科技', '信息技术', 'yfinance'),
            ('GOOGL', 'Alphabet', 'US', 'NASDAQ', '科技', '信息技术', 'yfinance'),
        ]
        
        for stock in sample_stocks:
            cursor.execute('''
            INSERT OR IGNORE INTO stocks 
            (symbol, name, market, exchange, industry, sector, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', stock)
        
        print(f"    ✅ 插入 {len(sample_stocks)} 只示例股票")
        
        # 插入示例经济指标
        sample_indicators = [
            ('GDP', '国内生产总值', 'CN', 'QUARTERLY', '2024-12-31', 1270000.0, '亿元', 'akshare'),
            ('CPI', '消费者价格指数', 'CN', 'MONTHLY', '2024-12-01', 102.5, '指数', 'akshare'),
            ('UNRATE', '失业率', 'CN', 'MONTHLY', '2024-12-01', 5.2, '%', 'akshare'),
        ]
        
        for indicator in sample_indicators:
            cursor.execute('''
            INSERT OR IGNORE INTO economic_indicators
            (indicator_code, indicator_name, country, frequency, period, value, unit, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', indicator)
        
        print(f"    ✅ 插入 {len(sample_indicators)} 个经济指标")
        
        print("  示例数据插入完成")
    
    def _verify_database(self, cursor):
        """验证数据库"""
        print("  验证数据库...")
        
        # 检查表数量
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   表数量: {len(tables)}")
        
        # 检查视图数量
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        print(f"   视图数量: {len(views)}")
        
        # 检查索引数量
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        print(f"   索引数量: {len(indexes)}")
        
        # 检查示例数据
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cursor.fetchone()[0]
        print(f"   股票数量: {stock_count}")
        
        cursor.execute("SELECT COUNT(*) FROM economic_indicators")
        indicator_count = cursor.fetchone()[0]
        print(f"   经济指标数量: {indicator_count}")
        
        # 检查外键约束
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        if not fk_issues:
            print("   外键约束: ✅ 正常")
        else:
            print(f"   外键约束: ❌ 问题: {fk_issues}")
        
        print("  数据库验证完成")
    
    def _get_db_size(self):
        """获取数据库文件大小"""
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path)
        return 0
    
    def backup_database(self, backup_dir: str = "backups"):
        """备份数据库"""
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"market_data_{timestamp}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_file)
        
        print(f"💾 数据库备份完成: {backup_file}")
        return str(backup_file)
    
    def get_database_info(self):
        """获取数据库信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        info = {
            'path': self.db_path,
            'size': self._get_db_size(),
            'tables': [],
            'row_counts': {}
        }
        
        # 获取表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        info['tables'] = tables
        
        # 获取每个表的行数
        for table in tables:
            if table.startswith('sqlite_'):  # 跳过系统表
                continue
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                info['row_counts'][table] = count
            except:
                info['row_counts'][table] = 'N/A'
        
        conn.close()
        return info


def main():
    """主函数"""
    print("=" * 60)
    print("SQLite数据库初始化工具")
    print("基于教授建议：不要过早优化，先用SQLite")
    print("=" * 60)
    
    # 初始化数据库
    initializer = DatabaseInitializer("database/market_data.db")
    
    print("\n🚀 开始初始化数据库...")
    initializer.init_database()
    
    # 获取数据库信息
    print("\n📊 数据库信息:")
    info = initializer.get_database_info()
    print(f"   数据库路径: {info['path']}")
    print(f"   数据库大小: {info['size']:,} bytes")
    print(f"   表列表: {', '.join(info['tables'])}")
    
    print("\n📈 数据统计:")
    for table, count in info['row_counts'].items():
        print(f"   {table}: {count} 行")
    
    # 创建备份
    print("\n💾 创建数据库备份...")
    backup_file = initializer.backup_database()
    print(f"   备份文件: {backup_file}")
    
    print("\n" + "=" * 60)
    print("✅ SQLite数据库初始化完成!")
    print("=" * 60)
    
    print("\n💡 使用说明:")
    print("1. 数据库文件: database/market_data.db")
    print("2. 备份目录: database/backups/")
    print("3. 使用SQLite浏览器查看: https://sqlitebrowser.org/")
    print("4. Python连接示例:")
    print("   import sqlite3")
    print("   conn = sqlite3.connect('database/market_data.db')")
    print("   cursor = conn.cursor()")
    print("   cursor.execute('SELECT * FROM stocks LIMIT 5')")
    print("   print(cursor.fetchall())")
    
    print("\n🎯 教授建议遵守情况:")
    print("   ✅ 不要过早优化：使用SQLite而非PostgreSQL")
    print("   ✅ 保持轻量：单文件数据库，易于备份")
    print("   ✅ 数据质量优先：包含完整的数据质量监控表")


if __name__ == "__main__":
    main()