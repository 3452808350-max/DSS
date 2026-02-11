#!/bin/bash
# GitHub推送脚本
# 使用方法: ./push_to_github.sh YOUR_GITHUB_URL

set -e  # 遇到错误时退出

echo "🚀 Stock Analysis DSS - GitHub推送工具"
echo "========================================"

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供GitHub仓库URL"
    echo ""
    echo "使用方法:"
    echo "  $0 https://github.com/your-username/stock-analysis-dss.git"
    echo ""
    echo "获取URL步骤:"
    echo "1. 登录GitHub (Google登录)"
    echo "2. 创建新仓库 (选择Private)"
    echo "3. 复制HTTPS URL"
    exit 1
fi

GITHUB_URL="$1"
PROJECT_DIR="/home/kyj/文档/code"

cd "$PROJECT_DIR"

echo "📁 项目目录: $PROJECT_DIR"
echo "🔗 GitHub URL: $GITHUB_URL"
echo ""

# 检查git状态
echo "📊 检查Git状态..."
git status

echo ""
read -p "是否继续推送? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 操作取消"
    exit 0
fi

# 添加远程仓库
echo "🔗 添加远程仓库..."
if git remote | grep -q origin; then
    echo "⚠️  远程仓库origin已存在，更新URL..."
    git remote set-url origin "$GITHUB_URL"
else
    git remote add origin "$GITHUB_URL"
fi

echo "✅ 远程仓库配置完成"
git remote -v
echo ""

# 推送代码
echo "📤 推送代码到GitHub..."
echo "这可能需要一些时间..."

if git push -u origin master; then
    echo ""
    echo "🎉 推送成功!"
    echo ""
    echo "✅ 完成事项:"
    echo "  1. 代码已推送到GitHub私有仓库"
    echo "  2. 远程分支已设置"
    echo "  3. 所有文件已上传"
    echo ""
    echo "🔍 下一步:"
    echo "  1. 访问GitHub查看仓库"
    echo "  2. 邀请协作者 (如果需要)"
    echo "  3. 设置仓库描述和主题标签"
    echo "  4. 配置GitHub Actions (可选)"
else
    echo ""
    echo "❌ 推送失败!"
    echo ""
    echo "🔧 故障排除:"
    echo "  1. 检查网络连接"
    echo "  2. 验证GitHub URL"
    echo "  3. 确认有推送权限"
    echo "  4. 尝试使用SSH代替HTTPS"
    echo ""
    echo "🔄 备用命令:"
    echo "  git push --force origin master  # 强制推送 (谨慎使用)"
    exit 1
fi

echo ""
echo "📈 项目统计:"
echo "  提交数量: $(git rev-list --count HEAD)"
echo "  文件数量: $(git ls-files | wc -l)"
echo "  代码行数: $(git ls-files | xargs cat | wc -l)"
echo ""
echo "🏁 推送流程完成!"