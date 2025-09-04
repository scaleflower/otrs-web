# OTRS Web 安全配置指南

## 🔐 自定义每日统计密码

### 方法一：使用环境变量（推荐）

#### Windows 系统

**临时设置（仅在当前会话有效）：**
```cmd
# 在命令提示符中
set DAILY_STATS_PASSWORD=MySecurePassword123!
python app.py

# 在PowerShell中
$env:DAILY_STATS_PASSWORD="MySecurePassword123!"
python app.py
```

**永久设置：**
```cmd
# 使用系统环境变量设置
setx DAILY_STATS_PASSWORD "MySecurePassword123!"
# 注意：需要重启命令提示符才能生效
```

#### Linux/macOS 系统

**临时设置：**
```bash
export DAILY_STATS_PASSWORD="MySecurePassword123!"
python app.py
```

**永久设置：**
```bash
# 添加到 ~/.bashrc 或 ~/.profile
echo 'export DAILY_STATS_PASSWORD="MySecurePassword123!"' >> ~/.bashrc
source ~/.bashrc
```

### 方法二：使用 .env 文件

1. 在项目根目录创建 `.env` 文件：
```bash
# .env 文件内容
DAILY_STATS_PASSWORD=MySecurePassword123!
SECRET_KEY=your-super-secret-key-for-production
```

2. 安装 python-dotenv 包：
```bash
pip install python-dotenv
```

3. 在 `app.py` 开头添加：
```python
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件中的环境变量
```

### 方法三：Docker 部署

**docker-compose.yml 示例：**
```yaml
version: '3.8'
services:
  otrs-web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DAILY_STATS_PASSWORD=MySecurePassword123!
      - SECRET_KEY=your-production-secret-key
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
```

**Docker 命令行：**
```bash
docker run -e DAILY_STATS_PASSWORD="MySecurePassword123!" -p 5000:5000 otrs-web
```

### 方法四：修改配置文件（不推荐）

直接修改 `config/base.py`：
```python
# 在 config/base.py 中
DAILY_STATS_PASSWORD = 'MySecurePassword123!'  # 直接硬编码，不推荐
```

**注意：** 此方法不推荐，因为密码会被提交到版本控制系统中。

## 📝 密码要求和建议

### 推荐的密码格式
- 长度至少8位
- 包含大小写字母、数字和特殊字符
- 避免使用常见密码

### 示例密码
```
MySecure123!         # 简单安全
Admin@2025$          # 包含年份
OtrsWeb#Secure789    # 项目相关
P@ssw0rd2025!        # 经典格式
```

## 🛡️ 安全最佳实践

### 1. 生产环境配置
```bash
# 生产环境环境变量示例
export DAILY_STATS_PASSWORD="Complex$Password123!"
export SECRET_KEY="your-very-long-random-secret-key"
export FLASK_ENV="production"
```

### 2. 权限管理
- 确保 `.env` 文件权限设置为仅所有者可读：
```bash
chmod 600 .env
```

### 3. 版本控制
在 `.gitignore` 中添加：
```
.env
*.env
config/local.py
```

## 🔄 验证配置

### 检查当前密码设置
创建测试脚本 `check_password.py`：
```python
import os

# 检查密码设置
password = os.environ.get('DAILY_STATS_PASSWORD', 'Enabling@2025')
print(f"当前使用的密码: {password}")

if password == 'Enabling@2025':
    print("状态: 使用默认密码")
else:
    print("状态: 使用自定义密码 ✅")
```

### 测试环境变量
```bash
# 设置环境变量
export DAILY_STATS_PASSWORD="TestPassword123"

# 运行检查脚本
python check_password.py

# 输出示例：
# 当前密码: TestPassword123
# 密码来源: 环境变量
```

## 📋 快速设置步骤

### 开发环境快速设置

1. **创建 .env 文件：**
```bash
echo "DAILY_STATS_PASSWORD=MyDevPassword123!" > .env
```

2. **修改 app.py 加载环境变量：**
```python
# 在 app.py 顶部添加
from dotenv import load_dotenv
load_dotenv()
```

3. **启动应用：**
```bash
python app.py
```

4. **测试密码：**
   - 访问 http://localhost:5000/daily-statistics
   - 尝试保存配置，输入 `MyDevPassword123!`

### 生产环境快速设置

```bash
# 设置环境变量
export DAILY_STATS_PASSWORD="YourProductionPassword123!"
export SECRET_KEY="your-production-secret-key"

# 启动应用
python app.py
```

## ❓ 常见问题

### Q: 环境变量设置后不生效？
A: 确保重启了应用程序，环境变量在程序启动时读取。

### Q: 忘记了自定义密码？
A: 检查环境变量或 .env 文件，或者临时移除环境变量使用默认密码 `Enabling@2025`。

### Q: 可以动态修改密码吗？
A: 当前需要重启应用才能生效，密码在启动时读取。

## 🔧 故障排除

### 检查环境变量是否设置成功
```python
import os
print("DAILY_STATS_PASSWORD:", os.environ.get('DAILY_STATS_PASSWORD', '未设置'))
```

### 临时重置为默认密码
```bash
unset DAILY_STATS_PASSWORD  # Linux/macOS
set DAILY_STATS_PASSWORD=   # Windows cmd
