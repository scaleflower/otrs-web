# OTRS Web Application

基于Flask的OTRS工单数据分析Web应用，旨在提供美观界面和丰富的统计分析功能，帮助用户可视化和管理OTRS工单数据。

## 功能特性

- 数据可视化：使用图表展示工单统计数据
- 文件上传：支持Excel文件上传和解析
- 多维度分析：包括优先级、状态、责任人、每日统计等
- 数据导出：支持Excel和文本格式报告导出
- 自动更新：GitHub发布新版本时自动通知并支持一键更新
- 数据库监控：实时监控数据库状态

## 环境要求

- Python 3.6+
- Docker (可选，推荐)
- 数据库（SQLite或PostgreSQL）

## 安装和部署

### 方法1：使用Docker（推荐）

#### 使用PostgreSQL数据库（推荐用于生产环境）

```bash
docker-compose up -d
```

#### 使用SQLite数据库

```bash
docker-compose -f docker-compose.sqlite.yml up -d
```

### 方法2：本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python app.py
```

或者使用gunicorn（生产环境）：
```bash
gunicorn -w 4 -b 0.0.0.0:15001 --access-logfile - --error-logfile - app:app
```

## 数据库配置

应用支持两种数据库：

### SQLite（默认）
- 适用于开发和小型部署
- 数据存储在本地文件中
- 无需额外配置数据库服务

### PostgreSQL（推荐用于生产环境）
- 更好的性能和可靠性
- 支持并发访问
- 需要单独的数据库服务

通过设置环境变量 `DATABASE_TYPE` 来选择数据库类型：
- `DATABASE_TYPE=sqlite` 使用SQLite
- `DATABASE_TYPE=postgresql` 使用PostgreSQL

PostgreSQL相关配置：
- `DB_HOST`: 数据库主机地址
- `DB_PORT`: 数据库端口（默认5432）
- `DB_NAME`: 数据库名称
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码

## 数据库初始化

### 使用Docker（推荐）

当使用Docker运行应用时，数据库会在应用启动时自动初始化。

### 手动初始化数据库

如果需要手动初始化数据库（特别是PostgreSQL），可以使用以下方法：

#### 方法1：使用Flask Shell
```bash
flask shell
>>> from app import app
>>> from models import init_db
>>> with app.app_context():
...     init_db(app)
```

#### 方法2：运行初始化脚本
```bash
python init_postgres_db.py
```

该脚本会根据环境变量配置连接到相应的数据库并创建所有必要的表。

## 目录结构

- `uploads/`: 上传的Excel文件存储目录
- `logs/`: 应用日志目录
- `database_backups/`: 数据库备份目录
- `db/`: SQLite数据库文件目录（仅SQLite模式使用）

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| FLASK_ENV | development | 运行环境（development/production） |
| PORT | 15001 | 应用监听端口 |
| DATABASE_TYPE | sqlite | 数据库类型（sqlite/postgresql） |
| DB_HOST | localhost | PostgreSQL主机地址 |
| DB_PORT | 5432 | PostgreSQL端口 |
| DB_NAME | otrs_db | PostgreSQL数据库名 |
| DB_USER | otrs_user | PostgreSQL用户名 |
| DB_PASSWORD |  | PostgreSQL密码 |

## 访问应用

启动后访问 `http://localhost:15001`

## 自动更新

应用支持自动更新功能，当GitHub上有新版本发布时会自动检测并提示更新。

更新时会保留以下路径的文件：
- `.env`
- `uploads/`
- `database_backups/`
- `logs/`
- `db/otrs_data.db`（仅SQLite模式）

## 故障排除

1. 如果遇到端口冲突，请修改docker-compose.yml中的端口映射
2. 如果数据库连接失败，请检查数据库配置和网络连接
3. 如果上传文件失败，请检查文件格式和大小限制