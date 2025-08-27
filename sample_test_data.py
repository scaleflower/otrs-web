#!/usr/bin/env python3
"""
创建示例Excel文件用于测试OTRS工单分析应用
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def create_sample_excel():
    """创建示例OTRS工单数据Excel文件"""
    
    # 生成示例数据
    num_records = 50
    dates = [datetime.now().date() - timedelta(days=i) for i in range(30)]
    
    data = {
        'Ticket Number': [f'TK{1000 + i}' for i in range(num_records)],
        'Created': [np.random.choice(dates) for _ in range(num_records)],
        'Closed': [np.random.choice([None, np.random.choice(dates)], p=[0.3, 0.7]) for _ in range(num_records)],
        'State': np.random.choice(['Open', 'Closed', 'Resolved', 'In Progress'], num_records, p=[0.3, 0.4, 0.2, 0.1]),
        'Priority': np.random.choice(['1 very high', '2 high', '3 normal'], num_records, p=[0.1, 0.3, 0.6]),
        'FirstResponse': np.random.choice(['', 'Completed', 'Pending', None], num_records, p=[0.2, 0.5, 0.2, 0.1]),
        'Age': [f'{np.random.randint(1, 5)} d {np.random.randint(1, 24)} h' for _ in range(num_records)]
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存为Excel文件
    filename = 'sample_otrs_data.xlsx'
    df.to_excel(filename, index=False)
    
    print(f"✅ 示例Excel文件已创建: {filename}")
    print(f"📊 记录数量: {num_records}")
    print("📋 包含列: Ticket Number, Created, Closed, State, Priority, FirstResponse, Age")
    print("\n💡 使用说明:")
    print(f"1. 访问 http://localhost:5000")
    print(f"2. 上传 {filename} 文件")
    print("3. 查看分析结果")
    print("4. 测试导出功能")
    
    return filename

if __name__ == "__main__":
    create_sample_excel()
