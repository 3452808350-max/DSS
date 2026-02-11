# 晚上7点操作指南 - NAS Git服务器部署

## ⏰ 时间安排
**目标时间**: 2026-02-10 19:00 (晚上7点)
**预计耗时**: 15-30分钟

## 📋 完整操作流程

### 第一阶段: NAS Git服务器设置 (5-10分钟)

#### 步骤1: SSH登录NAS
```bash
ssh -p 3410 rootKYJ@192.168.4.147
# 密码: Kyj 1145141919810.
```

#### 步骤2: 安装和配置Git
```bash
# 更新包列表
apt update

# 安装Git
apt install git -y

# 创建Git用户 (按提示设置密码，其他信息可留空)
adduser git

# 创建仓库目录
mkdir -p /srv/git
chown git:git /srv/git
chmod 755 /srv/git
```

#### 步骤3: 创建项目仓库
```bash
# 切换到git用户
su - git

# 创建裸仓库
cd /srv/git
git init --bare analyse.git

# 退出git用户
exit
```

#### 步骤4: 验证NAS设置
```bash
# 检查仓库创建
ls -la /srv/git/

# 应该看到: analyse.git/
```

### 第二阶段: 本地推送代码 (5分钟)

#### 步骤5: 返回本地终端
```bash
# 按Ctrl+D退出NAS SSH，回到本地
exit
```

#### 步骤6: 运行推送脚本
```bash
cd /home/kyj/文档/analyse

# 方法A: 使用推送脚本 (推荐)
./scripts/push_to_nas.sh

# 方法B: 手动推送
git remote add nas ssh://git@192.168.4.147:3410/srv/git/analyse.git
git push -u nas master
```

#### 步骤7: 验证推送
```bash
# 验证NAS上的仓库
ssh -p 3410 rootKYJ@192.168.4.147 \
  'su - git -c "cd /srv/git/analyse.git && git log --oneline -5"'

# 应该看到你的提交历史
```

### 第三阶段: 邮件提醒配置和发送 (5-10分钟)

#### 步骤8: 配置QQ邮箱
1. **登录QQ邮箱**: mail.qq.com
2. **进入设置**: 右上角设置 → 账户
3. **开启服务**: 找到"POP3/IMAP/SMTP服务"
4. **开启服务**: 点击开启 (可能需要短信验证)
5. **生成授权码**: 记下16位授权码 (不是邮箱密码)

#### 步骤9: 更新邮件脚本
```bash
cd /home/kyj/文档/analyse
nano /home/kyj/.openclaw/workspace/email_system.py
```

修改以下两行 (大约第20-21行):
```python
self.sender_email = "3452808350@qq.com"  # 你的QQ邮箱
self.sender_password = "你的16位授权码"   # 刚才生成的授权码
```

保存并退出: `Ctrl+X` → `Y` → `Enter`

#### 步骤10: 发送完成邮件
```bash
# 发送NAS推送完成邮件
python scripts/send_nas_completion_email.py

# 按照提示操作
```

#### 步骤11: (可选) 设置每日提醒
```bash
# 运行脚本并选择设置每日提醒
python scripts/send_nas_completion_email.py

# 当询问"是否设置每日邮件提醒?"时输入 y
```

## 🔐 安全注意事项

### API密钥保护
当前API密钥在代码中，NAS在本地网络相对安全，但建议:

1. **短期**: 保持现状，NAS有基本安全
2. **中期**: 创建 `.env` 文件存储密钥
3. **长期**: 使用密钥管理服务

### NAS安全加固
```bash
# 在NAS上执行
# 1. 修改SSH端口 (可选)
nano /etc/ssh/sshd_config
# 修改 Port 3410 为其他端口

# 2. 禁用root SSH登录
# 在sshd_config中添加: PermitRootLogin no

# 3. 重启SSH服务
systemctl restart sshd
```

## 📧 邮件系统功能

### 已实现的邮件类型:
1. **NAS推送完成提醒** - 推送成功后自动发送
2. **NAS推送失败提醒** - 推送失败时发送
3. **每日项目提醒** - 可配置定时发送
4. **自定义提醒** - 任意时间手动发送

### 邮件内容包含:
- ✅ 项目状态摘要
- ✅ 安全提醒
- ✅ 后续操作指南
- ✅ HTML格式美化

### 收件人配置:
当前配置发送到:
1. `3452808350@qq.com` (你的QQ邮箱)
2. 可添加第二个邮箱 (需要完整地址)

## 🚨 故障排除

### 常见问题1: SSH连接失败
```bash
# 检查NAS是否开机
ping 192.168.4.147

# 检查SSH服务
ssh -p 3410 rootKYJ@192.168.4.147 "echo test"

# 解决方案: 重启NAS或检查网络
```

### 常见问题2: Git推送权限错误
```bash
# 检查NAS目录权限
ssh -p 3410 rootKYJ@192.168.4.147 "ls -la /srv/git/"

# 解决方案: 修正权限
ssh -p 3410 rootKYJ@192.168.4.147 "chown -R git:git /srv/git"
```

### 常见问题3: 邮件发送失败
```bash
# 测试邮件配置
python /home/kyj/.openclaw/workspace/email_system.py

# 检查:
# 1. QQ邮箱是否开启SMTP
# 2. 授权码是否正确
# 3. 网络连接是否正常
```

## ✅ 成功标准

完成所有步骤后，你应该有:

1. ✅ NAS Git服务器运行中
2. ✅ 代码推送到NAS仓库
3. ✅ 收到确认邮件 (QQ邮箱)
4. ✅ 可以从NAS克隆项目
5. ✅ 每日提醒已配置 (可选)

## 📞 紧急联系

如果遇到问题:

1. **检查日志**: `cat /home/kyj/文档/analyse/logs/stock_dss.log`
2. **查看错误**: 运行脚本时注意错误信息
3. **备份方案**: 代码已在本地Git，可稍后重试

## 🎯 晚上7点后的下一步

完成NAS部署后，可以:

1. **完善项目**: 按照TASKS.md Week 1计划
2. **测试功能**: 运行 `python main.py test`
3. **获取数据**: 运行 `python main.py fetch`
4. **文档更新**: 记录NAS部署过程

---

**提醒**: 晚上7点你会收到OpenClaw的系统提醒，按照此指南操作即可。

**备份**: 代码已在本地Git，即使NAS部署失败，项目也是安全的。

**安全**: API密钥在本地网络相对安全，后续可进一步加固。