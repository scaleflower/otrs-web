# OTRS 数据库升级指南

## 问题描述

在运行程序清理数据库时出现错误：
```
Error processing file: (sqlite3.OperationalError) no such column: otrs_ticket.responsible
```

这是因为数据库表中缺少 `responsible` 列，但代码中已经实现了 responsible 统计功能。

## 解决方案

提供了两种解决方案：

### 方案一：数据库升级（推荐）

使用升级脚本在现有数据库中添加 `responsible` 列，保留现有数据：

```bash
python upgrade_database.py
```

**特点：**
- ✅ 保留现有数据
- ✅ 只添加缺失的列
- ✅ 自动创建备份
- ✅ 验证升级结果

### 方案二：数据库重新创建

完全重新创建数据库，删除所有现有数据：

```bash
python recreate_database_with_responsible.py
```

**特点：**
- ⚠️ 删除所有现有数据
- ✅ 创建全新的数据库
- ✅ 包含所有最新字段
- ✅ 自动创建备份

## 升级脚本说明

### upgrade_database.py

主要功能：
1. 检查 `responsible` 列是否已存在
2. 创建数据库备份
3. 使用 `ALTER TABLE` 添加 `responsible` 列
4. 创建测试数据验证功能
5. 测试 responsible 相关功能

### recreate_database_with_responsible.py

主要功能：
1. 创建数据库备份
2. 删除现有数据库文件
3. 使用 `db.create_all()` 重新创建所有表
4. 验证新数据库结构

## 验证升级结果

运行以下命令验证数据库结构：

```bash
python check_database_schema.py
```

运行以下命令测试 responsible 统计功能：

```bash
python test_responsible_stats.py
```

## 数据库结构变化

升级后的 `otrs_ticket` 表包含以下列：

- `id` - INTEGER (主键)
- `ticket_number` - VARCHAR(100)
- `created_date` - DATETIME
- `closed_date` - DATETIME
- `state` - VARCHAR(100)
- `priority` - VARCHAR(50)
- `first_response` - VARCHAR(255)
- `age` - VARCHAR(50)
- `age_hours` - FLOAT
- `queue` - VARCHAR(255)
- `owner` - VARCHAR(255)
- `customer_id` - VARCHAR(255)
- `customer_realname` - VARCHAR(255)
- `title` - TEXT
- `service` - VARCHAR(255)
- `type` - VARCHAR(100)
- `category` - VARCHAR(255)
- `sub_category` - VARCHAR(255)
- `responsible` - VARCHAR(255) ✅ **新增列**
- `import_time` - DATETIME
- `data_source` - VARCHAR(255)
- `raw_data` - TEXT

## 备份文件位置

所有备份文件保存在 `database_backups/` 目录中，文件名格式：
- `otrs_backup_pre_upgrade_YYYYMMDD_HHMMSS.db` - 升级前备份
- `otrs_backup_before_recreate_YYYYMMDD_HHMMSS.db` - 重新创建前备份

## 注意事项

1. **推荐使用升级方案**：除非有特殊需求，否则建议使用 `upgrade_database.py` 保留现有数据
2. **备份重要性**：两个脚本都会自动创建备份，确保数据安全
3. **测试验证**：升级后请运行测试脚本验证功能正常
4. **数据兼容性**：新增的 `responsible` 列允许 NULL 值，与现有数据兼容

## 故障排除

如果升级过程中遇到问题：

1. 检查数据库文件权限
2. 确保有足够的磁盘空间
3. 查看详细的错误信息
4. 可以从备份文件中恢复数据

备份文件位于 `database_backups/` 目录，可以直接复制回 `instance/otrs_data.db` 进行恢复。
