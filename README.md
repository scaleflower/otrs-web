# OTRS工单数据分析Web应用

基于Flask的OTRS工单数据分析Web应用，提供美观的界面和丰富的统计分析功能。

## 功能特性

- 📊 **数据可视化**: 精美的图表展示工单统计数据
- 📈 **多种分析**: 优先级分布、状态分布、每日统计等
- 💾 **文件上传**: 支持Excel文件上传和分析
- 📥 **导出功能**: 支持导出Excel和文本格式报告
- 🎨 **美观界面**: 现代化的响应式设计
- 📱 **移动友好**: 支持各种设备屏幕尺寸
- 👥 **责任人分析**: 按责任人分组统计分析
- 📅 **每日统计**: 自动计算每日工单统计数据
- 🔄 **实时监控**: 数据库状态实时监控
- 📋 **详细报告**: 多维度详细分析报告
- 🚀 **自动更新提醒**: GitHub 发布新版本时自动通知并支持一键更新

## 完整功能列表

### 📄 主要页面

1. **首页 (index.html)** - `/`
   - 文件上传功能 (Excel文件)
   - 数据分析选项 (清除现有数据或增量导入)
   - 实时处理状态显示

2. **上传记录页面 (uploads.html)** - `/uploads`
   - 显示所有已上传的数据源
   - 按文件名分组统计记录数量

3. **上传详情页面 (upload_details.html)** - `/upload/<filename>`
   - 显示特定上传文件的详细工单信息
   - 列出所有相关工单记录

4. **数据库统计页面 (database_stats.html)** - `/database`
   - 显示数据库总体统计信息
   - 实时数据库状态监控
   - 空FirstResponse详情查看

5. **责任人统计页面 (responsible_stats.html)** - `/responsible-stats`
   - 按责任人分组统计
   - 多选责任人分析功能
   - 年龄分布统计

6. **每日统计页面 (daily_statistics.html)** - `/daily-statistics`
   - 每日工单统计报表
   - 年龄分布趋势分析
   - 执行日志查看

7. **结果页面 (results.html)** - (通过分析后显示)
   - 分析结果展示
   - 图表和统计信息

### 🔧 API 端点

**文件处理相关:**
- `POST /upload` - 文件上传和处理
- `GET /processing-status` - 获取处理状态

**数据导出相关:**
- `POST /export/excel` - 导出Excel报表
- `POST /export/txt` - 导出文本报表

**统计分析相关:**
- `POST /age-details` - 获取年龄分段详情
- `POST /empty-firstresponse-details` - 获取空FirstResponse详情
- `GET /database-stats` - 获取数据库统计信息

**责任人分析相关:**
- `GET /api/responsible-list` - 获取责任人列表
- `POST /api/responsible-stats` - 获取责任人统计数据

**每日统计相关:**
- `GET /api/daily-statistics` - 获取每日统计数据
- `POST /api/update-schedule` - 更新统计计划
- `POST /api/calculate-daily-stats` - 手动计算每日统计
- `GET /api/export-execution-logs` - 导出执行日志

**应用更新相关:**
- `GET /api/update/status` - 查询当前版本及最新发布状态
- `POST /api/update/ack` - 标记客户端已读更新提醒
- `POST /api/update/trigger` - 触发应用自动更新（需管理员密码）

### ⚡ JavaScript 功能文件

1. **script.js** - 主页面功能
   - 文件上传处理
   - 实时进度更新
   - 数据分析交互

2. **database_stats.js** - 数据库统计功能
   - 数据库状态监控
   - 实时数据刷新
   - 详情查看功能

3. **results.js** - 结果页面功能
   - 图表渲染
   - 数据展示
   - 导出功能

### 🗄️ 数据库功能

**数据模型:**
- OtrsTicket - 工单数据
- UploadDetail - 上传记录
- Statistic - 统计查询记录
- DatabaseLog - 数据库操作日志
- ResponsibleConfig - 责任人配置
- DailyStatistics - 每日统计数据
- StatisticsConfig - 统计配置
- StatisticsLog - 统计执行日志
- AppUpdateStatus - 应用更新状态记录

