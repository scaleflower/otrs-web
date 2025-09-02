# OTRS Web Application - 系统统计逻辑文档

## 概述

本文档详细说明OTRS Web应用程序中所有页面的统计逻辑和计算方法。

---

## 1. 主页 (Index Page) - Analysis Results

### 1.1 基础统计

#### Total Records (总记录数)
```sql
SELECT COUNT(*) FROM otrs_ticket
```

#### Current Open Count (当前开放工单数)
```sql
SELECT COUNT(*) FROM otrs_ticket WHERE closed_date IS NULL
```

#### Empty First Response (空首次响应)
```sql
SELECT COUNT(*) FROM otrs_ticket 
WHERE (first_response IS NULL OR first_response = '' OR first_response = 'nan' OR first_response = 'NaN')
AND state NOT IN ('Closed', 'Resolved')
```

### 1.2 时间维度统计

#### Daily New Tickets (每日新工单)
```sql
SELECT DATE(created_date) as date, COUNT(*) as count 
FROM otrs_ticket 
WHERE created_date IS NOT NULL 
GROUP BY DATE(created_date)
```

#### Daily Closed Tickets (每日关闭工单)
```sql
SELECT DATE(closed_date) as date, COUNT(*) as count 
FROM otrs_ticket 
WHERE closed_date IS NOT NULL 
GROUP BY DATE(closed_date)
```

#### Daily Open Tickets (每日开放工单累计)
```
计算逻辑：累计开放 = 前一天累计 + 当天新增 - 当天关闭
```

### 1.3 分类统计

#### Priority Distribution (优先级分布)
```sql
SELECT priority, COUNT(*) as count 
FROM otrs_ticket 
WHERE priority IS NOT NULL 
GROUP BY priority
```

#### State Distribution (状态分布)
```sql
SELECT state, COUNT(*) as count 
FROM otrs_ticket 
WHERE state IS NOT NULL 
GROUP BY state
```

### 1.4 年龄段统计

#### Age Segments (年龄段分布)
基于开放工单的age_hours字段：
- **≤24小时**: `age_hours <= 24`
- **24-48小时**: `24 < age_hours <= 48`
- **48-72小时**: `48 < age_hours <= 72`
- **>72小时**: `age_hours > 72`

```sql
SELECT COUNT(*) FROM otrs_ticket 
WHERE closed_date IS NULL AND age_hours IS NOT NULL
```

### 1.5 优先级维度首次响应统计

#### Empty First Response by Priority
```sql
SELECT priority, COUNT(*) as count 
FROM otrs_ticket 
WHERE (first_response IS NULL OR first_response = '' OR first_response = 'nan' OR first_response = 'NaN')
AND state NOT IN ('Closed', 'Resolved')
AND priority IS NOT NULL 
GROUP BY priority
```

---

## 2. Database Statistics Page

### 2.1 数据库概览

#### Total Records (总记录数)
```sql
SELECT COUNT(*) FROM otrs_ticket
```

#### Data Sources Count (数据源数量)
```sql
SELECT COUNT(DISTINCT data_source) FROM otrs_ticket
```

#### Last Updated (最后更新时间)
```sql
SELECT MAX(import_time) FROM otrs_ticket
```

### 2.2 详细统计
继承主页的所有统计逻辑，包括：
- 基础统计
- 时间维度统计
- 分类统计
- 年龄段统计

### 2.3 空首次响应详情
提供具体的工单详情列表：
```sql
SELECT ticket_number, age, created_date, priority, state 
FROM otrs_ticket 
WHERE (first_response IS NULL OR first_response = '' OR first_response = 'nan' OR first_response = 'NaN')
AND state NOT IN ('Closed', 'Resolved')
```

---

## 3. Daily Statistics Page

### 3.1 数据模型
Daily Statistics基于`daily_statistics`表，包含以下字段：
- `statistic_date`: 统计日期
- `opening_balance`: 期初余额
- `new_tickets`: 新增工单
- `resolved_tickets`: 解决工单
- `closing_balance`: 期末余额
- `age_lt_24h`: <24小时工单数
- `age_24_48h`: 24-48小时工单数
- `age_48_72h`: 48-72小时工单数
- `age_72_96h`: 72-96小时工单数
- `age_gt_96h`: >96小时工单数

### 3.2 Opening Balance计算逻辑

#### 第一条记录
```sql
Opening Balance = (SELECT COUNT(*) FROM otrs_ticket) - 
                 (SELECT COUNT(*) FROM otrs_ticket WHERE state IN ('Closed', 'Resolved', 'Cancelled'))
```

#### 后续记录
```sql
Opening Balance = 前一天的Closing Balance
```

