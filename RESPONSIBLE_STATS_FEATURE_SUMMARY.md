# Responsible Statistics Feature Summary

## 功能概述

新增了基于Responsible字段的工单统计功能，可以统计每个人处理工单的数量，支持按天/周/月统计，点击数量可以打开对应时间段的工单明细，并且能够配置对哪些人进行统计，忽略其他未选中的人员。

## 新增功能

### 1. 数据库模型更新

- **OtrsTicket模型**: 新增了`responsible`字段用于存储负责人信息
- **ResponsibleConfig模型**: 新增配置表用于存储用户选择的Responsible人员配置

### 2. Excel导入增强

- 扩展了Excel列名映射，支持多种Responsible字段名称：
  - Responsible
  - responsible
  - Assignee
  - assignee
  - 处理人
  - 负责人

### 3. API端点

新增了以下API端点：

- `GET /responsible-stats` - Responsible统计页面
- `GET /api/responsible-list` - 获取所有Responsible人员列表
- `GET /api/responsible-config` - 获取用户配置
- `POST /api/responsible-config` - 保存用户配置
- `POST /api/responsible-stats` - 获取Responsible统计数据
- `POST /api/responsible-details` - 获取工单详情
- `POST /api/export-responsible-excel` - 导出Excel报表
- `POST /api/export-responsible-txt` - 导出文本报表

### 4. 前端页面

新增了`templates/responsible_stats.html`页面，包含：

- 统计周期选择（按天/周/月）
- Responsible人员多选功能
- 统计数据表格展示
- 点击数量查看工单详情
- Excel和文本导出功能

## 功能特点

### 1. 灵活的统计周期
- **按天统计**: 显示每天的工单数量
- **按周统计**: 显示每周的工单数量（格式: YYYY-WW）
- **按月统计**: 显示每月的工单数量（格式: YYYY-MM）

### 2. 人员配置管理
- 用户可以选择需要统计的Responsible人员
- 配置会自动保存到数据库，基于用户IP地址
- 支持全选/取消全选功能

### 3. 交互式数据展示
- 点击统计数字可以查看对应时间段的工单详情
- 支持模态框显示工单详细信息
- 实时加载和显示数据

### 4. 数据导出功能
- 支持导出Excel格式报表
- 支持导出文本格式报表
- 导出文件包含统计数据和配置信息

## 技术实现

### 后端实现
- 使用SQLAlchemy进行数据库查询和分组统计
- 支持SQLite的日期函数进行时间分组
- 使用JSON存储用户配置

### 前端实现
- 使用Bootstrap 5进行响应式设计
- 使用Fetch API进行异步数据加载
- 支持加载状态显示和错误处理

## 测试验证

已通过完整的测试验证：
1. ✅ Responsible列表获取
2. ✅ 按天/周/月统计功能
3. ✅ 用户配置保存和读取
4. ✅ 工单详情查看
5. ✅ 数据导出功能

## 使用说明

1. 上传包含Responsible字段的Excel文件
2. 访问 `/responsible-stats` 页面
3. 选择统计周期和需要统计的人员
4. 点击"加载统计"查看结果
5. 点击数字查看工单详情
6. 使用导出按钮下载报表

## 文件变更

### 新增文件
- `templates/responsible_stats.html` - Responsible统计页面
- `test_responsible_stats.py` - 功能测试脚本
- `recreate_db.py` - 数据库重建脚本

### 修改文件
- `app.py` - 新增API端点和数据库模型
- `templates/index.html` - 添加导航链接

## 数据库变更

- `otrs_ticket`表新增`responsible`字段
- 新增`responsible_config`表存储用户配置

## 兼容性

- 向后兼容现有的所有功能
- 不影响现有的统计和导出功能
- 支持增量数据导入

## 性能考虑

- 使用数据库索引优化查询性能
- 分页加载大量数据
- 异步数据处理避免阻塞
