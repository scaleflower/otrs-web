# OTRS Web 应用更新机制详解

## 更新流程概述

OTRS Web应用的自动更新功能通过GitHub Release提供的HTTP包完成，避免了在目标环境安装Git的要求。以下是完整的更新流程：

### 1. 检测阶段
- 应用通过GitHub API检查 `scaleflower/otrs-web` 仓库的最新release
- 使用语义化版本号比较算法判断是否需要更新
- 当前版本：`1.2.3`，最新版本：`release/v1.2.6`

### 2. 执行阶段
当用户点击"更新"按钮时，系统执行以下步骤：

#### 2.1 数据库备份
```bash
# 创建数据库备份（实际路径）
cp db/otrs_data.db database_backups/backup_before_update_manual.db
```

#### 2.2 下载并校验更新包
```bash
# 从 release tarball 下载更新包
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     -H "Accept: application/octet-stream" \
     -L "$(python3 - <<'PY'
import os, requests
repo = os.environ.get("APP_UPDATE_REPO", "scaleflower/otrs-web")
token = os.environ["GITHUB_TOKEN"]
tag = os.environ.get("TARGET_TAG", "release/v1.2.6")
resp = requests.get(f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
                    headers={"Authorization": f"Bearer {token}",
                             "Accept": "application/vnd.github+json"})
resp.raise_for_status()
print(resp.json()["tarball_url"])
PY
)" -o instance/releases/release-v1.2.6.tar.gz
```

#### 2.3 解压并同步文件
```bash
tar -xzf instance/releases/release-v1.2.6.tar.gz -C /tmp
rsync -a --exclude='.env' --exclude='uploads/' --exclude='database_backups/' \
      /tmp/otrs-web-release-v1.2.6/ /path/to/otrs-web/
```

#### 2.4 依赖安装
```bash
# 安装/更新Python依赖
python3 -m pip install -r requirements.txt
```

#### 2.5 数据库迁移（如果存在）
```bash
# 执行数据库迁移脚本（如果存在）
python3 upgrade_statistics_log_columns.py
python3 upgrade_database_with_new_records_count.py
```

### 3. 重启阶段
- 更新完成后，应用自动重启
- 在开发模式下使用子进程重启策略
- 在生产模式下使用进程替换重启策略

## 当前状态分析

### 问题识别
当前实现已经迁移为“下载Release包 → 解压 → 同步文件”的流程，因此无需处理Git分离头指针的问题。需要重点关注以下几点：

1. **更新包是否下载成功**：检查 `instance/releases/<版本>` 目录
2. **同步过程中是否保留敏感文件**：`.env`、`uploads/`、`database_backups/` 等路径默认跳过
3. **依赖安装与迁移是否成功**：查看更新日志与命令输出

## 验证更新是否成功

### 方法1：检查版本号
```bash
sqlite3 db/otrs_data.db "SELECT current_version FROM app_update_status;"
```

### 方法2：查看配置中的版本
```bash
grep "APP_VERSION" config/base.py
```

### 方法3：检查更新日志
访问页面“更新日志”或查看 `logs/update.log` 以获取每个步骤的执行结果。

## 解决当前问题

### 方案1：重新下载更新包
删除 `instance/releases/<版本>` 后重新执行更新，确保网络与GitHub Token配置正确。

### 方案2：手动解压覆盖
在临时目录手动解压 Release 包，确定文件完整后再同步到应用目录。

### 方案3：回滚至备份
若更新失败，可将 `database_backups` 中的备份恢复到 `db/otrs_data.db`，然后重新部署上一版本的代码包。

## 推荐的更新流程

### 对于生产环境
1. **备份重要数据**
   - 数据库文件 (`db/otrs_data.db`)
   - 配置文件 (`.env`)
   - 上传文件 (`uploads/`)

2. **执行更新**
   ```bash
   python3 scripts/update_app.py --repo=scaleflower/otrs-web --target=release/v1.2.6
   ```

3. **验证更新**
   ```bash
   python3 app.py
   ```

### 对于开发环境
1. **提交或暂存本地修改**
   ```bash
   cp -r . ../otrs-web-backup
   ```

2. **执行更新**
   ```bash
   python3 scripts/update_app.py --repo=scaleflower/otrs-web --target=release/v1.2.6
   ```

3. **恢复本地修改（如果需要）**
   ```bash
   rsync -a ../otrs-web-backup/ .
   ```

## 故障排除

### 常见问题

#### Q: 更新后应用无法启动
**A**: 检查依赖是否安装成功
```bash
pip install -r requirements.txt
```

#### Q: 数据库连接错误
**A**: 恢复数据库备份
```bash
cp database_backups/backup_before_update_manual.db db/otrs_data.db
```

#### Q: 权限错误
**A**: 检查文件权限
```bash
chmod +x scripts/update_app.py
```

## 总结

新的自动更新机制完全基于HTTP下载与包解压，解决了在目标环境必须安装Git的问题。通过统一的更新守护进程，系统会依次执行备份、包下载、文件同步、依赖安装和迁移脚本，并在完成后触发应用重启。若任一步骤失败，可借助更新日志快速定位问题，并通过保留的数据库备份进行回滚。

HTTP 包更新同样具备以下优势：

- ✅ 默认跳过 `.env`、`uploads/`、`database_backups/` 等关键数据；
- ✅ 仅覆盖发布包内的文件，支持自定义保留列表；
- ✅ 自动执行依赖安装与迁移脚本；
- ✅ 更新日志完整记录，可快速定位失败原因并回滚。

若更新后文件时间戳没有变化，通常是发布包内文件未变更或被保留规则跳过。建议通过数据库中的版本号与更新日志来确认更新是否成功。
