# 系统升级功能使用指南

## 功能概述

OTRS Web 应用现已集成自动版本检测和升级功能，支持从 GitHub 和阿里云云效（Codeup）检测和下载新版本，并提供一键升级功能。

## 主要特性

### 1. 版本检测
- ✅ 自动检测 GitHub Releases 上的最新版本
- ✅ 支持从阿里云云效检测最新版本
- ✅ 智能版本号比较
- ✅ 缓存机制减少 API 调用

### 2. 自动升级
- ✅ 一键升级到最新版本
- ✅ 升级前自动备份当前版本
- ✅ 自动下载并解压 release 包
- ✅ 自动安装依赖
- ✅ 升级失败自动回滚
- ✅ 实时显示升级进度和日志

### 3. 备份管理
- ✅ 查看所有升级备份
- ✅ 一键恢复到任意备份版本
- ✅ 显示备份大小和创建时间

### 4. 版本历史
- ✅ 查看最近 10 个版本的更新日志
- ✅ Markdown 格式的 Release Notes
- ✅ 直接跳转到 GitHub/云效查看详情

## 配置说明

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 应用版本（必须）
APP_VERSION=1.2.9.1

# 更新源：github 或 yunxiao（默认：github）
APP_UPDATE_SOURCE=github

# GitHub 配置
APP_UPDATE_REPO=scaleflower/otrs-web
APP_UPDATE_GITHUB_TOKEN=your_github_token  # 可选，避免 API 限流

# 云效配置（当 APP_UPDATE_SOURCE=yunxiao 时使用）
APP_UPDATE_YUNXIAO_REPO=68720966aa7bbf6cb884753e/scaleflower/otrs-web
APP_UPDATE_YUNXIAO_TOKEN=your_yunxiao_token  # 私有仓库需要

# 自动检查配置
APP_UPDATE_AUTO_CHECK=true  # 是否自动检查更新
APP_UPDATE_CHECK_INTERVAL=24  # 检查间隔（小时）
```

### 版本号格式

版本号遵循语义化版本规范 (Semantic Versioning):

```
主版本号.次版本号.修订号
例如: 1.2.9.1
```

## 使用方法

### 1. 访问升级页面

在应用中点击导航栏的"系统升级"，或直接访问:

```
http://your-server:15001/upgrade
```

### 2. 检查更新

点击"检查更新"按钮，系统将：
1. 从配置的更新源获取最新版本信息
2. 比较当前版本和最新版本
3. 如果有新版本，显示 Release Notes

### 3. 开始升级

如果检测到新版本：

1. 点击"开始升级"按钮
2. 确认升级提示
3. 系统自动执行以下步骤：
   - 创建当前版本备份
   - 下载新版本文件
   - 解压文件
   - 安装依赖（pip install -r requirements.txt）
   - 更新应用文件
   - 显示升级结果

4. 升级完成后，**重启应用**以应用更改：

```bash
# 如果使用 systemd
sudo systemctl restart otrs-web

# 如果使用 Docker
docker-compose restart

# 如果直接运行
# 停止当前进程，然后：
python3 app.py
```

### 4. 备份恢复

如果升级后出现问题，可以恢复到之前的备份：

1. 在"备份管理"部分查看所有可用备份
2. 选择要恢复的备份，点击"恢复"按钮
3. 确认恢复操作
4. 重启应用

## API 接口

升级功能提供以下 API 接口：

### 检查更新

```http
GET /upgrade/api/check-update?force=false
```

响应：
```json
{
  "success": true,
  "data": {
    "update_available": true,
    "current_version": "1.2.9",
    "latest_version": "1.2.9.1",
    "release_name": "v1.2.9.1",
    "release_notes": "## 新特性\n...",
    "download_url": "https://github.com/...",
    "tarball_url": "https://github.com/.../tarball/v1.2.9.1",
    "zipball_url": "https://github.com/.../zipball/v1.2.9.1"
  }
}
```

### 开始升级

```http
POST /upgrade/api/start-upgrade
Content-Type: application/json

