#!/usr/bin/env python3
"""
Database Schema Fix Script
修复数据库表结构，添加缺失的表和列
"""

import sqlite3
import os
from datetime import datetime

def fix_database(db_path):
    """修复数据库表结构"""
    print(f"修复数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查并创建upload_detail表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upload_detail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_time TIMESTAMP NOT NULL,
                record_count INTEGER NOT NULL,
                import_mode TEXT DEFAULT 'clear_existing',
                new_records_count INTEGER DEFAULT 0
            )
        """)
        
        # 检查是否需要添加new_records_count列
        cursor.execute("PRAGMA table_info(upload_detail)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'new_records_count' not in columns:
            print("  添加 new_records_count 列...")
            cursor.execute("ALTER TABLE upload_detail ADD COLUMN new_records_count INTEGER DEFAULT 0")
        
        if 'import_mode' not in columns:
            print("  添加 import_mode 列...")
            cursor.execute("ALTER TABLE upload_detail ADD COLUMN import_mode TEXT DEFAULT 'clear_existing'")
        
        # 创建其他必要的表
        
        # ticket表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number TEXT UNIQUE NOT NULL,
                title TEXT,
                state TEXT,
                priority TEXT,
                type TEXT,
                service TEXT,
                sla TEXT,
                queue TEXT,
                owner TEXT,
                responsible TEXT,
                customer_user_id TEXT,
                created TIMESTAMP,
                closed TIMESTAMP,
                first_response TIMESTAMP,
                solution_time TIMESTAMP,
                until_time TEXT,
                escalation_time TEXT,
                escalation_response_time TEXT,
                escalation_solution_time TEXT,
                age_in_hours REAL,
                first_response_time_hours REAL
            )
        """)
        
        # daily_statistics表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                opening_balance INTEGER DEFAULT 0,
                new_tickets INTEGER DEFAULT 0,
                resolved_tickets INTEGER DEFAULT 0,
                closing_balance INTEGER DEFAULT 0,
                age_lt_24h INTEGER DEFAULT 0,
                age_24_48h INTEGER DEFAULT 0,
                age_48_72h INTEGER DEFAULT 0,
                age_72_96h INTEGER DEFAULT 0,
                age_gt_96h INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # statistics_log表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statistic_date TEXT,
                total_open INTEGER DEFAULT 0,
                age_24h INTEGER DEFAULT 0,
                age_24_48h INTEGER DEFAULT 0,
                age_48_72h INTEGER DEFAULT 0,
                age_72_96h INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                details TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"  ✓ 数据库 {db_path} 修复完成")
        return True
        
    except Exception as e:
        print(f"  ✗ 修复数据库 {db_path} 失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 数据库表结构修复工具 ===")
    print(f"开始时间: {datetime.now()}")
    print()
    
    # 需要检查的数据库路径
    db_paths = [
        "instance/otrs_data.db",
        "db/otrs_data.db"
    ]
    
    success_count = 0
    total_count = 0
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            total_count += 1
            if fix_database(db_path):
                success_count += 1
        else:
            # 如果数据库不存在，创建目录并创建数据库
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                print(f"创建目录: {db_dir}")
            
            total_count += 1
            if fix_database(db_path):
                success_count += 1
    
    print()
    print(f"修复完成: {success_count}/{total_count} 个数据库")
    print(f"结束时间: {datetime.now()}")

if __name__ == "__main__":
    main()
