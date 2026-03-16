import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from datetime import datetime, date, timedelta
import json

app = Flask(__name__)
app.secret_key = 'overtime-system-secret-key-2024'
import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

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
    
    # 加班批次表（领导创建）
    c.execute('''CREATE TABLE IF NOT EXISTS overtime_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dates TEXT NOT NULL,  -- JSON数组，如 ["2026-03-18", "2026-03-19"]
        is_open INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 员工申请表
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        rank TEXT NOT NULL,
        phone TEXT NOT NULL,
        selected_dates TEXT NOT NULL,
        reason TEXT NOT NULL,
        work_content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES overtime_batches(id)
    )''')
    
    # 创建默认管理员
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, name, rank, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ('admin', 'admin123', '领导', 'CL10', 1))
    
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
    conn = get_db()
    
    # 获取所有开放的加班批次
    batches_raw = conn.execute('SELECT * FROM overtime_batches WHERE is_open = 1 ORDER BY created_at DESC').fetchall()
    
    # 解析日期JSON
    batches = []
    for b in batches_raw:
        batch = dict(b)
        batch['dates'] = json.loads(batch['dates'])
        batches.append(batch)
    
    # 获取所有申请
    applications = conn.execute('''SELECT a.*, b.name as batch_name
                                    FROM applications a 
                                    JOIN overtime_batches b ON a.batch_id = b.id
                                    ORDER BY a.created_at DESC''').fetchall()
    for app in applications:
        app['selected_dates'] = json.loads(app['selected_dates'])
    
    return render_template('index.html', batches=batches, applications=applications)

