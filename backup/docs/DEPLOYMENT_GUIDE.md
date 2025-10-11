# GitHub自动部署脚本使用指南

## 概述

本项目提供了两个自动化脚本来简化代码提交和推送到GitHub的过程：

- `deploy_to_github.sh` - Linux/macOS版本
- `deploy_to_github.bat` - Windows版本

## 功能特性

✅ **智能分支管理** - 自动切换或创建目标分支  
✅ **安全文件过滤** - 自动排除数据库文件、日志文件等  
✅ **完整性检查** - 验证Git配置和仓库状态  
✅ **详细日志** - 提供彩色输出和操作报告  
✅ **错误处理** - 完善的错误检测和提示  
✅ **自动同步** - 拉取远程最新更改  

## 使用方法

### Linux/macOS用户

```bash
# 使脚本可执行（仅第一次需要）
chmod +x deploy_to_github.sh

# 提交到master分支
./deploy_to_github.sh master "功能更新：增量导入和统计修复"

# 提交到develop分支
./deploy_to_github.sh develop "Bug修复"

# 使用自动生成的提交信息
./deploy_to_github.sh feature-branch
```

### Windows用户

```cmd
# 提交到master分支
deploy_to_github.bat master "功能更新：增量导入和统计修复"

# 提交到develop分支
deploy_to_github.bat develop "Bug修复"

# 使用自动生成的提交信息
deploy_to_github.bat feature-branch
```

## 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `branch_name` | ✅ | 目标分支名称 | `master`, `develop`, `feature-xxx` |
| `commit_message` | ❌ | 提交信息 | `"新功能：增量导入"` |

## 自动排除的文件

脚本会自动排除以下文件类型，避免将敏感或临时文件提交到GitHub：

- **数据库文件**: `*.db`, `db/*.db`, `instance/*.db`
- **日志文件**: `logs/*.log`
- **Python缓存**: `__pycache__/`, `*.pyc`
- **系统文件**: `.DS_Store`, `Thumbs.db`

## 脚本执行流程

1. **参数验证** - 检查必需参数
2. **环境检查** - 验证Git安装和配置
3. **仓库验证** - 确认当前目录为Git仓库
4. **分支管理** - 切换到目标分支或创建新分支
5. **同步更新** - 拉取远程分支最新更改
6. **文件添加** - 添加所有更改，排除特定文件
7. **提交更改** - 使用指定或自动生成的提交信息
8. **推送代码** - 推送到远程仓库
9. **生成报告** - 显示操作结果和详细信息

## 使用示例

### 场景1：日常开发提交

```bash
# Linux/macOS
./deploy_to_github.sh develop "修复用户登录问题"

# Windows
deploy_to_github.bat develop "修复用户登录问题"
```

### 场景2：功能分支创建

```bash
# Linux/macOS
./deploy_to_github.sh feature-new-ui "实现新的用户界面"

# Windows
deploy_to_github.bat feature-new-ui "实现新的用户界面"
```

### 场景3：快速提交（自动生成消息）

```bash
# Linux/macOS
./deploy_to_github.sh master

# Windows
deploy_to_github.bat master
```

## 错误处理

脚本包含完善的错误处理机制：

### 常见错误及解决方案

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `当前目录不是git仓库` | 不在Git项目目录中 | 切换到正确的项目目录 |
| `Git用户配置未设置` | Git用户信息未配置 | 执行 `git config` 命令设置用户信息 |
| `未找到远程仓库origin` | 没有配置远程仓库 | 添加远程仓库：`git remote add origin <url>` |
| `推送失败` | 网络问题或权限不足 | 检查网络连接和GitHub权限 |

### Git配置示例

```bash
# 设置用户名和邮箱
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 添加远程仓库
git remote add origin https://github.com/username/repository.git
```

## 输出示例

```
[INFO] 开始部署到GitHub...
[INFO] 目标分支: master
[INFO] 提交信息: 新功能：增量导入和统计修复
[INFO] Git配置检查通过...
[INFO] 当前分支: master
[INFO] 拉取远程分支最新更改...
[INFO] 检查Git状态...
[INFO] 添加文件到暂存区...
[INFO] 即将提交的文件：
M       models/ticket.py
M       services/analysis_service.py
A       SystemLogic.md
[INFO] 提交更改...
[SUCCESS] 提交成功！
[INFO] 推送到远程仓库 origin/master...
[SUCCESS] 推送成功！
[INFO] 最新提交信息：
a1b2c3d 新功能：增量导入和统计修复
[SUCCESS] 部署完成！
[INFO] 远程仓库: https://github.com/scaleflower/otrs-web.git
[INFO] 分支: master
[INFO] 提交哈希: a1b2c3d4e5f6...

==========================================
           部署报告
==========================================
时间: 2025-09-03 01:08:45
分支: master
提交: a1b2c3d 新功能：增量导入和统计修复
仓库: https://github.com/scaleflower/otrs-web.git
操作员: Developer <dev@example.com>
==========================================
```

## 最佳实践

1. **提交前检查** - 确保代码已经测试通过
2. **有意义的提交信息** - 使用清晰描述性的提交信息
3. **小步提交** - 避免一次性提交过多更改
4. **分支策略** - 使用合适的分支策略（如GitFlow）
5. **代码审查** - 重要更改提交前进行代码审查

## 安全说明

- 脚本会自动排除敏感文件（数据库、日志等）
- 建议在 `.gitignore` 文件中配置项目特定的排除规则
- 不要在提交信息中包含敏感信息

## 故障排除

如果遇到问题，请按以下步骤排查：

1. 确认在正确的Git项目目录中
2. 检查Git是否正确安装和配置
3. 验证网络连接和GitHub访问权限
4. 查看完整的错误信息输出
5. 检查分支权限和保护规则

## 支持

如有问题或建议，请：

1. 查看脚本输出的详细错误信息
2. 检查本文档的故障排除部分
3. 确认Git环境配置正确
4. 联系项目维护者

---

**注意**: 使用脚本前请确保已备份重要数据，并在测试环境中验证脚本功能。
