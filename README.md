# GitHub Daily Digest

每日自动获取 GitHub 热门项目，生成中文总结并发送邮件报告。

## 功能

- **🔥 Stars 昨日增长 Top 10** - 从 GitHub Trending 获取
- **📈 Stars 增长率 Top 10** - 从 OssInsight API 获取（发现黑马项目）
- **📅 本周订阅增长 Top 10** - 从 GitHub Trending Weekly 获取
- **⭐ Stars 总数最高 Top 10** - 从 GitHub API 获取（全站热门项目）
- **中文总结** - 混合风格：通俗易懂 + 技术细节
- **HTML 邮件** - 每天早上 8:00 自动发送
- **群发支持** - 支持多个收件人，逗号分隔

## 快速开始

### 1. Fork 仓库

点击右上角 `Fork` 按钮，将仓库复制到你的账号下。

### 2. 配置 GitHub Secrets

进入仓库 `Settings` → `Secrets and variables` → `Actions`，添加以下 Secrets：

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `SMTP_SERVER` | SMTP 服务器地址 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_SSL` | 是否启用 SSL | `true` |
| `SENDER_EMAIL` | 发件人邮箱 | `your-email@gmail.com` |
| `SENDER_PASSWORD` | 邮箱密码或应用专用密码 | `your-app-password` |
| `RECIPIENT_EMAIL` | 收件人邮箱（多个用逗号分隔） | `user@example.com` |

### 3. 获取邮箱授权码

#### Gmail

1. 访问 [Google 账号安全设置](https://myaccount.google.com/security)
2. 启用两步验证
3. 访问 [应用专用密码](https://myaccount.google.com/apppasswords)
4. 生成应用专用密码（选择"其他"，输入名称）
5. 复制生成的 16 位密码

#### QQ 邮箱

1. 登录 QQ 邮箱
2. 设置 → 账户 → POP3/IMAP/SMTP 服务
3. 开启 SMTP 服务
4. 生成授权码

#### 163 邮箱

1. 登录 163 邮箱
2. 设置 → POP3/SMTP/IMAP
3. 开启 SMTP 服务
4. 生成授权码

#### 139 邮箱

1. 登录 https://mail.10086.cn
2. 设置 → 邮箱协议
3. 开启 SMTP 服务
4. 获取授权码

### 4. 启用 Actions

1. 进入仓库 `Actions` 页面
2. 如果看到提示，点击 `I understand my workflows, go ahead and enable them`

### 5. 测试运行

在 `Actions` 页面，选择 `GitHub Daily Digest`，点击 `Run workflow` 手动触发一次测试。

## 定时配置

默认配置：每天北京时间 8:00 自动运行。

如需修改时间，编辑 `.github/workflows/daily-digest.yml`：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # UTC 00:00 = 北京时间 08:00
```

常用时间配置：
- 北京时间 08:00 → `cron: '0 0 * * *'`
- 北京时间 12:00 → `cron: '0 4 * * *'`
- 北京时间 20:00 → `cron: '0 12 * * *'`

## 群发配置

在 `RECIPIENT_EMAIL` 中用逗号分隔多个邮箱：

```
user1@example.com, user2@example.com, user3@example.com
```

## 本地测试

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/github-daily-digest.git
cd github-daily-digest

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="465"
export SMTP_SSL="true"
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"
export RECIPIENT_EMAIL="user@example.com"

# 运行
python scripts/main.py
```

## 工作原理

1. **爬取 GitHub Trending Daily** - 获取今日 Stars 增长最多的 10 个项目
2. **爬取 GitHub Trending Weekly** - 获取本周 Stars 增长最多的 10 个项目
3. **调用 OssInsight API** - 获取 Stars 增长率最高的 10 个项目
4. **调用 GitHub API** - 获取 Stars 总数最高的 10 个项目
5. **生成中文总结** - 使用 Google Translate 翻译 + 技术关键词提取
6. **生成 HTML 报告** - 包含 4 个表格、链接、统计数据
7. **发送邮件** - 通过 SMTP 发送到指定邮箱

## 失败重试

- GitHub Trending 爬取失败：等待 5/10/15 分钟后重试，共 3 次
- OssInsight API 失败：使用 GitHub API 作为备选方案
- 邮件发送失败：等待 1 分钟后重试，共 3 次

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
