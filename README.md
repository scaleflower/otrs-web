# OTRS工单数据分析Web应用

基于Flask的OTRS工单数据分析Web应用，提供美观的界面和丰富的统计分析功能。

## 功能特性

- 📊 **数据可视化**: 精美的图表展示工单统计数据
- 📈 **多种分析**: 优先级分布、状态分布、每日统计等
- 💾 **文件上传**: 支持Excel文件上传和分析
- 📥 **导出功能**: 支持导出Excel和文本格式报告
- 🎨 **美观界面**: 现代化的响应式设计
- 📱 **移动友好**: 支持各种设备屏幕尺寸

## 安装要求

- Python 3.6+
- 以下Python包:
  - Flask>=2.3.0
  - pandas>=1.3.0
  - openpyxl>=3.0.0
  - numpy>=1.21.0
  - matplotlib>=3.5.0

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

#### 双击运行
1. 下载所有文件到同一文件夹
2. 双击运行 `run_web.bat`
3. 脚本会自动检查并安装所需依赖
4. 浏览器自动打开 http://localhost:5000

#### 命令行运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

应用将在 http://localhost:5000 启动

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

## 文件结构

```
.
├── app.py              # Flask主应用
├── requirements.txt    # Python依赖列表
├── run_web.bat        # Windows启动脚本
├── templates/         # HTML模板
│   └── index.html     # 主页面模板
├── static/            # 静态文件
│   ├── css/
│   │   └── style.css  # 样式文件
│   └── js/
│       └── script.js  # JavaScript文件
└── backup/            # 原始脚本备份
```

## 技术栈

- **后端**: Flask (Python Web框架)
- **数据处理**: pandas (数据分析库)
- **图表生成**: matplotlib (数据可视化)
- **前端**: HTML5, CSS3, JavaScript
- **图表库**: Chart.js (交互式图表)
- **图标库**: Font Awesome (图标字体)

## Docker部署说明

### 前置要求
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose (通常包含在Docker Desktop中)

### 部署步骤

#### 1. 使用Docker Compose（推荐）
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

#### 2. 使用Docker命令
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

### Docker相关问题
1. **端口冲突**: 如果5000端口被占用，可以修改docker-compose.yml中的端口映射（如: "8080:5000"）
2. **构建失败**: 确保网络连接正常，Docker可以访问外部资源
3. **权限问题**: 在Linux上可能需要使用sudo或配置Docker用户组

### 常见问题
1. **端口占用**: 如果5000端口被占用，应用会自动选择其他端口
2. **依赖安装失败**: 尝试手动运行 `pip install -r requirements.txt`
3. **文件格式错误**: 确保上传的是.xlsx或.xls格式的Excel文件

### 手动安装依赖
```bash
pip install Flask pandas openpyxl numpy matplotlib
```

## 许可证

MIT License

## 支持

如有问题，请检查：
1. Python是否正确安装并添加到PATH
2. 网络连接是否正常（安装包需要下载）
3. Excel文件是否可访问且格式正确
