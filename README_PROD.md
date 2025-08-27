# 生产环境部署指南

## Flask开发服务器警告解决方案

您看到的警告信息：
```
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
```

这是Flask内置的开发服务器，不适合生产环境使用。

## 解决方案

### 方案1：开发环境（忽略警告）

如果您只是在开发测试，可以忽略这个警告。Flask开发服务器适合开发和测试使用。

```bash
# 继续使用开发服务器
python app.py
```

### 方案2：使用环境变量抑制警告（开发环境）

设置环境变量来抑制警告：

```bash
# Windows
set FLASK_ENV=development
set PYTHONWARNINGS=ignore
python app.py

# Linux/Mac
export FLASK_ENV=development
export PYTHONWARNINGS=ignore
python app.py
```

### 方案3：生产环境部署（推荐）

使用Gunicorn作为生产级WSGI服务器：

#### 安装生产依赖

```bash
pip install -r requirements_prod.txt
```

#### 启动生产服务器

**Linux/Mac:**
```bash
bash start_prod.sh
```

**Windows:**
```cmd
start_prod.bat
```

#### 手动启动Gunicorn

```bash
# 基本启动
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 带日志输出
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app

# 更多工作进程（根据CPU核心数调整）
gunicorn -w $(nproc) -b 0.0.0.0:5000 app:app
```

### 方案4：Docker部署

项目已经包含Docker支持：

```bash
# 构建镜像
docker build -t otrs-web .

# 运行容器
docker run -p 5000:5000 otrs-web

# 使用docker-compose
docker-compose up
```

## Gunicorn配置说明

- `-w 4`: 使用4个工作进程（根据服务器CPU核心数调整）
- `-b 0.0.0.0:5000`: 绑定到所有网络接口的5000端口
- `--access-logfile -`: 将访问日志输出到标准输出
- `--error-logfile -`: 将错误日志输出到标准输出
- `app:app`: 指定应用模块和应用实例

## 性能优化建议

1. **工作进程数**: 通常设置为CPU核心数的2-4倍
2. **超时设置**: 添加 `--timeout 120` 设置请求超时时间
3. **工作模式**: 可以使用 `--worker-class gevent` 支持异步处理
4. **资源限制**: 设置 `--worker-connections 1000` 限制每个工作进程的连接数

## 监控和维护

生产环境建议使用：

1. **进程管理**: systemd, supervisord
2. **负载均衡**: Nginx反向代理
3. **监控**: Prometheus + Grafana
4. **日志**: ELK Stack或类似方案

## 注意事项

1. 生产环境务必设置 `debug=False`
2. 使用环境变量管理敏感配置
3. 定期检查日志和监控指标
4. 设置适当的防火墙和安全组规则

## 开发 vs 生产

| 环境 | 服务器 | 适用场景 | 性能 | 安全性 |
|------|--------|----------|------|--------|
| 开发 | Flask开发服务器 | 本地测试 | 低 | 低 |
| 生产 | Gunicorn + Nginx | 正式部署 | 高 | 高 |
