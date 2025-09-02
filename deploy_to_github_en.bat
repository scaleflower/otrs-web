@echo off
setlocal enabledelayedexpansion

:: ================================================================================
:: OTRS Web Application - GitHub Deployment Script (Windows Version)
:: Function: Automatically commit all changes and push to specified GitHub branch
:: Usage: deploy_to_github_en.bat [branch_name] [commit_message]
:: Example: deploy_to_github_en.bat master "New feature: incremental import and stats fix"
:: ================================================================================

:: Check for help parameters first
if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help

:: Set default branch name to master if no parameter provided
if "%~1"=="" (
    set "BRANCH_NAME=master"
) else (
    set "BRANCH_NAME=%~1"
)

goto :main

:show_help
echo Usage: %0 [branch_name] [commit_message]
echo [INFO] Parameter description:
echo [INFO]   branch_name    : Target branch name (optional, defaults to master)
echo [INFO]   commit_message : Commit message (optional, defaults to timestamp)
echo [INFO]
echo [INFO] Examples:
echo [INFO]   %0                           # Commit to master branch, use default commit message
echo [INFO]   %0 master                    # Commit to master branch, use default commit message
echo [INFO]   %0 develop                   # Commit to develop branch
echo [INFO]   %0 master "New feature"      # Commit to master branch, custom commit message
echo [INFO]   %0 develop "Bug fix"         # Commit to develop branch, custom commit message
exit /b 0

:main
if "%~2"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "current_date=%%c-%%a-%%b"
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "current_time=%%a:%%b"
    set "COMMIT_MESSAGE=Auto commit: !current_date! !current_time!"
) else (
    set "COMMIT_MESSAGE=%~2"
)

echo [INFO] Starting deployment to GitHub...
echo [INFO] Target branch: %BRANCH_NAME%
echo [INFO] Commit message: %COMMIT_MESSAGE%

:: Check if in git repository
if not exist ".git" (
    echo [ERROR] Current directory is not a git repository!
    exit /b 1
)

:: Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH!
    exit /b 1
)

:: Check git configuration
git config user.name >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git user configuration not set! Please configure:
    echo git config user.name "Your Name"
    echo git config user.email "your.email@example.com"
    exit /b 1
)

git config user.email >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git email configuration not set! Please configure:
    echo git config user.email "your.email@example.com"
    exit /b 1
)

:: Check remote repository
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Remote repository 'origin' not found!
    exit /b 1
)

echo [INFO] Git configuration check passed...

:: Check current branch
for /f "tokens=*" %%i in ('git branch --show-current') do set "current_branch=%%i"
echo [INFO] Current branch: %current_branch%

:: Switch to target branch if different
if not "%current_branch%"=="%BRANCH_NAME%" (
    echo [WARNING] Current branch ^(%current_branch%^) differs from target branch ^(%BRANCH_NAME%^)
    
    :: Check if target branch exists
    git show-ref --verify --quiet refs/heads/%BRANCH_NAME% >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Creating and switching to new branch: %BRANCH_NAME%
        git checkout -b %BRANCH_NAME%
    ) else (
        echo [INFO] Switching to existing branch: %BRANCH_NAME%
        git checkout %BRANCH_NAME%
    )
    
    if errorlevel 1 (
        echo [ERROR] Branch switching failed!
        exit /b 1
    )
)

:: Pull latest changes if branch exists on remote
git ls-remote --heads origin %BRANCH_NAME% | findstr %BRANCH_NAME% >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Pulling latest changes from remote branch...
    git pull origin %BRANCH_NAME%
    if errorlevel 1 (
        echo [WARNING] Failed to pull remote changes, continuing...
    )
)

:: Show current status
echo [INFO] Checking Git status...
git status --porcelain

:: Add all changes, excluding specific temporary files
echo [INFO] Adding files to staging area...

:: Add all files
git add .

:: Exclude temporary files (keep database files)
git reset HEAD -- "logs/*.log" "__pycache__/" "*.pyc" ".DS_Store" "Thumbs.db" >nul 2>&1

:: Warning: including database files
git ls-files --cached | findstr /R "\.db$ \.sqlite$ \.sqlite3$" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Database files detected and will be committed to GitHub!
    echo [WARNING] Ensure database files do not contain sensitive data.
)

:: Show files to be committed
echo [INFO] Files to be committed:
git diff --cached --name-status

:: Check if there are files to commit
git diff --cached --quiet
if not errorlevel 1 (
    echo [WARNING] No changes to commit!
    exit /b 0
)

:: Commit changes
echo [INFO] Committing changes...
git commit -m "%COMMIT_MESSAGE%"

if errorlevel 1 (
    echo [ERROR] Commit failed!
    exit /b 1
)

echo [SUCCESS] Commit successful!

:: Push to remote repository
echo [INFO] Pushing to remote repository origin/%BRANCH_NAME%...
git push origin %BRANCH_NAME%

if errorlevel 1 (
    echo [ERROR] Push failed! Please check network connection and permissions.
    exit /b 1
)

echo [SUCCESS] Push successful!

:: Show latest commit information
echo [INFO] Latest commit information:
git log --oneline -1

:: Show remote repository URL
for /f "tokens=*" %%i in ('git remote get-url origin') do set "remote_url=%%i"
echo [SUCCESS] Deployment completed!
echo [INFO] Remote repository: %remote_url%
echo [INFO] Branch: %BRANCH_NAME%

:: Get commit hash
for /f "tokens=*" %%i in ('git rev-parse HEAD') do set "commit_hash=%%i"
echo [INFO] Commit hash: %commit_hash%

:: Generate deployment report
echo.
echo ==========================================
echo           Deployment Report
echo ==========================================
echo Time: %date% %time%
echo Branch: %BRANCH_NAME%
for /f "tokens=*" %%i in ('git log --oneline -1') do echo Commit: %%i
echo Repository: %remote_url%
for /f "tokens=*" %%i in ('git config user.name') do set "git_name=%%i"
for /f "tokens=*" %%i in ('git config user.email') do set "git_email=%%i"
echo Operator: %git_name% ^<%git_email%^>
echo ==========================================

endlocal
