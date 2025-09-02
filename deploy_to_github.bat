@echo off
setlocal enabledelayedexpansion

:: ================================================================================
:: OTRS Web Application - GitHub部署脚本 (Windows版本)
:: 功能：自动提交所有更改并推送到指定GitHub分支
:: 用法：deploy_to_github.bat <branch_name> [commit_message]
:: 示例：deploy_to_github.bat master "新功能：增量导入和统计修复"
:: ================================================================================

:: 颜色定义 (Windows下使用echo命令显示信息)
set "INFO_COLOR=[INFO]"
set "SUCCESS_COLOR=[SUCCESS]"
set "WARNING_COLOR=[WARNING]"
set "ERROR_COLOR=[ERROR]"

:: 检查参数
if "%~1"=="" (
    echo %ERROR_COLOR% 使用方法: %0 ^<branch_name^> [commit_message]
    echo %INFO_COLOR% 示例: %0 master "新功能实现"
    echo %INFO_COLOR% 示例: %0 develop "修复bug"
    exit /b 1
)

set "BRANCH_NAME=%~1"
if "%~2"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "current_date=%%c-%%a-%%b"
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "current_time=%%a:%%b"
    set "COMMIT_MESSAGE=Auto commit: !current_date! !current_time!"
) else (
    set "COMMIT_MESSAGE=%~2"
)

echo %INFO_COLOR% 开始部署到GitHub...
echo %INFO_COLOR% 目标分支: %BRANCH_NAME%
echo %INFO_COLOR% 提交信息: %COMMIT_MESSAGE%

:: 检查是否在git仓库中
if not exist ".git" (
    echo %ERROR_COLOR% 当前目录不是git仓库！
    exit /b 1
)

:: 检查git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_COLOR% Git未安装或不在PATH中！
    exit /b 1
)

:: 检查git配置
git config user.name >nul 2>&1
if errorlevel 1 (
    echo %ERROR_COLOR% Git用户配置未设置！请先配置：
    echo git config user.name "Your Name"
    echo git config user.email "your.email@example.com"
    exit /b 1
)

git config user.email >nul 2>&1
if errorlevel 1 (
    echo %ERROR_COLOR% Git邮箱配置未设置！请先配置：
    echo git config user.email "your.email@example.com"
    exit /b 1
)

:: 检查远程仓库
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo %ERROR_COLOR% 未找到远程仓库origin！
    exit /b 1
)

echo %INFO_COLOR% Git配置检查通过...

:: 检查当前分支
for /f "tokens=*" %%i in ('git branch --show-current') do set "current_branch=%%i"
echo %INFO_COLOR% 当前分支: %current_branch%

:: 如果目标分支不是当前分支，进行切换
if not "%current_branch%"=="%BRANCH_NAME%" (
    echo %WARNING_COLOR% 当前分支 ^(%current_branch%^) 与目标分支 ^(%BRANCH_NAME%^) 不同
    
    :: 检查目标分支是否存在
    git show-ref --verify --quiet refs/heads/%BRANCH_NAME% >nul 2>&1
    if errorlevel 1 (
        echo %INFO_COLOR% 创建并切换到新分支: %BRANCH_NAME%
        git checkout -b %BRANCH_NAME%
    ) else (
        echo %INFO_COLOR% 切换到现有分支: %BRANCH_NAME%
        git checkout %BRANCH_NAME%
    )
    
    if errorlevel 1 (
        echo %ERROR_COLOR% 分支切换失败！
        exit /b 1
    )
)

:: 拉取最新更改（如果分支存在于远程）
git ls-remote --heads origin %BRANCH_NAME% | findstr %BRANCH_NAME% >nul 2>&1
if not errorlevel 1 (
    echo %INFO_COLOR% 拉取远程分支最新更改...
    git pull origin %BRANCH_NAME%
    if errorlevel 1 (
        echo %WARNING_COLOR% 拉取远程更改失败，继续执行...
    )
)

:: 显示当前状态
echo %INFO_COLOR% 检查Git状态...
git status --porcelain

:: 添加所有更改，但排除特定文件
echo %INFO_COLOR% 添加文件到暂存区...

:: 添加所有文件
git add .

:: 排除数据库文件和临时文件
git reset HEAD -- "*.db" "db/*.db" "instance/*.db" "logs/*.log" "__pycache__/" "*.pyc" ".DS_Store" "Thumbs.db" >nul 2>&1

:: 显示即将提交的文件
echo %INFO_COLOR% 即将提交的文件：
git diff --cached --name-status

:: 检查是否有文件要提交
git diff --cached --quiet
if not errorlevel 1 (
    echo %WARNING_COLOR% 没有更改需要提交！
    exit /b 0
)

:: 提交更改
echo %INFO_COLOR% 提交更改...
git commit -m "%COMMIT_MESSAGE%"

if errorlevel 1 (
    echo %ERROR_COLOR% 提交失败！
    exit /b 1
)

echo %SUCCESS_COLOR% 提交成功！

:: 推送到远程仓库
echo %INFO_COLOR% 推送到远程仓库 origin/%BRANCH_NAME%...
git push origin %BRANCH_NAME%

if errorlevel 1 (
    echo %ERROR_COLOR% 推送失败！请检查网络连接和权限。
    exit /b 1
)

echo %SUCCESS_COLOR% 推送成功！

:: 显示最新提交信息
echo %INFO_COLOR% 最新提交信息：
git log --oneline -1

:: 显示远程仓库URL
for /f "tokens=*" %%i in ('git remote get-url origin') do set "remote_url=%%i"
echo %SUCCESS_COLOR% 部署完成！
echo %INFO_COLOR% 远程仓库: %remote_url%
echo %INFO_COLOR% 分支: %BRANCH_NAME%

:: 获取提交哈希
for /f "tokens=*" %%i in ('git rev-parse HEAD') do set "commit_hash=%%i"
echo %INFO_COLOR% 提交哈希: %commit_hash%

:: 生成部署报告
echo.
echo ==========================================
echo            部署报告
echo ==========================================
echo 时间: %date% %time%
echo 分支: %BRANCH_NAME%
for /f "tokens=*" %%i in ('git log --oneline -1') do echo 提交: %%i
echo 仓库: %remote_url%
for /f "tokens=*" %%i in ('git config user.name') do set "git_name=%%i"
for /f "tokens=*" %%i in ('git config user.email') do set "git_email=%%i"
echo 操作员: %git_name% ^<%git_email%^>
echo ==========================================

endlocal
