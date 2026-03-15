#!/usr/bin/env python3
"""
一键启动加班审批系统
Usage: python3 start.py
"""

import os
import sys
import subprocess
import time

def print_banner():
    print("=" * 50)
    print("🏢 加班审批系统启动中...")
    print("=" * 50)

def check_python():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ 需要 Python 3.6 或更高版本")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装依赖"""
    print("\n📦 正在安装依赖...")
    
    # 检查flask是否已安装
    try:
        import flask
        print("✅ Flask 已安装")
        return True
    except ImportError:
        pass
    
    # 安装flask
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "-q"])
        print("✅ Flask 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Flask 安装失败: {e}")
        return False

def init_database():
    """初始化数据库"""
    print("\n🗄️ 初始化数据库...")
    
    db_path = "database.db"
    if os.path.exists(db_path):
        print("✅ 数据库已存在")
        return True
    
    # 尝试导入并初始化
    try:
        # 导入app模块来初始化数据库
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # 临时创建app来初始化数据库
        import sqlite3
        import json
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 用户表
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            rank TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )''')
        
        # 加班批次表
        c.execute('''CREATE TABLE IF NOT EXISTS overtime_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dates TEXT NOT NULL,
            is_open INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 员工申请表
        c.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            batch_id INTEGER NOT NULL,
            selected_dates TEXT NOT NULL,
            reason TEXT NOT NULL,
            work_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 创建默认管理员
        c.execute("SELECT * FROM users WHERE username = 'admin'")
        if not c.fetchone():
            c.execute("INSERT INTO users (username, password, name, rank, is_admin) VALUES (?, ?, ?, ?, ?)",
                      ('admin', 'admin123', '领导', 'CL10', 1))
        
        conn.commit()
        conn.close()
        
        print("✅ 数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def start_server():
    """启动服务器"""
    print("\n🚀 启动服务器...")
    print("\n" + "=" * 50)
    print("🎉 启动成功！")
    print("=" * 50)
    print("\n📍 访问地址:")
    print("   http://localhost:5001")
    print("\n👤 测试账号:")
    print("   领导账号: admin / admin123")
    print("   员工账号: 请先注册或让领导批量创建")
    print("\n🛑 按 Ctrl+C 停止服务")
    print("=" * 50 + "\n")
    
    try:
        # 启动Flask应用
        from app import app
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    return True

def main():
    print_banner()
    
    # 检查Python
    if not check_python():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 初始化数据库
    if not init_database():
        sys.exit(1)
    
    # 启动服务器
    start_server()

if __name__ == '__main__':
    main()
