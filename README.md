# 加班审批系统 (Overtime Approval System)

一个简单的加班申请审批系统，支持员工提交加班申请、领导审批管理。

## 功能

### 员工功能
- 填写个人信息（职级、姓名）
- 提交加班申请（加班日期、理由、工作内容）
- 每天只能提交一次，提交后可修改
- 查看当日加班统计

### 领导功能
- 设置开放日期（某一天开放申请）
- 设置加班日期（申请的是哪一天的加班）
- 设置申请开始/结束时间
- 查看所有员工加班申请

## 技术栈

- Flask (Web 框架)
- SQLite (数据库)
- HTML/CSS (前端)

## 本地运行

```bash
pip install flask

python app.py
```

访问 http://localhost:5000

## 默认账号

- 领导账号：`admin` / `admin123`
- 员工账号：注册后使用

## 目录结构

```
overtime-system/
├── app.py          # 主应用
├── database.db     # SQLite数据库
├── templates/      # HTML模板
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── apply.html
│   ├── admin.html
│   └── stats.html
└── static/         # 静态文件
    └── style.css
```