**自动功能:**
- 每日23:59自动计算年龄分布统计
- 数据库操作日志记录
- 用户选择记忆功能

## 安装要求

- Python 3.6+
- 以下Python包:
  - Flask>=2.3.0
  - pandas>=1.3.0
  - openpyxl>=3.0.0
  - numpy>=1.21.0
  - matplotlib>=3.5.0
  - gunicorn>=20.1.0 (生产环境)
  - Flask-SQLAlchemy>=3.0.0
  - APScheduler>=3.10.0
  - tzlocal>=3.0
  - python-dotenv>=1.0.0
  - requests>=2.31.0

## 自动更新配置

- 设置环境变量启用/配置自动更新：
  - `APP_UPDATE_ENABLED`（默认为 `true`）控制是否启用自动更新。
  - `APP_UPDATE_REPO` 设置 GitHub 仓库（默认为 `Jacky/otrs-web`）。
  - `APP_UPDATE_BRANCH` 作为无标签时的备用分支，默认 `main`。
  - `APP_UPDATE_POLL_INTERVAL` 控制后台轮询 GitHub 发布的周期（秒）。
  - `APP_UPDATE_GITHUB_TOKEN` 可选的 GitHub Token，用于提高速率或访问私有仓库。
- 服务器上提供 `scripts/update_app.py` 脚本：
  - 自动执行 `git fetch`、切换标签/分支、安装依赖并运行升级脚本。
  - 支持 `--skip-deps`、`--pip-extra-args` 等参数，便于自定义部署流程。
- 后端启动时会执行一次版本检查，之后由调度器按配置周期轮询。
- 管理端调用顺序：
  1. 前端轮询 `GET /api/update/status` 获取最新发布信息；
  2. 弹窗提醒后通过 `POST /api/update/ack` 标记已读；
  3. 当用户确认升级时调用 `POST /api/update/trigger`（需管理员密码）启动脚本；
  4. 调用 `GET /api/update/status` 可查看更新进度与结果，失败时会返回错误原因。

## 快速开始

### 方法一：Docker部署（推荐）

#### 使用Docker Compose（最简单）

```bash
# 启动应用
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止应用
docker-compose down
```

应用将在 http://localhost:5000 启动

#### 使用Docker直接运行

```bash
# 构建镜像
docker build -t otrs-web .

# 运行容器
docker run -d -p 5000:5000 --name otrs-web-app otrs-web

# 查看运行状态
docker logs otrs-web-app
```

### 方法二：原生Python运行

#### 开发环境运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py
```

应用将在 http://localhost:5000 启动

#### 生产环境运行

```bash
# 安装生产依赖
pip install -r requirements.txt gunicorn

# 启动生产服务器 (Linux/Mac)
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app

# 启动生产服务器 (Windows)
# 建议使用Docker或WSL2，或者使用waitress作为替代:
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

## GitHub安装到Linux主机

### 方式一：直接克隆运行

```bash
# 克隆项目
git clone https://github.com/scaleflower/otrs-web.git
cd otrs-web

# 安装依赖
pip install -r requirements.txt gunicorn

# 启动生产服务器
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app

# 后台运行 (使用nohup)
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > app.log 2>&1 &
```

### 方式二：使用Systemd服务

```bash
# 创建系统服务文件
sudo nano /etc/systemd/system/otrs-web.service
```

服务文件内容：
```ini
[Unit]
Description=OTRS Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/otrs-web
Environment=PYTHONPATH=/path/to/otrs-web
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable otrs-web
sudo systemctl start otrs-web
sudo systemctl status otrs-web
```

### 方式三：使用Nginx反向代理

```bash
# 安装Nginx
sudo apt update
sudo apt install nginx

# 创建Nginx配置
sudo nano /etc/nginx/sites-available/otrs-web
```

