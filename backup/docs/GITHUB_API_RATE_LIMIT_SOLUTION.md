# GitHub API 速率限制解决方案

## 问题描述
GitHub API 对未认证的请求有严格的速率限制：
- **未认证请求**: 60 次/小时
- **认证请求**: 5000 次/小时

## 解决方案

### 方法1: 创建GitHub Personal Access Token

#### 步骤1: 创建Token
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置Token名称，如 "OTRS Web Update"
4. **权限设置**: 只需要 `public_repo` 权限（只读访问公共仓库）
5. 点击 "Generate token"
6. **重要**: 立即复制生成的Token，它只会显示一次

#### 步骤2: 配置Token到应用
在 `.env` 文件中添加：

```bash
# GitHub Personal Access Token for API rate limit
APP_UPDATE_GITHUB_TOKEN=ghp_your_token_here
```

### 方法2: 使用GitHub App Token (推荐用于生产环境)

#### 步骤1: 创建GitHub App
1. 访问 https://github.com/settings/apps
2. 点击 "New GitHub App"
3. 填写基本信息：
   - GitHub App name: `otrs-web-updater`
   - Homepage URL: 您的应用URL
   - Webhook: 可选，不需要
4. **权限设置**: Repository permissions → Metadata: Read-only
5. 点击 "Create GitHub App"

#### 步骤2: 生成App Token
1. 在App设置页面，点击 "Generate a private key"
2. 下载私钥文件
3. 使用JWT库生成Token

### 方法3: 缓存机制（临时解决方案）

在 `services/update_service.py` 中添加缓存：

```python
import time

# 添加缓存变量
_last_check_time = 0
_cached_result = None
_CACHE_DURATION = 300  # 5分钟缓存

def check_for_updates(self):
    """Manually check for updates from GitHub with caching"""
    global _last_check_time, _cached_result
    
    # 检查缓存
    current_time = time.time()
    if _cached_result and (current_time - _last_check_time) < _CACHE_DURATION:
        return _cached_result
    
    # 原有检查逻辑...
    result = self._do_github_check()
    
    # 缓存结果
    if result.get('success'):
        _cached_result = result
        _last_check_time = current_time
    
    return result
```

## 推荐的完整解决方案

### 1. 立即实施：添加GitHub Token
在 `.env` 文件中配置：

```bash
# GitHub Personal Access Token
APP_UPDATE_GITHUB_TOKEN=ghp_your_actual_token_here
```

### 2. 增强错误处理
在 `services/update_service.py` 中改进错误处理：

```python
def check_for_updates(self):
    """Manually check for updates from GitHub Releases"""
    if not self._config('APP_UPDATE_ENABLED', True):
        return {'success': False, 'error': 'Auto-update disabled'}

    with self._ensure_app_context():
        repo = self._config('APP_UPDATE_REPO')
        token = self._config('APP_UPDATE_GITHUB_TOKEN')
        
        # 检查是否有Token
        if not token:
            return {
                'success': False, 
                'error': 'GitHub Token未配置，请设置APP_UPDATE_GITHUB_TOKEN环境变量',
                'help_url': 'https://github.com/settings/tokens'
            }
        
        headers = {
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'otrs-web-update-service',
            'Authorization': f'Bearer {token}'
        }

        # 其余代码保持不变...
```

### 3. 前端错误提示改进
在 `static/js/script.js` 中改进错误处理：

```javascript
// 在 handleManualUpdateCheck 函数中改进错误处理
if (!response.ok || !data.success) {
    let errorMessage = data.error || '检查更新失败';
    
    // 特殊处理速率限制错误
    if (errorMessage.includes('rate limit exceeded')) {
        errorMessage = 'GitHub API 速率限制，请稍后再试或配置GitHub Token';
    } else if (errorMessage.includes('GitHub Token未配置')) {
        errorMessage = 'GitHub Token未配置，请联系管理员设置APP_UPDATE_GITHUB_TOKEN';
    }
    
    throw new Error(errorMessage);
}
```

## 验证配置

创建验证脚本：

```python
# test_github_token.py
import os
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get('APP_UPDATE_GITHUB_TOKEN')
if token:
    print(f"✅ GitHub Token已配置: {token[:10]}...")
else:
    print("❌ GitHub Token未配置")
    print("💡 请在 .env 文件中设置 APP_UPDATE_GITHUB_TOKEN")
```

## 生产环境建议

1. **使用环境变量**: 不要在代码中硬编码Token
2. **定期轮换**: 定期更新Token
3. **最小权限**: 只授予必要的权限
4. **监控使用**: 监控API使用情况
5. **备用方案**: 考虑使用GitHub App替代Personal Token

配置GitHub Token后，API限制将从60次/小时提升到5000次/小时，完全满足应用需求。