### 3.3 New Tickets计算逻辑
```sql
SELECT COUNT(*) FROM otrs_ticket WHERE DATE(created_date) = TODAY
```

### 3.4 Resolved Tickets计算逻辑
```sql
SELECT COUNT(*) FROM otrs_ticket WHERE DATE(closed_date) = TODAY
```

### 3.5 Closing Balance计算逻辑
```sql
SELECT COUNT(*) FROM otrs_ticket WHERE closed_date IS NULL
```

### 3.6 Age Distribution计算逻辑
基于当前所有开放工单的age_hours：
- `age_lt_24h`: `age_hours < 24`
- `age_24_48h`: `24 <= age_hours < 48`
- `age_48_72h`: `48 <= age_hours < 72`
- `age_72_96h`: `72 <= age_hours < 96`
- `age_gt_96h`: `age_hours >= 96`

### 3.7 调度配置
- **默认执行时间**: 23:59
- **时区**: Asia/Shanghai (UTC+8)
- **配置表**: `statistics_config`

### 3.8 执行日志
记录到`statistics_log`表：
- 执行时间
- 统计日期
- 年龄分布数据
- 执行状态
- 错误信息（如有）

---

## 4. Responsible Statistics Page

### 4.1 基础负责人统计

#### Total Tickets by Responsible (按负责人统计总工单)
```sql
SELECT responsible, COUNT(*) as count 
FROM otrs_ticket 
WHERE responsible IN (selected_responsibles)
GROUP BY responsible
```

#### Open Tickets by Responsible (按负责人统计开放工单)
```sql
SELECT responsible, COUNT(*) as count 
FROM otrs_ticket 
WHERE responsible IN (selected_responsibles)
AND closed_date IS NULL 
GROUP BY responsible
```

### 4.2 年龄分布统计

#### Age Distribution by Responsible
对每个负责人计算开放工单的年龄分布：
```sql
SELECT responsible, age_hours 
FROM otrs_ticket 
WHERE responsible = ? AND closed_date IS NULL
```

分组统计：
- `age_24h`: `age_hours <= 24`
- `age_24_48h`: `24 < age_hours <= 48`
- `age_48_72h`: `48 < age_hours <= 72`
- `age_72h`: `age_hours > 72`

### 4.3 时间周期统计

#### Daily Statistics (按日统计)
```sql
SELECT DATE(created_date) as date, responsible, COUNT(*) as count 
FROM otrs_ticket 
WHERE responsible IN (selected_responsibles)
AND created_date IS NOT NULL 
GROUP BY DATE(created_date), responsible 
ORDER BY DATE(created_date) DESC
```

#### Weekly Statistics (按周统计)
```sql
SELECT STRFTIME('%Y-%W', created_date) as week, responsible, COUNT(*) as count 
FROM otrs_ticket 
WHERE responsible IN (selected_responsibles)
AND created_date IS NOT NULL 
GROUP BY STRFTIME('%Y-%W', created_date), responsible 
ORDER BY STRFTIME('%Y-%W', created_date) DESC
```

#### Monthly Statistics (按月统计)
```sql
SELECT STRFTIME('%Y-%m', created_date) as month, responsible, COUNT(*) as count 
FROM otrs_ticket 
WHERE responsible IN (selected_responsibles)
AND created_date IS NOT NULL 
GROUP BY STRFTIME('%Y-%m', created_date), responsible 
ORDER BY STRFTIME('%Y-%m', created_date) DESC
```

### 4.4 详情查询逻辑

#### Age-based Details (基于年龄的详情)
```sql
SELECT * FROM otrs_ticket 
WHERE responsible = ? 
AND closed_date IS NULL 
AND age_hours [符合年龄段条件]
```

#### Period-based Details (基于时间周期的详情)

**Daily Details:**
```sql
SELECT * FROM otrs_ticket 
WHERE responsible = ? 
AND DATE(created_date) = ?
```

**Weekly Details:**
```sql
SELECT * FROM otrs_ticket 
WHERE responsible = ? 
AND created_date >= week_start 
AND created_date < week_end
```

**Monthly Details:**
```sql
SELECT * FROM otrs_ticket 
WHERE responsible = ? 
AND YEAR(created_date) = ? 
AND MONTH(created_date) = ?
```

### 4.5 用户选择记录
保存用户选择的负责人到`responsible_config`表：
```sql
INSERT/UPDATE responsible_config 
SET user_identifier = ?, selected_responsibles = ?
```

---

## 5. Uploads Page

### 5.1 上传历史统计

#### Upload Sessions (上传会话)
```sql
SELECT * FROM upload_detail 
ORDER BY upload_time DESC
```

