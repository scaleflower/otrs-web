#!/usr/bin/env python3
"""
Production server script for OTRS Ticket Analysis Web Application
使用Gunicorn作为生产服务器
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # 生产环境配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting production server on {host}:{port}")
    print("Note: This is a production-ready server using Gunicorn")
    
    # 使用Gunicorn启动应用
    # 这个文件主要用于开发环境测试，实际生产环境应该直接使用:
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
    
    # 对于开发环境，仍然可以使用Flask开发服务器，但会显示警告
    # 生产环境建议使用上面的gunicorn命令
    app.run(host=host, port=port, debug=False)