{
  "download_url": "https://github.com/.../tarball/v1.2.9.1",
  "is_tarball": true
}
```

响应：
```json
{
  "success": true,
  "message": "Upgrade completed successfully",
  "log": [
    "[2025-01-17 10:00:00] [INFO] Creating backup...",
    "[2025-01-17 10:00:05] [INFO] Backup created successfully",
    ...
  ]
}
```

### 获取版本历史

```http
GET /upgrade/api/version-history?limit=10
```

### 获取备份列表

```http
GET /upgrade/api/backup-list
```

### 恢复备份

```http
POST /upgrade/api/restore-backup
Content-Type: application/json

{
  "backup_path": "/path/to/backup_20250117_100000"
}
```

## 安全注意事项

1. **备份数据库**: 虽然升级会自动备份代码，但建议升级前手动备份数据库

2. **权限管理**: 确保应用有权限写入以下目录：
   - `upgrade_backups/` - 存储升级备份
   - 应用根目录 - 更新文件

3. **网络要求**:
   - GitHub: 需要能访问 `api.github.com` 和 `github.com`
   - 云效: 需要能访问 `codeup.aliyun.com`

4. **Token 安全**:
   - GitHub Token 和云效 Token 应设置为只读权限
   - 使用环境变量存储，不要提交到代码仓库

## 故障排查

### 问题 1: 升级失败，提示下载错误

**原因**: 网络问题或 Token 配置错误

**解决方案**:
1. 检查网络连接
2. 如果使用私有仓库，确认 Token 配置正确
3. 查看升级日志了解详细错误信息

### 问题 2: 依赖安装失败

**原因**: pip 环境问题或依赖冲突

**解决方案**:
1. 确保 pip 已更新: `pip install --upgrade pip`
2. 查看升级日志中的具体错误
3. 如果失败，系统会自动回滚，手动恢复备份

### 问题 3: 升级后应用无法启动

**原因**: 配置文件不兼容或依赖问题

**解决方案**:
1. 访问 `/upgrade` 页面，从备份恢复到之前版本
2. 检查 `.env` 文件配置
3. 手动运行 `pip install -r requirements.txt`
4. 查看应用日志了解详细错误

### 问题 4: 检查更新时提示 API 限流

**原因**: GitHub API 有访问限制（未认证: 60次/小时）

**解决方案**:
1. 配置 `APP_UPDATE_GITHUB_TOKEN` 环境变量
2. 或切换到云效更新源（如果有）
3. 等待一小时后再次尝试

## 开发说明

### 服务架构

```
services/
├── version_service.py      # 版本检测和比较
└── upgrade_service.py      # 升级和备份管理

blueprints/
└── upgrade_bp.py           # 升级管理路由

templates/
└── upgrade.html            # 升级管理界面
```

### 添加新的更新源

要添加新的更新源（如 GitLab、Gitee 等），修改 `version_service.py`:

```python
def _get_latest_from_custom_source(self):
    """Get latest release from custom source"""
    # 实现自定义更新源的逻辑
    pass
```

然后在 `check_for_updates()` 方法中添加分支：

```python
if update_source == 'custom':
    latest_info = self._get_latest_from_custom_source()
```

### 自定义升级流程

如果需要在升级过程中执行特殊操作（如数据库迁移），修改 `upgrade_service.py` 的 `perform_upgrade()` 方法，在相应步骤添加自定义逻辑。

## 最佳实践

1. **定期检查更新**: 每周检查一次是否有新版本
2. **测试环境先行**: 如有条件，先在测试环境升级测试
3. **保留多个备份**: 不要删除最近 3-5 个升级备份
4. **监控日志**: 升级后查看应用日志确保一切正常
5. **数据库备份**: 重要升级前单独备份数据库

## 相关文档

- [GitHub Releases API](https://docs.github.com/en/rest/releases)
- [阿里云云效 API](https://help.aliyun.com/document_detail/464941.html)
- [语义化版本规范](https://semver.org/lang/zh-CN/)

## 支持

如遇问题，请：
1. 查看升级日志获取详细错误信息
2. 检查本文档的故障排查部分
3. 在 GitHub Issues 提交问题: https://github.com/scaleflower/otrs-web/issues
