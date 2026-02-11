#!/bin/bash
# 推送到NAS Git服务器脚本
# 使用方法: ./push_to_nas.sh

set -e  # 遇到错误时退出

echo "🚀 analyse - NAS Git服务器推送工具"
echo "=============================================="
echo "时间: $(date)"
echo ""

PROJECT_DIR="/home/kyj/文档/analyse"
NAS_IP="192.168.4.147"
NAS_PORT="3410"
NAS_USER="rootKYJ"
REPO_NAME="analyse.git"

cd "$PROJECT_DIR"

echo "📁 项目目录: $PROJECT_DIR"
echo "🏠 NAS地址: $NAS_IP:$NAS_PORT"
echo "👤 NAS用户: $NAS_USER"
echo "📦 仓库名称: $REPO_NAME"
echo ""

# 检查本地Git状态
echo "📊 检查本地Git状态..."
git status

echo ""
read -p "是否继续推送到NAS? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 操作取消"
    exit 0
fi

echo "🔍 测试NAS连接..."
if ssh -p "$NAS_PORT" "$NAS_USER@$NAS_IP" "echo 'NAS连接测试成功'"; then
    echo "✅ NAS连接正常"
else
    echo "❌ NAS连接失败"
    echo "请检查:"
    echo "  1. NAS是否开机"
    echo "  2. SSH服务是否运行"
    echo "  3. 网络连接"
    exit 1
fi

echo ""
echo "📋 NAS Git服务器设置检查..."
echo "请确保NAS上已执行以下命令:"
echo ""
echo "1. 安装Git:"
echo "   apt update && apt install git -y"
echo ""
echo "2. 创建Git用户和目录:"
echo "   adduser git"
echo "   mkdir -p /srv/git"
echo "   chown git:git /srv/git"
echo ""
echo "3. 创建裸仓库:"
echo "   su - git"
echo "   cd /srv/git"
echo "   git init --bare $REPO_NAME"
echo ""

read -p "NAS Git服务器是否已设置完成? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 请先在NAS上设置Git服务器"
    exit 1
fi

# 添加NAS远程仓库
echo "🔗 配置远程仓库..."
NAS_GIT_URL="ssh://git@$NAS_IP:$NAS_PORT/srv/git/$REPO_NAME"

if git remote | grep -q nas; then
    echo "⚠️  远程仓库nas已存在，更新URL..."
    git remote set-url nas "$NAS_GIT_URL"
else
    git remote add nas "$NAS_GIT_URL"
fi

echo "✅ 远程仓库配置完成"
git remote -v
echo ""

# 推送代码到NAS
echo "📤 推送代码到NAS Git服务器..."
echo "这可能需要一些时间..."

if git push -u nas master; then
    echo ""
    echo "🎉 推送成功!"
    echo ""
    echo "✅ 完成事项:"
    echo "  1. 代码已推送到NAS私有Git服务器"
    echo "  2. 远程分支已设置"
    echo "  3. 所有文件安全存储在本地网络"
    echo ""
    echo "🔍 验证推送:"
    echo "  在NAS上运行:"
    echo "  ssh -p $NAS_PORT $NAS_USER@$NAS_IP \\"
    echo "    'su - git -c \"cd /srv/git/$REPO_NAME && git log --oneline -5\"'"
    echo ""
    echo "💡 后续使用:"
    echo "  从NAS克隆: git clone ssh://git@$NAS_IP:$NAS_PORT/srv/git/$REPO_NAME"
    echo "  日常推送: git push nas"
    echo "  日常拉取: git pull nas"
else
    echo ""
    echo "❌ 推送失败!"
    echo ""
    echo "🔧 故障排除:"
    echo "  1. 检查NAS Git用户权限"
    echo "  2. 确认仓库路径正确"
    echo "  3. 检查SSH密钥配置"
    echo "  4. 查看详细错误信息"
    echo ""
    echo "🔄 备用方案:"
    echo "  1. 使用HTTP方式 (如果支持)"
    echo "  2. 直接复制文件到NAS"
    echo "  3. 使用rsync同步"
    exit 1
fi

echo ""
echo "📈 项目统计:"
echo "  提交数量: $(git rev-list --count HEAD)"
echo "  文件数量: $(git ls-files | wc -l)"
echo "  代码行数: $(git ls-files | xargs cat | wc -l)"
echo ""
echo "🔐 安全提醒:"
echo "  API密钥在本地代码中，NAS在本地网络相对安全"
echo "  建议后续将API密钥移到环境变量"
echo ""
echo "🏁 NAS推送流程完成!"