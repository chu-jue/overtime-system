import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'overtime-system-secret-key-2024'
DB_PATH = '/root/.openclaw/workspace/overtime-system/database.db'

# 初始化数据库
def init_db():
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
    
    # 加班申请表
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        overtime_date DATE NOT NULL,
        reason TEXT NOT NULL,
        work_content TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, overtime_date)
    )''')
    
    # 系统设置表
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        open_date DATE,
        overtime_date DATE,
        start_time TIME,
        end_time TIME,
        is_open INTEGER DEFAULT 0
    )''')
    
    # 创建默认管理员
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, name, rank, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ('admin', 'admin123', '领导', 'L10', 1))
    
    # 初始化设置
    c.execute("SELECT * FROM settings WHERE id = 1")
    if not c.fetchone():
        c.execute("INSERT INTO settings (id, is_open) VALUES (1, 0)")
    
    conn.commit()
    conn.close()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['rank'] = user['rank']
            session['is_admin'] = user['is_admin']
            
            if user['is_admin']:
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        rank = request.form['rank']
        
        try:
            conn = get_db()
            conn.execute('INSERT INTO users (username, password, name, rank) VALUES (?, ?, ?, ?)',
                        (username, password, name, rank))
            conn.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('用户名已存在')
    
    return render_template('register.html')

# 登出
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 首页 / 申请页面
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取系统设置
    conn = get_db()
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    
    # 获取用户今天的申请
    today = date.today()
    application = conn.execute(
        'SELECT * FROM applications WHERE user_id = ? AND overtime_date = ?',
        (session['user_id'], today)
    ).fetchone()
    
    return render_template('index.html', settings=settings, application=application)

# 提交/修改申请
@app.route('/apply', methods=['POST'])
def apply():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    
    # 检查是否开放
    if not settings or not settings['is_open']:
        flash('申请尚未开放')
        return redirect(url_for('index'))
    
    overtime_date = request.form['overtime_date']
    reason = request.form['reason']
    work_content = request.form['work_content']
    
    # 检查是否在申请时间内
    now = datetime.now().time()
    if settings['start_time'] and now < settings['start_time']:
        flash('申请时间未到')
        return redirect(url_for('index'))
    if settings['end_time'] and now > settings['end_time']:
        flash('申请时间已过')
        return redirect(url_for('index'))
    
    # 检查今天是否已提交
    today = date.today()
    existing = conn.execute(
        'SELECT * FROM applications WHERE user_id = ? AND overtime_date = ?',
        (session['user_id'], overtime_date)
    ).fetchone()
    
    if existing:
        # 更新
        conn.execute('''UPDATE applications 
                       SET reason = ?, work_content = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE user_id = ? AND overtime_date = ?''',
                    (reason, work_content, session['user_id'], overtime_date))
        flash('申请已更新')
    else:
        # 插入
        conn.execute('''INSERT INTO applications (user_id, overtime_date, reason, work_content)
                       VALUES (?, ?, ?, ?)''',
                    (session['user_id'], overtime_date, reason, work_content))
        flash('申请提交成功')
    
    conn.commit()
    return redirect(url_for('index'))

# 统计页面
@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    
    # 获取指定日期的申请
    if settings and settings['overtime_date']:
        applications = conn.execute('''SELECT a.*, u.name, u.rank 
                                       FROM applications a 
                                       JOIN users u ON a.user_id = u.id 
                                       WHERE a.overtime_date = ?
                                       ORDER BY u.rank, u.name''', 
                                   (settings['overtime_date'],)).fetchall()
    else:
        applications = []
    
    return render_template('stats.html', applications=applications, settings=settings)

# 管理后台
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db()
    
    if request.method == 'POST':
        open_date = request.form.get('open_date')
        overtime_date = request.form.get('overtime_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        is_open = 1 if request.form.get('is_open') else 0
        
        conn.execute('''UPDATE settings SET 
                       open_date = ?, overtime_date = ?, 
                       start_time = ?, end_time = ?, is_open = ?
                       WHERE id = 1''',
                    (open_date, overtime_date, start_time, end_time, is_open))
        conn.commit()
        flash('设置已更新')
    
    settings = conn.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    applications = conn.execute('''SELECT a.*, u.name, u.rank 
                                   FROM applications a 
                                   JOIN users u ON a.user_id = u.id 
                                   ORDER BY a.overtime_date DESC, u.rank''').fetchall()
    
    return render_template('admin.html', settings=settings, applications=applications)

# 获取今日统计
@app.route('/today_stats')
def today_stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    settings = conn.execute('SELECT overtime_date FROM settings WHERE id = 1').fetchone()
    
    if settings and settings['overtime_date']:
        applications = conn.execute('''SELECT u.name, u.rank, a.reason, a.work_content
                                       FROM applications a 
                                       JOIN users u ON a.user_id = u.id 
                                       WHERE a.overtime_date = ?''',
                                   (settings['overtime_date'],)).fetchall()
        return {'applications': [dict(a) for a in applications]}
    
    return {'applications': []}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