# 提交/修改申请
@app.route('/apply', methods=['POST'])
def apply():
    batch_id = request.form.get('batch_id')
    name = request.form['name']
    rank = request.form['rank']
    dates_input = request.form.get('dates', '[]')
    reason = request.form['reason']
    work_content = request.form['work_content']
    
    # 解析日期JSON
    try:
        selected_dates = json.loads(dates_input)
    except:
        selected_dates = request.form.getlist('dates')
    
    if not selected_dates:
        flash('请至少选择一个加班日期')
        return redirect(url_for('index'))
    
    conn = get_db()
    
    # 检查批次是否存在且开放
    batch = conn.execute('SELECT * FROM overtime_batches WHERE id = ? AND is_open = 1', (batch_id,)).fetchone()
    if not batch:
        flash('该加班批次不存在或已关闭')
        return redirect(url_for('index'))
    
    # 检查日期是否在允许范围内
    allowed_dates = json.loads(batch['dates'])
    for d in selected_dates:
        if d not in allowed_dates:
            flash(f'日期 {d} 不在允许范围内')
            return redirect(url_for('index'))
    
    # 检查是否已存在申请（通过姓名+职级+批次判断）
    existing = conn.execute(
        'SELECT * FROM applications WHERE name = ? AND rank = ? AND batch_id = ?',
        (name, rank, batch_id)
    ).fetchone()
    
    selected_dates_json = json.dumps(selected_dates)
    
    if existing:
        conn.execute('''UPDATE applications 
                       SET name = ?, rank = ?, selected_dates = ?, reason = ?, work_content = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE name = ? AND rank = ? AND batch_id = ?''',
                    (name, rank, selected_dates_json, reason, work_content, name, rank, batch_id))
        flash('申请已更新')
    else:
        conn.execute('''INSERT INTO applications (batch_id, name, rank, selected_dates, reason, work_content)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (batch_id, name, rank, selected_dates_json, reason, work_content))
        flash('申请提交成功')
    
    conn.commit()
    return redirect(url_for('index'))

# 修改申请页面
@app.route('/edit/<int:app_id>', methods=['GET', 'POST'])
def edit_application(app_id):
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form['name']
        rank = request.form['rank']
        dates_input = request.form.get('dates', '[]')
        reason = request.form['reason']
        work_content = request.form['work_content']
        
        try:
            selected_dates = json.loads(dates_input)
        except:
            selected_dates = request.form.getlist('dates')
        
        if not selected_dates:
            flash('请至少选择一个加班日期')
            return redirect(url_for('index'))
        
        # 检查日期是否在允许范围内
        app = conn.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
        if not app:
            flash('申请不存在')
            return redirect(url_for('index'))
        
        batch = conn.execute('SELECT * FROM overtime_batches WHERE id = ?', (app['batch_id'],)).fetchone()
        allowed_dates = json.loads(batch['dates'])
        for d in selected_dates:
            if d not in allowed_dates:
                flash(f'日期 {d} 不在允许范围内')
                return redirect(url_for('index'))
        
        selected_dates_json = json.dumps(selected_dates)
        conn.execute('''UPDATE applications 
                       SET name = ?, rank = ?, selected_dates = ?, reason = ?, work_content = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?''',
                    (name, rank, selected_dates_json, reason, work_content, app_id))
        conn.commit()
        flash('申请已更新')
        return redirect(url_for('index'))
    
    # 获取申请信息
    app = conn.execute('''SELECT a.*, b.name as batch_name, b.dates as batch_dates
                           FROM applications a 
                           JOIN overtime_batches b ON a.batch_id = b.id
                           WHERE a.id = ?''', (app_id,)).fetchone()
    
    if not app:
        flash('申请不存在')
        return redirect(url_for('index'))
    
    app = dict(app)
    app['selected_dates'] = json.loads(app['selected_dates'])
    app['batch_dates'] = json.loads(app['batch_dates'])
    
    return render_template('edit_application.html', app=app)

# 删除申请
@app.route('/delete', methods=['POST'])
def delete_application():
    app_id = request.form.get('app_id')
    
    conn = get_db()
    
    app = conn.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
    if not app:
        flash('申请不存在')
        return redirect(url_for('index'))
    
    conn.execute('DELETE FROM applications WHERE id = ?', (app_id,))
    conn.commit()
    flash('申请已删除')
    
    return redirect(url_for('index'))

# 统计页面
@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    
    # 获取所有开放的批次
    batches = conn.execute('SELECT * FROM overtime_batches WHERE is_open = 1').fetchall()
    
    # 获取所有申请
    all_applications = conn.execute('''SELECT a.*, u.name, u.rank, b.name as batch_name
                                       FROM applications a 
                                       JOIN users u ON a.user_id = u.id
                                       JOIN overtime_batches b ON a.batch_id = b.id
                                       ORDER BY b.id, a.created_at''').fetchall()
    
    return render_template('stats.html', applications=all_applications, batches=batches)

# 管理后台
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db()
    
    # 添加新批次
    if request.method == 'POST' and 'action' in request.form:
        action = request.form['action']
        
        if action == 'add':
            name = request.form.get('name')
            dates_input = request.form.get('dates', '[]')
            if name and dates_input:
                try:
                    dates = json.loads(dates_input)
                    if dates:
                        dates_json = json.dumps(dates)
                        conn.execute('INSERT INTO overtime_batches (name, dates) VALUES (?, ?)', (name, dates_json))
                        flash('加班批次已创建')
                except:
                    flash('日期格式错误')
        
        elif action == 'toggle':
            batch_id = request.form.get('batch_id')
            conn.execute('UPDATE overtime_batches SET is_open = NOT is_open WHERE id = ?', (batch_id,))
            flash('状态已更新')
        
        elif action == 'delete':
            batch_id = request.form.get('batch_id')
            # 先删除相关申请
            conn.execute('DELETE FROM applications WHERE batch_id = ?', (batch_id,))
            conn.execute('DELETE FROM overtime_batches WHERE id = ?', (batch_id,))
            flash('加班批次已删除')
        
        elif action == 'update':
            batch_id = request.form.get('batch_id')
            name = request.form.get('name')
            dates_input = request.form.get('dates', '')
            if name and dates_input:
                # 解析逗号分隔的日期
                dates = [d.strip() for d in dates_input.split(',') if d.strip()]
                dates = [d.strip('[]"') for d in dates]  # 清理可能的JSON格式
                if dates:
                    dates_json = json.dumps(dates)
                    conn.execute('UPDATE overtime_batches SET name = ?, dates = ? WHERE id = ?', 
                               (name, dates_json, batch_id))
                    flash('加班批次已更新')
        
        elif action == 'update_user_role':
            user_id = request.form.get('user_id')
            is_admin = request.form.get('is_admin')
            # 防止管理员把自己降级
            if int(user_id) == session['user_id'] and int(is_admin) == 0:
                flash('不能将自己降为员工')
            else:
                conn.execute('UPDATE users SET is_admin = ? WHERE id = ?', (is_admin, user_id))
                flash('用户角色已更新')
        
        conn.commit()
    
    batches = conn.execute('SELECT * FROM overtime_batches ORDER BY created_at DESC').fetchall()
    applications = conn.execute('''SELECT a.*, u.name, u.rank, b.name as batch_name
                                   FROM applications a 
                                   JOIN users u ON a.user_id = u.id
                                   JOIN overtime_batches b ON a.batch_id = b.id
                                   ORDER BY b.id, u.rank, u.name''').fetchall()
    
    # 获取所有用户
    users = conn.execute('SELECT * FROM users ORDER BY is_admin DESC, id ASC').fetchall()
    
    return render_template('admin.html', batches=batches, applications=applications, users=users)

# 个人中心
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    
    if request.method == 'POST':
        # 修改姓名
        new_name = request.form.get('new_name')
        if new_name:
            conn.execute('UPDATE users SET name = ? WHERE id = ?', (new_name, session['user_id']))
            session['name'] = new_name
            flash('姓名修改成功')
        
        # 修改职级
        new_rank = request.form.get('new_rank')
        if new_rank:
            conn.execute('UPDATE users SET rank = ? WHERE id = ?', (new_rank, session['user_id']))
            session['rank'] = new_rank
            flash('职级修改成功')
        
        # 修改密码
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if user['password'] != old_password:
            flash('原密码错误')
        elif new_password:
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, session['user_id']))
            flash('密码修改成功')
        
        conn.commit()
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('profile.html', user=user)

# 批量创建员工（领导）
@app.route('/batch_create', methods=['GET', 'POST'])
def batch_create():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db()
    message = ''
    
    if request.method == 'POST':
        users_text = request.form.get('users_text', '')
        # 格式：用户名,密码,姓名,职级 每行一个
        lines = users_text.strip().split('\n')
        success_count = 0
        error_count = 0
        
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                username, password, name, rank = parts[0], parts[1], parts[2], parts[3]
                try:
                    conn.execute('INSERT INTO users (username, password, name, rank) VALUES (?, ?, ?, ?)',
                               (username, password, name, rank))
                    success_count += 1
                except:
                    error_count += 1
        
        conn.commit()
        message = f'成功创建 {success_count} 个账号，{error_count} 个失败'
    
    return render_template('batch_create.html', message=message)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
