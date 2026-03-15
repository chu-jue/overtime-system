# 🏢 加班审批系统

一个支持多批次的加班申请审批系统。

## 🚀 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/chu-jue/overtime-system.git
cd overtime-system

# 2. 一键启动
python3 start.py
```

或者手动启动：

```bash
# 安装依赖
pip install flask

# 启动服务
python3 app.py
```

## 📍 访问地址

- 本地: http://localhost:5001
- 服务器: http://你的服务器IP:5001

## 👤 账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 领导 | admin | admin123 |
| 员工 | 注册或批量创建 | - |

## 📱 功能

### 领导功能
- 创建/管理加班批次
- 设置开放日期（多选）
- 开启/关闭批次
- 批量创建员工
- 查看所有申请

### 员工功能
- 申请加班（多选日期）
- 修改申请
- 查看统计

## 🛠️ 技术栈

- Flask + SQLite

## 📝 职级

CL1 - CL8
