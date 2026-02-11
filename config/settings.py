"""
Configuration settings for analyse
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Create directories if they don't exist
for directory in [DATA_DIR, LOG_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# API Keys (load from environment variables)
class APIConfig:
    """API configuration"""
    
    # Alpha Vantage
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "MXAYBEBGFHR6PHYW")
    
    # Yahoo Finance (no key needed)
    YAHOO_FINANCE_ENABLED = True
    
    # Chinese financial APIs (to be configured)
    EAST_MONEY_API_KEY = os.getenv("EAST_MONEY_API_KEY", "")
    SINA_FINANCE_API_KEY = os.getenv("SINA_FINANCE_API_KEY", "")
    
    # Rate limiting (calls per minute)
    RATE_LIMITS = {
        "alpha_vantage": 5,  # Free tier: 5 calls per minute
        "yfinance": 10,      # Conservative limit
        "east_money": 20,    # Estimated
        "sina_finance": 20,  # Estimated
    }

# Database configuration
class DatabaseConfig:
    """Database configuration"""
    
    # SQLite for development
    SQLITE_PATH = DATA_DIR / "stock_dss.db"
    SQLITE_URL = f"sqlite:///{SQLITE_PATH}"
    
    # PostgreSQL for production
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "stock_dss")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Active database
    ACTIVE_DB = "sqlite"  # Change to "postgres" for production

# Market configuration
class MarketConfig:
    """Market-specific configuration"""
    
    # Trading hours (Beijing time)
    TRADING_HOURS = {
        "US": {
            "open": "22:30",  # 9:30 AM EST = 22:30 Beijing
            "close": "05:00",  # 4:00 PM EST = 05:00 Beijing (next day)
            "timezone": "America/New_York",
        },
        "HK": {
            "open": "09:30",
            "close": "16:00",
            "timezone": "Asia/Hong_Kong",
        },
        "CN": {
            "open": "09:30",
            "close": "15:00",
            "timezone": "Asia/Shanghai",
        }
    }
    
    # Default stocks to monitor
    DEFAULT_WATCHLIST = {
        "US": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"],
        "HK": ["0700.HK", "9988.HK", "3690.HK", "1810.HK"],  # Tencent, Alibaba, Meituan, Xiaomi
        "CN": ["600519.SS", "000001.SS", "601318.SS", "601166.SS"]  # Moutai, SSE, Ping An, Industrial Bank
    }
    
    # Market identifiers
    MARKET_IDENTIFIERS = {
        "US": ".US",
        "HK": ".HK",
        "CN": ".SS/.SZ"
    }

# Analysis configuration
class AnalysisConfig:
    """Analysis configuration"""
    
    # Technical indicators
    TECHNICAL_INDICATORS = {
        "moving_averages": [5, 10, 20, 50, 200],
        "rsi_period": 14,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "bollinger_period": 20,
        "bollinger_std": 2,
        "atr_period": 14,
    }
    
    # Sentiment analysis
    SENTIMENT_CONFIG = {
        "model": "textblob",  # Options: textblob, vader, transformers
        "update_frequency": "daily",  # How often to update sentiment data
        "sources": ["news", "social_media", "earnings_calls"],
    }
    
    # Machine learning
    ML_CONFIG = {
        "prediction_horizons": [30, 60, 90],  # Days
        "test_size": 0.2,  # Train-test split
        "cv_folds": 5,  # Cross-validation folds
        "random_state": 42,
    }

# Decision support configuration
class DecisionConfig:
    """Decision support configuration"""
    
    # Trend scoring
    TREND_SCORING = {
        "weights": {
            "technical": 0.4,
            "sentiment": 0.3,
            "fundamental": 0.2,
            "market_structure": 0.1,
        },
        "thresholds": {
            "strong_bull": 80,
            "bull": 60,
            "neutral": 40,
            "bear": 20,
            "strong_bear": 0,
        }
    }
    
    # Risk assessment
    RISK_ASSESSMENT = {
        "factors": ["volatility", "liquidity", "correlation", "leverage", "concentration"],
        "thresholds": {
            "low": 0.3,
            "medium": 0.6,
            "high": 1.0,
        }
    }
    
    # Rule-based interpretation
    RULES = {
        "trend_following": [
            "IF trend_score > 70 AND risk_level == 'low' THEN market_state = 'Strong Uptrend'",
            "IF trend_score < 30 AND risk_level == 'low' THEN market_state = 'Strong Downtrend'",
        ],
        "mean_reversion": [
            "IF rsi < 30 AND volume > average THEN potential = 'Oversold Bounce'",
            "IF rsi > 70 AND volume > average THEN potential = 'Overbought Pullback'",
        ]
    }

# LLM integration configuration
class LLMConfig:
    """LLM integration configuration"""
    
    # OpenClaw integration
    OPENCLAW_CONFIG = {
        "enabled": True,
        "model": "default",
        "max_tokens": 2000,
        "temperature": 0.7,
    }
    
    # Context generation
    CONTEXT_CONFIG = {
        "max_context_length": 4000,  # Characters
        "include_sources": True,
        "include_confidence": True,
        "format": "markdown",  # Options: markdown, json, plaintext
    }

# Logging configuration
class LoggingConfig:
    """Logging configuration"""
    
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOG_DIR / "stock_dss.log"
    
    # Rotate logs daily, keep 7 days
    LOG_ROTATION = "1 day"
    LOG_RETENTION = "7 days"

# Export configurations
API_CONFIG = APIConfig()
DB_CONFIG = DatabaseConfig()
MARKET_CONFIG = MarketConfig()
ANALYSIS_CONFIG = AnalysisConfig()
DECISION_CONFIG = DecisionConfig()
LLM_CONFIG = LLMConfig()
LOGGING_CONFIG = LoggingConfig()

# Convenience function to get all configs
def get_all_configs() -> Dict[str, Any]:
    """Get all configuration objects as a dictionary"""
    return {
        "api": API_CONFIG,
        "database": DB_CONFIG,
        "market": MARKET_CONFIG,
        "analysis": ANALYSIS_CONFIG,
        "decision": DECISION_CONFIG,
        "llm": LLM_CONFIG,
        "logging": LOGGING_CONFIG,
    }