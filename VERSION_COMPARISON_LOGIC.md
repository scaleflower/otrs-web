# 版本号判断和GitHub Release对比逻辑

## 当前版本号判断机制

### 1. 版本号来源
当前应用通过两种方式确定版本号：

**配置文件中定义** (`config/base.py`):
```python
APP_VERSION = "1.2.3"
```

**数据库存储** (`AppUpdateStatus` 表):
- `current_version`: 当前运行的版本号
- `latest_version`: 检测到的最新GitHub release版本号

### 2. 版本号初始化流程
1. **应用启动时**: 从配置文件读取 `APP_VERSION`
2. **数据库初始化**: 如果 `AppUpdateStatus` 表为空，创建记录并设置 `current_version = APP_VERSION`
3. **更新成功后**: `current_version` 更新为最新版本

### 3. 获取当前版本号的API
```python
# 在 UpdateService.get_status() 中
status = AppUpdateStatus.query.first()
if not status:
    return {'current_version': self._config('APP_VERSION', '0.0.0')}
else:
    return status.to_dict()
```

## GitHub Release检测机制

### 1. 仓库配置
通过环境变量或配置文件指定GitHub仓库：
```python
APP_UPDATE_REPO = os.environ.get('APP_UPDATE_REPO', 'Jacky/otrs-web')
```

### 2. API调用流程
```python
def check_for_updates(self, force=False):
    # 1. 构建GitHub API URL
    repo = self._config('APP_UPDATE_REPO')  # 例如: "Jacky/otrs-web"
    url = f'https://api.github.com/repos/{repo}/releases/latest'
    
    # 2. 发送HTTP请求
    response = requests.get(url, headers=headers, timeout=10)
    
    # 3. 解析响应
    if response.status_code == 200:
        payload = response.json()
        latest_version = payload.get('tag_name') or payload.get('name')
```

### 3. 版本对比逻辑
```python
current_version = status.current_version or '0.0.0'
if latest_version != current_version:
    status.status = 'update_available'
else:
    status.status = 'up_to_date'
```

## 关键问题和改进建议

### 1. 当前实现的问题

**版本号对比过于简单**:
- 仅使用字符串相等比较 `latest_version != current_version`
- 无法正确处理语义化版本号 (如 `1.2.3` vs `1.2.4`)

**版本号来源不一致**:
- 配置文件中硬编码 `APP_VERSION = "1.2.3"`
- 数据库存储的版本号可能不同步

### 2. 建议的改进方案

#### 2.1 语义化版本号对比
```python
import re
from packaging import version

def compare_versions(current, latest):
    """比较语义化版本号"""
    try:
        current_ver = version.parse(current)
        latest_ver = version.parse(latest)
        return latest_ver > current_ver
    except:
        # 回退到字符串比较
        return latest != current
```

#### 2.2 动态版本号管理
```python
# 从git标签或文件读取版本号
def get_current_version():
    """动态获取当前版本号"""
    # 1. 尝试从git标签获取
    try:
        result = subprocess.run(['git', 'describe', '--tags'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # 2. 从版本文件读取
    version_file = Path(__file__).parent / 'VERSION'
    if version_file.exists():
        return version_file.read_text().strip()
    
    # 3. 回退到配置
    return current_app.config.get('APP_VERSION', '0.0.0')
```

#### 2.3 增强的GitHub API处理
```python
def get_latest_release_info(repo, token=None):
    """获取GitHub release信息，支持分页和错误处理"""
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'otrs-web-update-service'
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # 获取所有release，按发布时间排序
    url = f'https://api.github.com/repos/{repo}/releases'
    params = {'per_page': 10, 'page': 1}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            releases = response.json()
            if releases:
                # 返回最新的release
                latest = releases[0]
                return {
                    'tag_name': latest.get('tag_name'),
                    'name': latest.get('name'),
                    'body': latest.get('body'),
                    'html_url': latest.get('html_url'),
                    'published_at': latest.get('published_at'),
                    'prerelease': latest.get('prerelease', False)
                }
    except requests.RequestException as e:
        logger.error(f"GitHub API请求失败: {e}")
    
    return None
```

## 实际工作流程示例

### 场景1: 检测到新版本
1. 当前版本: `1.2.3` (数据库 `current_version`)
2. GitHub最新release: `1.2.4` (从API获取的 `tag_name`)
3. 对比结果: `1.2.4 != 1.2.3` → 状态设为 `update_available`

### 场景2: 版本相同
1. 当前版本: `1.2.3`
2. GitHub最新release: `1.2.3`
3. 对比结果: `1.2.3 == 1.2.3` → 状态设为 `up_to_date`

### 场景3: 版本格式不同
1. 当前版本: `v1.2.3`
2. GitHub最新release: `1.2.3`
3. 当前逻辑: `v1.2.3 != 1.2.3` → 错误地认为需要更新

## 配置说明

### 环境变量
```bash
# GitHub仓库 (格式: owner/repo)
APP_UPDATE_REPO=Jacky/otrs-web

# 当前版本号 (可选，默认从配置文件读取)
APP_VERSION=1.2.3

# GitHub Token (用于私有仓库或提高API限制)
APP_UPDATE_GITHUB_TOKEN=ghp_xxx

# 检测间隔 (秒)
APP_UPDATE_POLL_INTERVAL=3600
```

### 当前限制
1. **版本号格式**: 必须与GitHub release的 `tag_name` 完全匹配
2. **仓库权限**: 需要公开仓库或提供GitHub Token
3. **网络依赖**: 需要能够访问GitHub API

## 测试建议

使用以下命令测试版本检测功能:
```bash
# 测试当前版本获取
python3 test_update_functionality.py

# 手动测试GitHub API
curl -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/Jacky/otrs-web/releases/latest
```

通过改进版本对比逻辑和错误处理，可以构建更健壮的自动更新系统。
