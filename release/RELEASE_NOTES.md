# OTRS Web Application v1.2.9

## 发布说明

- 解决自动升级相关问题

# OTRS Web Application v1.0.8

## 主要更新内容

### 新功能
- 支持同时从GitHub和云效获取更新版本供用户选择
- 实现了双源代码推送，可同时推送到云效和GitHub仓库
- 修复了密码验证相关的问题

### 修复和改进
- 修复了PasswordProtection类中缺失的方法
- 修复了应用程序启动时的配置导入错误
- 优化了数据库初始化逻辑
- 修复了多个导入和引用错误

## 环境要求
- Python 3.6+
- SQLite (默认) 或 PostgreSQL
- 支持Docker部署

## 安装说明
1. 克隆代码库
2. 安装依赖: `pip install -r requirements.txt`
3. 配置环境变量
4. 运行应用: `python app.py`

## 升级说明
对于从旧版本升级的用户，请确保:
1. 备份现有数据库
2. 检查环境变量配置
3. 重新安装依赖: `pip install -r requirements.txt --upgrade`

## 注意事项
- 请确保SSH密钥配置正确以支持双源推送
- 建议在生产环境中设置有效的GitHub Token以避免速率限制
