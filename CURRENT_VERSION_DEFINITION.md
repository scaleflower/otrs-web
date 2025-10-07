# 当前版本号定义位置

## 版本号定义位置

### 1. 主要定义位置

**配置文件 (`config/base.py`)**:
```python
APP_VERSION = "1.2.3"
```
这是版本号的**主要定义位置**，硬编码在配置文件中。

### 2. 版本号使用流程

#### 2.1 应用启动时
```python
# app.py
APP_VERSION = app.config.get('APP_VERSION', '1.2.3')
```

#### 2.2 数据库初始化
```python
# models/__init__.py
initial_version = app.config.get('APP_VERSION', '0.0.0')
update_status = AppUpdateStatus(current_version=initial_version)
```

#### 2.3 前端显示
```html
<!-- 所有模板文件 -->
<p>OTRS Ticket Analysis System v{{ APP_VERSION }} | © 2025</p>
```

#### 2.4 更新服务
```python
# services/update_service.py
current_version = status.current_version or '0.0.0'
```

### 3. 版本号存储位置

#### 3.1 配置文件 (静态)
- **文件**: `config/base.py`
- **键名**: `APP_VERSION`
- **值**: `"1.2.3"`
- **类型**: 硬编码字符串

#### 3.2 数据库 (动态)
- **表名**: `app_update_status`
- **字段**: `current_version`
- **初始值**: 从配置文件读取
- **更新**: 成功更新后自动更新

### 4. 版本号获取优先级

1. **数据库存储** (`app_update_status.current_version`)
2. **配置文件** (`config.base.APP_VERSION`)
3. **默认值** (`'0.0.0'`)

### 5. 版本号更新流程

```python
# 更新成功后
status.current_version = target_version  # 更新数据库中的版本号
db.session.commit()
```

### 6. 当前实现的问题

#### 6.1 硬编码版本号
版本号硬编码在配置文件中，需要手动修改：
```python
# config/base.py
APP_VERSION = "1.2.3"  # 需要手动更新
```

#### 6.2 版本号不一致风险
- 配置文件版本号可能与数据库存储的版本号不同步
- 手动修改配置文件容易出错

### 7. 建议的改进方案

#### 7.1 动态版本号获取
```python
def get_dynamic_version():
    """动态获取版本号"""
    # 1. 从git标签获取
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

#### 7.2 版本文件方案
创建 `VERSION` 文件：
```
1.2.3
```

#### 7.3 环境变量方案
```bash
# .env
APP_VERSION=1.2.3
```

### 8. 当前配置总结

| 位置 | 类型 | 值 | 更新方式 |
|------|------|-----|----------|
| `config/base.py` | 硬编码 | `"1.2.3"` | 手动修改代码 |
| `.env` | 环境变量 | 未设置 | 可配置 |
| 数据库 | 动态存储 | 从配置初始化 | 自动更新 |

### 9. 修改版本号的步骤

#### 当前方式
1. 编辑 `config/base.py`
2. 修改 `APP_VERSION = "新版本号"`
3. 重启应用

#### 建议方式
1. 编辑 `VERSION` 文件或环境变量
2. 版本号自动同步到数据库
3. 无需重启应用（部分情况）

### 10. 测试当前版本号

```bash
# 测试版本号获取
python3 test_update_functionality.py

# 查看数据库中的版本号
sqlite3 db/otrs_data.db "SELECT current_version FROM app_update_status;"
```

当前版本号系统工作正常，但建议采用更动态的版本管理方式以提高维护性。
