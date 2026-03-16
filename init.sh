#!/bin/bash
# 加班管理系统初始化脚本

echo "🚀 初始化加班管理系统..."

# 创建必要的目录
mkdir -p static

# 检查并创建数据库
if [ ! -f "database.db" ]; then
    echo "📦 创建数据库..."
    # 使用当前工作目录（假设在项目目录下运行）
    python3 << 'PYEOF'
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'database.db')
conn = sqlite3.connect(DB_PATH)
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES overtime_batches(id)
)''')

# 创建默认管理员
c.execute(\"SELECT * FROM users WHERE username = 'admin'\")
if not c.fetchone():
    c.execute('INSERT INTO users (username, password, name, rank, is_admin) VALUES (?, ?, ?, ?, ?)',
              ('admin', 'admin123', '领导', 'CL10', 1))
    print('✅ 默认管理员已创建: admin / admin123')

conn.commit()
conn.close()
print('✅ 数据库初始化完成')
"
else
    echo "📦 数据库已存在，跳过创建"
fi

# 创建static目录（如果不存在）
if [ ! -d "static" ]; then
    mkdir -p static
fi

if [ ! -f "static/style.css" ]; then
    echo "📦 创建默认样式文件..."
    cat > static/style.css << 'EOF'
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: #fff;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

header h1 {
    font-size: 24px;
    color: #1976d2;
}

.user-info {
    display: flex;
    gap: 10px;
    align-items: center;
}

.card {
    background: #fff;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card h2 {
    font-size: 20px;
    margin-bottom: 15px;
    color: #333;
}

.card h3 {
    font-size: 16px;
    margin: 20px 0 10px;
    color: #666;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
    color: #555;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #1976d2;
}

.btn {
    background: #1976d2;
    color: #fff;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.btn:hover {
    background: #1565c0;
}

.btn-small {
    background: #f5f5f5;
    color: #333;
    padding: 6px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    text-decoration: none;
    display: inline-block;
}

.btn-small:hover {
    background: #e0e0e0;
}

.btn-danger {
    background: #f44336;
    color: #fff;
}

.btn-danger:hover {
    background: #d32f2f;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

table th,
table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #eee;
}

table th {
    background: #f5f5f5;
    font-weight: 600;
    color: #666;
}

table tr:hover {
    background: #fafafa;
}

.badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
}

.badge-open {
    background: #4caf50;
    color: #fff;
}

.badge-closed {
    background: #9e9e9e;
    color: #fff;
}

.alert {
    background: #fff3cd;
    color: #856404;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 20px;
    border: 1px solid #ffeeba;
}

.info-box {
    background: #e3f2fd;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 20px;
}

.info-box p {
    margin: 5px 0;
}

.hint {
    color: #999;
    font-size: 13px;
    margin-top: 5px;
}

.date-checkbox {
    display: inline-flex;
    align-items: center;
    margin-right: 15px;
    margin-bottom: 10px;
}

.date-checkbox input {
    width: auto;
    margin-right: 5px;
}

.no-data {
    text-align: center;
    padding: 40px;
    color: #999;
}
EOF
    echo "✅ 样式文件已创建"
fi

echo ""
echo "🎉 初始化完成！"
echo ""
echo "启动命令: python3 start.py"
echo "默认管理员账号: admin / admin123"
echo "访问地址: http://localhost:5001"
