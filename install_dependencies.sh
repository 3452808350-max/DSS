#!/bin/bash
# analyse DSS 依赖安装脚本

echo "📦 安装 analyse DSS 项目依赖"
echo "=" * 60

cd /home/kyj/文档/analyse

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在，正在创建..."
    /home/kyj/.local/bin/uv venv .venv
    source .venv/bin/activate
fi

echo ""
echo "📋 安装阶段 1: 核心依赖"
echo "-" * 40

# 核心数据科学库
echo "安装 pandas, numpy, requests..."
/home/kyj/.local/bin/uv pip install pandas numpy requests

echo ""
echo "📋 安装阶段 2: 数据获取"
echo "-" * 40

# 数据获取库
echo "安装 yfinance, alpha-vantage..."
/home/kyj/.local/bin/uv pip install yfinance alpha-vantage

echo ""
echo "📋 安装阶段 3: 技术分析"
echo "-" * 40

# 技术分析库
echo "安装 pandas-ta (TA-LIB替代)..."
/home/kyj/.local/bin/uv pip install pandas-ta

echo ""
echo "📋 安装阶段 4: 基础工具"
echo "-" * 40

# 基础工具
echo "安装 matplotlib, seaborn, python-dotenv..."
/home/kyj/.local/bin/uv pip install matplotlib seaborn python-dotenv schedule

echo ""
echo "📋 安装阶段 5: 数据库"
echo "-" * 40

# 数据库
echo "安装 sqlalchemy..."
/home/kyj/.local/bin/uv pip install sqlalchemy

echo ""
echo "📋 安装阶段 6: 测试工具"
echo "-" * 40

# 测试工具
echo "安装 pytest..."
/home/kyj/.local/bin/uv pip install pytest pytest-cov

echo ""
echo "🎉 依赖安装完成!"
echo ""
echo "📊 已安装包:"
/home/kyj/.local/bin/uv pip list | grep -E "(pandas|numpy|requests|yfinance|alpha|pandas-ta|matplotlib|seaborn|sqlalchemy|pytest)"

echo ""
echo "🚀 下一步:"
echo "1. 测试系统: python main.py test"
echo "2. 获取数据: python main.py fetch"
echo "3. 查看信息: python main.py info"

# 创建激活脚本
cat > activate_project.sh << 'EOF'
#!/bin/bash
# analyse DSS 项目激活脚本

cd /home/kyj/文档/analyse
source .venv/bin/activate
echo "✅ analyse DSS 项目已激活"
echo "   虚拟环境: .venv"
echo "   项目目录: $(pwd)"
echo ""
echo "可用命令:"
echo "  python main.py test    # 测试系统"
echo "  python main.py fetch   # 获取市场数据"
echo "  python main.py info    # 查看系统信息"
EOF

chmod +x activate_project.sh
echo ""
echo "💡 快速激活脚本: ./activate_project.sh"