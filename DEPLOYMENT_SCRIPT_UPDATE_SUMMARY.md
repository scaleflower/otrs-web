# 自动部署脚本更新总结

## 更新概述

修改了所有GitHub自动部署脚本，使其在未提供参数时默认提交到master分支。

## 修改的文件

### 1. deploy_to_github.sh (Linux/macOS版本)
- **主要变更**: 将branch_name参数从必需改为可选，默认值为"master"
- **新功能**: 
  - 无参数调用时自动使用master分支
  - 添加了 `-h` 和 `--help` 选项显示详细使用说明
  - 改进的参数处理逻辑

### 2. deploy_to_github.bat (Windows中文版本)
- **主要变更**: 将branch_name参数从必需改为可选，默认值为"master" 
- **新功能**:
  - 无参数调用时自动使用master分支
  - 添加了 `-h` 和 `--help` 选项显示详细使用说明
  - 改进的参数处理逻辑

### 3. deploy_to_github_en.bat (Windows英文版本)
- **主要变更**: 将branch_name参数从必需改为可选，默认值为"master"
- **新功能**:
  - 无参数调用时自动使用master分支  
  - 添加了 `-h` 和 `--help` 选项显示详细使用说明
  - 改进的参数处理逻辑

## 使用方法变更

### 旧版本使用方法（必需参数）
```bash
# Linux/macOS
./deploy_to_github.sh <branch_name> [commit_message]

# Windows
deploy_to_github.bat <branch_name> [commit_message]
```

### 新版本使用方法（可选参数）
```bash
# Linux/macOS
./deploy_to_github.sh [branch_name] [commit_message]

# Windows PowerShell (推荐)
.\deploy_to_github.bat [branch_name] [commit_message]
.\deploy_to_github_en.bat [branch_name] [commit_message]

# Windows Command Prompt (cmd)
deploy_to_github.bat [branch_name] [commit_message]
deploy_to_github_en.bat [branch_name] [commit_message]
```

## 使用示例

### 基本用法（新增）
```bash
# Linux/macOS - 直接运行，默认提交到master分支
./deploy_to_github.sh

# Windows PowerShell - 需要 .\ 前缀
.\deploy_to_github.bat
.\deploy_to_github_en.bat

# Windows Command Prompt (cmd) - 无需前缀
deploy_to_github.bat
deploy_to_github_en.bat
```

### 指定分支
```bash
# Linux/macOS
./deploy_to_github.sh develop

# Windows PowerShell
.\deploy_to_github.bat develop
.\deploy_to_github_en.bat develop

# Windows Command Prompt
deploy_to_github.bat develop
deploy_to_github_en.bat develop
```

### 自定义提交信息
```bash
# Linux/macOS
./deploy_to_github.sh master "新功能：统一导航栏"

# Windows PowerShell  
.\deploy_to_github.bat master "新功能：统一导航栏"
.\deploy_to_github_en.bat master "Feature: unified navigation"

# Windows Command Prompt
deploy_to_github.bat master "新功能：统一导航栏" 
deploy_to_github_en.bat master "Feature: unified navigation"
```

### 查看帮助
```bash
# Linux/macOS
./deploy_to_github.sh --help

# Windows PowerShell
.\deploy_to_github.bat -h
.\deploy_to_github_en.bat --help

# Windows Command Prompt  
deploy_to_github.bat -h
deploy_to_github_en.bat --help
```

## 功能特性

### 保持的原有功能
- 自动检查Git配置和仓库状态
- 智能分支切换（如果目标分支不存在会自动创建）
- 排除数据库文件和临时文件的提交
- 详细的操作日志和部署报告
- 错误处理和回滚机制

### 新增功能
- **默认分支**: 无参数时自动使用master分支
- **帮助系统**: 支持 `-h` 和 `--help` 参数
- **更灵活的参数处理**: 所有参数都是可选的
- **向后兼容**: 旧的使用方式仍然有效

## 技术实现

### Shell脚本 (deploy_to_github.sh)
```bash
# 使用参数替换设置默认值
BRANCH_NAME=${1:-"master"}
COMMIT_MESSAGE=${2:-"Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"}
```

### Windows批处理 (deploy_to_github.bat & deploy_to_github_en.bat)
```batch
:: 条件判断设置默认分支
if "%~1"=="" (
    set "BRANCH_NAME=master"
) else (
    set "BRANCH_NAME=%~1"
)
```

## 测试结果

### 功能验证
- ✅ 无参数调用默认使用master分支
- ✅ 帮助信息正确显示（英文版）
- ✅ 向后兼容性保持
- ⚠️ 中文版在某些终端存在编码显示问题（功能正常）

### 建议
- 在Windows环境下推荐使用 `deploy_to_github_en.bat` 避免编码问题
- Linux/macOS环境下使用 `deploy_to_github.sh`

## 更新日期
2025-09-03

## 版本兼容性
- Git 2.x+
- Windows 10/11
- Linux/macOS with Bash 4.0+

## 注意事项
1. 首次使用前确保已配置Git用户信息
2. 确保有远程仓库的推送权限
3. 建议在推送前检查暂存区内容
4. 数据库文件(.db)和日志文件(.log)会被自动排除
