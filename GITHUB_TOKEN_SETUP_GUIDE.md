# GitHub Token 配置指南

## 问题描述
当前遇到 GitHub API 401 错误："Bad credentials"，说明配置的 Token 无效。

## 解决方案

### 步骤1: 创建有效的 GitHub Personal Access Token

1. **访问 Token 创建页面**
   - 打开 https://github.com/settings/tokens
   - 点击 "Generate new token" → "Generate new token (classic)"

2. **配置 Token 信息**
   - **Token name**: `OTRS Web Update`
   - **Expiration**: 建议选择 "No expiration" 或较长的有效期
   - **Select scopes**: 只需要勾选 `public_repo` 权限

3. **生成 Token**
   - 点击 "Generate token"
   - **重要**: 立即复制生成的 Token，它只会显示一次

### 步骤2: 更新配置文件

在 `.env` 文件中更新 Token 配置：

```bash
# GitHub Personal Access Token (必需，用于避免API速率限制)
# 获取地址: https://github.com/settings/tokens
# 权限: 只需要 public_repo (只读访问公共仓库)
APP_UPDATE_GITHUB_TOKEN=ghp_你的实际Token在这里
```

### 步骤3: 重启应用

```bash
# 如果应用正在运行，需要重启
# 或者重新启动 Flask 应用
python3 app.py
```

### 步骤4: 验证配置

运行验证脚本检查配置：

```bash
python3 check_github_config.py
```

### 步骤5: 测试功能

1. 打开应用首页
2. 点击 "检查更新" 按钮
3. 应该能够正常检查 GitHub 版本信息

## 常见问题

### Q: Token 权限不足
**A**: 确保 Token 有 `public_repo` 权限

### Q: Token 已过期
**A**: 重新生成新的 Token 并更新配置

### Q: 仍然遇到速率限制
**A**: 检查 Token 是否已正确配置并重启应用

### Q: 如何验证 Token 是否有效
**A**: 可以使用以下命令测试：

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/scaleflower/otrs-web/releases/latest
```

## 配置示例

有效的 `.env` 配置示例：

```bash
# 自动更新配置
APP_UPDATE_REPO=scaleflower/otrs-web
APP_UPDATE_GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890
APP_UPDATE_ENABLED=true
APP_UPDATE_RESTART_DELAY=5
```

## 安全建议

1. **不要提交 Token 到代码仓库**
2. **使用环境变量管理敏感信息**
3. **定期轮换 Token**
4. **使用最小必要权限**

配置有效的 GitHub Token 后，API 限制将从 60 次/小时提升到 5000 次/小时，完全满足应用需求。