Nginx配置内容：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件服务
    location /static {
        alias /path/to/otrs-web/static;
        expires 30d;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/otrs-web /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 使用方法

1. **上传文件**: 点击"选择Excel文件"按钮上传.xlsx或.xls格式的OTRS工单数据
2. **等待分析**: 系统会自动分析数据并显示统计结果
3. **查看结果**: 查看总记录数、开放工单、空FirstResponse等统计信息
4. **导出报告**: 点击"导出Excel"或"导出文本"按钮下载详细报告

## 支持的Excel列名

系统会自动识别以下列名变体：

- **创建时间**: Created, CreateTime, Create Time, Date Created, created, creation_date
- **关闭时间**: Closed, CloseTime, Close Time, Date Closed, closed, close_date
- **状态**: State, Status, Ticket State, state, status
- **工单号**: Ticket Number, TicketNumber, Number, ticket_number, id
- **优先级**: Priority, priority
- **首次响应**: FirstResponse, First Response, firstresponse

## 分析内容

### 基础统计
- 总记录数
- 当前开放工单数量
- 空FirstResponse记录数量

### 详细分析
- **每日统计**: 按日期统计新增和关闭工单数量
- **优先级分布**: 各优先级工单的数量分布
- **状态分布**: 各状态工单的数量分布
- **空FirstResponse分布**: 按优先级统计空FirstResponse记录

### 导出报告
- **Excel报告**: 包含多个工作表，带有直方图可视化
- **文本报告**: 简洁的文本格式统计报告

## 生产环境部署

### Gunicorn配置说明

- `-w 4`: 使用4个工作进程（根据服务器CPU核心数调整）
- `-b 0.0.0.0:5000`: 绑定到所有网络接口的5000端口
- `--access-logfile -`: 将访问日志输出到标准输出
- `--error-logfile -`: 将错误日志输出到标准输出
- `app:app`: 指定应用模块和应用实例

### 性能优化建议

1. **工作进程数**: 通常设置为CPU核心数的2-4倍
2. **超时设置**: 添加 `--timeout 120` 设置请求超时时间
3. **工作模式**: 可以使用 `--worker-class gevent` 支持异步处理
4. **资源限制**: 设置 `--worker-connections 1000` 限制每个工作进程的连接数

### 监控和维护

生产环境建议使用：

1. **进程管理**: systemd, supervisord
2. **负载均衡**: Nginx反向代理
3. **监控**: Prometheus + Grafana
4. **日志**: ELK Stack或类似方案

## 数据库结构

系统使用SQLite数据库存储工单数据和统计信息，包含以下表：

### otrs_ticket 表（工单数据表）
- **id**: INTEGER - 主键ID
- **ticket_number**: VARCHAR(100) - 工单编号
- **created_date**: DATETIME - 创建时间
- **closed_date**: DATETIME - 关闭时间
- **state**: VARCHAR(100) - 工单状态
- **priority**: VARCHAR(50) - 优先级
- **first_response**: VARCHAR(255) - 首次响应内容
- **age**: VARCHAR(50) - 工单年龄（文本格式）
- **age_hours**: FLOAT - 工单年龄（小时数）
- **queue**: VARCHAR(255) - 队列
- **owner**: VARCHAR(255) - 负责人
- **customer_id**: VARCHAR(255) - 客户ID
- **customer_realname**: VARCHAR(255) - 客户真实姓名
- **title**: TEXT - 工单标题
- **service**: VARCHAR(255) - 服务
- **type**: VARCHAR(100) - 类型
- **category**: VARCHAR(255) - 类别
- **sub_category**: VARCHAR(255) - 子类别
- **import_time**: DATETIME - 导入时间
- **data_source**: VARCHAR(255) - 数据来源
- **raw_data**: TEXT - 原始数据

### statistic 表（统计表）
- **id**: INTEGER - 主键ID
- **query_time**: DATETIME - 查询时间
- **query_type**: VARCHAR(50) - 查询类型
- **total_records**: INTEGER - 总记录数
- **current_open_count**: INTEGER - 当前开放工单数量
- **empty_firstresponse_count**: INTEGER - 空FirstResponse数量
- **daily_new_count**: INTEGER - 每日新增数量
- **daily_closed_count**: INTEGER - 每日关闭数量
- **age_segment**: VARCHAR(50) - 年龄分段
- **record_count**: INTEGER - 记录数量
- **upload_id**: INTEGER - 上传ID（外键）

### upload_detail 表（上传详情表）
- **id**: INTEGER - 主键ID
- **filename**: VARCHAR(255) - 文件名
- **upload_time**: DATETIME - 上传时间
- **record_count**: INTEGER - 记录数量
- **import_mode**: VARCHAR(50) - 导入模式

## 文件结构

```
.
├── app.py              # Flask主应用
├── requirements.txt    # Python依赖列表
├── docker-compose.yml  # Docker Compose配置
├── Dockerfile         # Docker构建配置
├── .gitignore         # Git忽略规则
├── templates/         # HTML模板
│   └── index.html     # 主页面模板
├── static/            # 静态文件
│   ├── css/
│   │   └── style.css  # 样式文件
│   └── js/
│       └── script.js  # JavaScript文件
└── uploads/           # 上传文件目录（自动创建）
```

## 技术栈

- **后端**: Flask (Python Web框架)
- **数据处理**: pandas (数据分析库)
- **图表生成**: matplotlib (数据可视化)
- **生产服务器**: Gunicorn (WSGI服务器)
- **前端**: HTML5, CSS3, JavaScript
- **图表库**: Chart.js (交互式图表)
- **图标库**: Font Awesome (图标字体)

## Docker部署说明

### 前置要求
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose (通常包含在Docker Desktop中)

### 部署步骤

#### 使用Docker Compose（推荐）
```bash
# 启动应用（后台运行）
docker-compose up -d

# 查看实时日志
docker-compose logs -f

# 停止应用
docker-compose down

# 重启应用
docker-compose restart
```

#### 使用Docker命令
```bash
# 构建镜像
docker build -t otrs-web .

# 运行容器（后台模式）
docker run -d -p 5000:5000 --name otrs-web-app otrs-web

# 运行容器（开发模式，查看实时输出）
docker run -p 5000:5000 --name otrs-web-app otrs-web

# 查看容器日志
docker logs otrs-web-app

# 进入容器shell
docker exec -it otrs-web-app /bin/bash

# 停止容器
docker stop otrs-web-app

# 删除容器
docker rm otrs-web-app
```

### 数据持久化
- 上传的文件保存在 `./uploads` 目录（通过Docker volume映射）
- 日志文件保存在 `./logs` 目录
- 这些目录会在首次运行时自动创建

## 故障排除

### 常见问题
1. **端口占用**: 如果5000端口被占用，应用会自动选择其他端口
2. **依赖安装失败**: 尝试手动运行 `pip install -r requirements.txt`
3. **文件格式错误**: 确保上传的是.xlsx或.xls格式的Excel文件

### 生产环境注意事项
1. 生产环境务必设置 `debug=False`
2. 使用环境变量管理敏感配置
3. 定期检查日志和监控指标
4. 设置适当的防火墙和安全组规则

## 开发 vs 生产

| 环境 | 服务器 | 适用场景 | 性能 | 安全性 |
|------|--------|----------|------|--------|
| 开发 | Flask开发服务器 | 本地测试 | 低 | 低 |
| 生产 | Gunicorn + Nginx | 正式部署 | 高 | 高 |

## 手动安装依赖
```bash
pip install Flask pandas openpyxl numpy matplotlib gunicorn
```

## 许可证

MIT License

## 支持

如有问题，请检查：
1. Python是否正确安装并添加到PATH
2. 网络连接是否正常（安装包需要下载）
3. Excel文件是否可访问且格式正确
