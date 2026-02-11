#!/bin/bash
# NAS Git服务器设置脚本
# 在NAS上以root或sudo权限运行

set -e

echo "=== NAS Git服务器设置脚本 ==="
echo "时间: $(date)"
echo ""

# 检查系统
echo "1. 检查系统信息..."
cat /etc/os-release 2>/dev/null || echo "无法获取系统信息"
echo ""

# 安装Git
echo "2. 安装Git..."
if command -v git &> /dev/null; then
    echo "✅ Git已安装: $(git --version)"
else
    echo "安装Git..."
    apt update && apt install git -y
    echo "✅ Git安装完成: $(git --version)"
fi
echo ""

# 创建git用户
echo "3. 创建git用户..."
if id git &> /dev/null; then
    echo "✅ git用户已存在"
else
    echo "创建git用户..."
    echo "请按提示设置git用户密码（建议设置简单密码如'git123'）"
    adduser git
    echo "✅ git用户创建完成"
fi
echo ""

# 创建仓库目录
echo "4. 创建仓库目录..."
mkdir -p /srv/git
chown git:git /srv/git
chmod 755 /srv/git
echo "✅ 目录创建完成: /srv/git"
ls -ld /srv/git
echo ""

# 创建裸仓库
echo "5. 创建analyse.git裸仓库..."
if [ -d "/srv/git/analyse.git" ]; then
    echo "⚠️  仓库已存在，跳过创建"
else
    echo "切换到git用户创建仓库..."
    su - git -c "cd /srv/git && git init --bare analyse.git"
    echo "✅ 裸仓库创建完成"
fi
echo ""

# 验证
echo "6. 验证设置..."
echo "仓库内容:"
ls -la /srv/git/analyse.git/ 2>/dev/null || echo "仓库不存在"
echo ""

# 权限检查
echo "7. 权限检查..."
ls -ld /srv/git
ls -ld /srv/git/analyse.git 2>/dev/null || true
echo ""

echo "=== 设置完成 ==="
echo ""
echo "📋 下一步:"
echo "1. 从本地推送代码:"
echo "   cd /home/kyj/文档/analyse"
echo "   git remote add nas ssh://git@192.168.4.147/srv/git/analyse.git"
echo "   git push -u nas master"
echo ""
echo "2. 验证推送:"
echo "   su - git -c 'cd /srv/git/analyse.git && git log --oneline -5'"
echo ""
echo "3. 发送完成邮件:"
echo "   python /home/kyj/.openclaw/workspace/email_system.py"