显示字段：
- 文件名 (`filename`)
- 上传时间 (`upload_time`)
- 记录数量 (`record_count`) - 数据库总记录数
- 新增记录数 (`new_records_count`) - 本次新增记录数
- 导入模式 (`import_mode`) - clear_existing/incremental

### 5.2 增量导入逻辑

#### 重复检测逻辑
```sql
SELECT ticket_number FROM otrs_ticket 
WHERE ticket_number IN (Excel文件中的ticket_numbers)
```

#### 新记录插入逻辑
```
1. 读取Excel文件中的所有Ticket Number
2. 查询数据库中已存在的Ticket Number
3. 计算差集：Excel工单号 - 数据库已有工单号 = 需要插入的新工单
4. 只插入新工单到数据库
5. 记录统计：
   - record_count = 插入后数据库总记录数
   - new_records_count = 本次插入的新记录数
```

---

## 6. Upload Details Page

### 6.1 单个上传详情

#### Upload Session Info
```sql
SELECT * FROM upload_detail WHERE filename = ?
```

#### Associated Tickets
```sql
SELECT * FROM otrs_ticket WHERE data_source = ?
```

### 6.2 显示逻辑
- 如果找不到upload_detail记录，创建MockSession用于向后兼容
- 显示该上传文件相关的所有工单记录
- 处理空值和错误情况

---

## 7. 最新上传信息API

### 7.1 首页上传信息显示

#### Latest Upload Info
```sql
SELECT * FROM upload_detail 
ORDER BY upload_time DESC 
LIMIT 1
```

#### Real-time Statistics
```sql
-- 总记录数
SELECT COUNT(*) FROM otrs_ticket

-- 开放工单数
SELECT COUNT(*) FROM otrs_ticket WHERE closed_date IS NULL
```

### 7.2 数据一致性
- **Analysis Results页面**: 使用缓存的上传会话数据
- **首页上传信息**: 使用实时数据库查询
- **解决方案**: 统一使用实时查询保证数据一致性

---

## 8. 年龄段详情查询

### 8.1 年龄段过滤逻辑

#### Age Segment Mapping
- `24h`: `age_hours <= 24`
- `24_48h`: `24 < age_hours <= 48`
- `48_72h`: `48 < age_hours <= 72`
- `72h`: `age_hours > 72`

#### Details Query
```sql
SELECT ticket_number, age, created_date, priority 
FROM otrs_ticket 
WHERE closed_date IS NULL 
AND age_hours [符合年龄段条件]
```

---

## 9. 空首次响应详情查询

### 9.1 过滤条件
```sql
SELECT ticket_number, age, created_date, priority, state 
FROM otrs_ticket 
WHERE (first_response IS NULL OR first_response = '' OR first_response = 'nan' OR first_response = 'NaN')
AND state NOT IN ('Closed', 'Resolved')
```

---

## 10. 数据导出功能

### 10.1 Excel导出
- 支持Analysis Results数据导出
- 支持Responsible Statistics数据导出
- 包含图表和详细数据

### 10.2 文本导出
- 支持Analysis Results数据导出
- 支持Responsible Statistics数据导出
- 纯文本格式

### 10.3 执行日志导出
```sql
SELECT * FROM statistics_log 
ORDER BY execution_time DESC
```

---

## 11. 统计查询日志

### 11.1 查询记录
每次统计查询都会记录到`statistic`表：
- 查询时间
- 查询类型 (main_analysis, age_details, empty_firstresponse等)
- 结果记录数
- 关联的上传ID

### 11.2 查询类型
- `main_analysis`: 主页分析
- `age_details`: 年龄段详情
- `empty_firstresponse`: 空首次响应详情
- `export_excel`: Excel导出
- `export_txt`: 文本导出

---

## 12. 系统架构说明

### 12.1 数据流向
```
Excel上传 → 增量导入 → otrs_ticket表 → 实时统计查询 → 页面展示
                ↓
            upload_detail表 → 上传历史追踪
```

### 12.2 调度系统
- **Daily Statistics**: 每日自动计算并存储
- **实时统计**: 基于otrs_ticket表实时查询
- **缓存策略**: Analysis Results使用实时查询避免数据不一致

### 12.3 数据一致性保证
- Opening Balance特殊逻辑确保数据连续性
- 增量导入避免重复数据
- 实时查询保证数据最新性
- 错误日志记录便于问题排查

---

## 总结

本系统通过多层次的统计逻辑，从不同维度（时间、负责人、优先级、状态、年龄）分析OTRS工单数据，为管理决策提供全面的数据支撑。所有统计逻辑都基于otrs_ticket核心表，通过SQL查询实现，确保数据的准确性和实时性。
