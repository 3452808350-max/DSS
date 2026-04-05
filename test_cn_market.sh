#!/bin/bash
# 测试中国A股数据模块

echo "🧪 测试中国A股数据获取模块"
echo "=" * 60

cd /home/kyj/文档/analyse

# 激活虚拟环境
source .venv/bin/activate

echo "1. 检查akshare安装状态..."
python -c "import akshare; print('✅ akshare版本:', akshare.__version__)" 2>/dev/null || {
    echo "❌ akshare未安装，正在安装..."
    /home/kyj/.local/bin/uv pip install akshare
}

echo ""
echo "2. 运行中国A股模块测试..."
python -c "
import sys
sys.path.insert(0, '.')
from data.acquisition.cn_market import test_cn_market_module
test_cn_market_module()
" 2>&1

echo ""
echo "3. 集成测试 - 更新main.py支持中国A股..."
# 备份原文件
cp main.py main.py.backup

echo ""
echo "🎯 下一步:"
echo "1. 如果测试成功，中国A股数据模块就绪"
echo "2. 可以更新main.py添加中国A股支持"
echo "3. 开始数据规范化系统开发"
echo ""
echo "💡 Vibe Coding成果:"
echo "   - 使用成熟库(akshare)而不是从零开发"
echo "   - 胶水代码连接现有轮子"
echo "   - 统一接口设计，便于扩展"