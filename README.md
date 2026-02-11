# analyse - Stock Analysis System (DSS)

## 📊 Project Overview

A modular, explainable Decision Support System for long-term stock market analysis across US, Hong Kong, and China A-share markets. Designed for research and educational purposes with clear separation between analysis and decision-making.

## 🎯 Core Philosophy

**"Explainability over prediction, analysis over automation"**

This system provides analytical insights to support human decision-making, not automated trading decisions.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Summary Interface                 │
│              (Structured context → Natural language)     │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                Decision Support Core                    │
│  (Trend scoring, Risk assessment, Rule-based logic)    │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                  Analysis Engine                        │
│  (Technical indicators, Sentiment analysis, ML models)  │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                     Data Layer                          │
│    (Multi-market integration, Normalization, Storage)   │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
stock-dss/
├── data/                    # Data layer modules
│   ├── acquisition/        # Market data collection
│   ├── normalization/      # Data standardization
│   └── storage/           # Database/File storage
├── analysis/               # Analysis engine modules
│   ├── technical/         # Technical indicators
│   ├── sentiment/         # NLP sentiment analysis
│   └── ml_models/         # Machine learning models
├── decision/              # Decision support core
│   ├── evaluation/        # Trend/risk scoring
│   ├── rules/            # Rule-based interpretation
│   └── explainability/    # Source attribution
├── integration/           # LLM and external interfaces
│   └── llm_context/      # Structured context generation
├── config/               # Configuration files
├── tests/               # Unit and integration tests
├── docs/                # Documentation
└── scripts/             # Utility scripts
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Alpha Vantage API key (for US market data)
- Access to Chinese financial data sources (for A-shares)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd stock-dss

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Quick Start
```bash
# Run basic data collection
python scripts/fetch_market_data.py --markets US,HK,CN

# Run technical analysis
python analysis/technical/compute_indicators.py

# Generate DSS report
python decision/generate_report.py --output report.json
```

## 🔧 Key Features

### 1. Multi-Market Data Integration
- **US Markets**: Alpha Vantage API, Yahoo Finance
- **Hong Kong Markets**: HKEX data sources
- **China A-Shares**: Chinese financial APIs
- **Unified Schema**: Timezone-normalized, currency-annotated

### 2. Comprehensive Analysis
- **Technical Indicators**: MA, RSI, MACD, Bollinger Bands, ATR
- **Sentiment Analysis**: News/article sentiment scoring
- **ML Models**: Risk estimation, return prediction
- **Market State Detection**: Trend identification, regime switching

### 3. Decision Support
- **Trend Scoring**: 0-100 scale with confidence intervals
- **Risk Assessment**: Low/Medium/High with justification
- **Rule-based Logic**: Configurable interpretation rules
- **Explainability**: Source feature attribution

### 4. LLM Integration
- **Structured Context**: Pre-validated data for LLM consumption
- **Natural Language Summaries**: Human-readable reports
- **Audit Trail**: Traceability from raw data to conclusions

## 📋 Development Roadmap

### Phase 1: Foundation (Current)
- [x] Requirements specification
- [x] Project structure setup
- [ ] Basic data layer implementation
- [ ] Core technical indicators
- [ ] Simple decision scoring

### Phase 2: Analysis Engine
- [ ] Advanced technical indicators
- [ ] Sentiment analysis pipeline
- [ ] ML model integration
- [ ] Backtesting framework

### Phase 3: Decision Support
- [ ] Comprehensive trend scoring
- [ ] Risk assessment models
- [ ] Rule-based interpretation engine
- [ ] Explainability framework

### Phase 4: Integration & Deployment
- [ ] LLM context generation
- [ ] Web interface/dashboard
- [ ] Automated reporting
- [ ] Performance optimization

## 👥 Team Roles & Responsibilities

| Module | Primary Role | Key Tasks |
|--------|-------------|-----------|
| **Data Layer** | Data Engineer | API integration, Data normalization, Storage design |
| **Technical Analysis** | Quant/ML Engineer | Indicator computation, Feature engineering |
| **Sentiment Analysis** | NLP Engineer | Text processing, Sentiment models, Aggregation |
| **ML Models** | ML Engineer | Risk/return prediction, Model training |
| **Decision Support** | System Designer | Scoring logic, Rule engine, Explainability |
| **LLM Integration** | Integration Engineer | Context structuring, Interface design |

## 🧪 Testing Strategy

- **Unit Tests**: Individual module functionality
- **Integration Tests**: Module interaction testing
- **Data Validation**: Input/output data consistency
- **Reproducibility Tests**: Deterministic output verification
- **Performance Tests**: Batch processing timing

## 📚 Documentation

- **API Documentation**: Module interfaces and usage
- **Data Dictionary**: Schema definitions and mappings
- **Algorithm References**: Technical indicator formulas
- **Decision Logic**: Rule definitions and interpretations
- **Deployment Guide**: Setup and configuration instructions

## ⚠️ Important Disclaimers

### What This System IS:
- A decision support tool for research and education
- A framework for market analysis experimentation
- A learning platform for quantitative finance concepts

### What This System IS NOT:
- A trading system or automated trading advisor
- A guarantee of investment returns or predictions
- A replacement for professional financial advice
- Regulatory compliant for commercial trading

### Key Limitations:
- Historical performance ≠ future results
- Models have inherent assumptions and biases
- Market conditions can change unexpectedly
- Data sources may have latency or inaccuracies

## 🔗 Related Resources

### Data Sources
- [Alpha Vantage](https://www.alphavantage.co/) - US market data
- [Yahoo Finance](https://finance.yahoo.com/) - Historical data
- [东方财富](http://www.eastmoney.com/) - Chinese market data
- [新浪财经](https://finance.sina.com.cn/) - Chinese financial news

### Technical References
- [Technical Analysis of Financial Markets](https://www.amazon.com/Technical-Analysis-Financial-Markets-Comprehensive/dp/0735200661)
- [Python for Finance](https://www.amazon.com/Python-Finance-Yves-Hilpisch/dp/1492024333)
- [Machine Learning for Asset Managers](https://www.amazon.com/Machine-Learning-Asset-Managers-Elements/dp/1108792898)

### Open Source Tools
- [TA-Lib](https://github.com/mrjbq7/ta-lib) - Technical analysis library
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API
- [pandas-ta](https://github.com/twopirllc/pandas-ta) - Pandas technical analysis

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Alpha Vantage for providing free tier API access
- Open source financial analysis libraries
- Academic research in quantitative finance
- The open source community for tools and inspiration

---

**Remember**: This is a research and educational tool. Always conduct your own due diligence and consult with financial professionals before making investment decisions.