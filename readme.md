# 河流水质监控数据管理系统

[![python](https://img.shields.io/badge/python-3.12+-grey)](https://www.python.org/)
[![flask](https://img.shields.io/badge/flask-3.x-blue)](https://flask.palletsprojects.com/)
[![database](https://img.shields.io/badge/database-SQLite-003B57)](https://www.sqlite.org/)
[![license](https://img.shields.io/badge/license-MIT-brightgreen)](https://opensource.org/licenses/MIT)

> 一个基于 Flask + SQLAlchemy + SQLite 的本地化河流水质监测数据管理平台，支持多监测点管理、水质数据录入与查询、超标自动报警等核心功能。

---

## 系统功能

- **监测点管理**：新增、查询、删除监测点，支持经纬度与描述信息
- **水质数据录入**：支持单条与批量录入，记录余氯、电导率、pH、ORP、浊度五项指标
- **条件查询**：按监测点、时间范围、各指标数值范围灵活过滤数据
- **超标报警**：数据录入时自动与阈值比对，生成高/低超标报警日志
- **阈值管理**：支持动态修改各指标的上下限阈值
- **数据编辑**：修改已有水质记录时自动重新计算报警状态

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Flask 3.x |
| 数据库 ORM | Flask-SQLAlchemy 3.x + SQLAlchemy 2.x |
| 数据库 | SQLite |
| 数据库迁移 | Flask-Migrate 4.x (Alembic) |
| 前端 | 原生 HTML / CSS / JavaScript |
| 运行环境 | Python 3.12+ |

---

## 项目结构

```
water/
├── app.py                  # 应用工厂函数 create_app()
├── config.py               # 配置类（数据库路径、外键约束等）
├── extensions.py           # SQLAlchemy 实例
├── requirements.txt        # 依赖清单
├── .env.example            # 环境变量模板
│
├── models/                 # 数据模型层
│   ├── monitor_point.py    # 监测点
│   ├── water_record.py     # 水质记录
│   ├── alarm_log.py        # 报警日志
│   └── threshold.py        # 指标阈值
│
├── services/               # 业务逻辑层
│   ├── record_service.py   # 水质记录增删改查
│   └── alarm_service.py    # 报警检测与查询
│
├── routes/                 # 路由层（Flask Blueprint）
│   ├── points.py           # 监测点 API
│   ├── records.py          # 水质记录 API
│   ├── alarms.py           # 报警日志 API
│   ├── thresholds.py       # 阈值管理 API
│   └── stats.py            # 统计汇总 API
│
├── templates/
│   └── index.html          # 前端页面
├── static/
│   ├── css/style.css
│   └── js/main.js
│
└── migrations/             # 数据库迁移文件（Alembic）
    └── versions/
        └── 4154daf5f9ed_initial_schema.py
```

---

## 数据模型

```
monitor_points          水质记录 water_records
──────────────          ────────────────────────
id (PK)          1───* point_id (FK)
name                    id (PK)
latitude                timestamp
longitude               chlorine      余氯
description             conductivity  电导率
created_at              ph            酸碱度
                        orp           氧化还原电位
                        turbidity     浊度
                              │
                              │ 1───*
                        alarm_logs 报警日志
                        ───────────────────
                        id (PK)
                        record_id (FK)
                        indicator     指标名
                        actual_val    实测值
                        threshold_val 阈值
                        alarm_type    high / low
                        created_at

thresholds  指标阈值（独立表）
──────────────────────────────
id, indicator (unique), min_val, max_val, updated_at
```

---

## 快速启动

### 1. 克隆项目

```bash
# HTTPS
git clone https://github.com/tirthayatri/water-quality-monitor.git
cd water-quality-monitor
```

```bash
# SSH
git clone git@github.com:tirthayatri/water-quality-monitor.git
cd water-quality-monitor
```

### 2. 创建并激活虚拟环境

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

> ⚠️ **必须确认虚拟环境已激活**
>
> 激活成功后，命令行前缀会出现 `(venv)` 字样，如：
> ```
> (venv) PS D:\xxxxx\xxxxx\water-quality-monitor>
> ```
> 如果没有看到 `(venv)`，说明虚拟环境**未激活**，后续所有 `pip install` 和 `flask` 命令都会作用在系统 Python 上，导致 `No module named 'flask_migrate'` 等报错

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

安装完成后可执行以下命令确认关键包已就位：

```bash
pip show flask flask-sqlalchemy flask-migrate
```

Flask/Flask-SQLAlchemy/Flask-Migrate三个包均有输出则说明安装正常

### 4. 配置环境变量

```powershell
# Windows
copy .env.example .env
```

```bash
# macOS / Linux
cp .env.example .env
```

按需修改 `.env` 中的 `SECRET_KEY`。

### 5. 创建 instance 目录

 在新环境克隆后需手动创建数据库所在的 `instance/` 目录：

 ```powershell
 # Windows PowerShell
 New-Item -ItemType Directory -Path instance
 ```

 ```bash
 # macOS / Linux
 mkdir instance
 ```

 创建后重新执行 `flask db upgrade` 即可。

### 6. 初始化数据库

```bash
flask db upgrade
```

执行成功后将在 `instance/` 目录下生成 `water.db`，并初始化默认阈值

### 7. 启动服务

```bash
flask run
```

浏览器访问 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## API 接口文档

### 监测点 `/api/points`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/points` | 获取所有监测点 |
| GET | `/api/points/<id>` | 获取单个监测点 |
| POST | `/api/points` | 新增监测点 |
| DELETE | `/api/points/<id>` | 删除监测点（级联删除记录和报警） |

**新增监测点请求体示例：**
```json
{
  "name": "上游监测站A",
  "latitude": 30.5728,
  "longitude": 104.0668,
  "description": "H市上游主干道监测点"
}
```

---

### 水质记录 `/api/records`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/records` | 条件查询记录 |
| GET | `/api/records/<id>` | 获取单条记录 |
| POST | `/api/records` | 新增单条记录 |
| POST | `/api/records/batch` | 批量新增记录 |
| PUT | `/api/records/<id>` | 修改记录 |
| DELETE | `/api/records/<id>` | 删除记录 |

**查询参数（均可选）：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `point_id` | 按监测点筛选 | `?point_id=1` |
| `date_from` | 起始日期 | `?date_from=2024-01-01` |
| `date_to` | 截止日期 | `?date_to=2024-12-31` |
| `ph_min` / `ph_max` | pH 范围 | `?ph_min=6.5&ph_max=8.5` |
| `chlorine_min` / `chlorine_max` | 余氯范围 | |
| `conductivity_min` / `conductivity_max` | 电导率范围 | |
| `orp_min` / `orp_max` | ORP 范围 | |
| `turbidity_min` / `turbidity_max` | 浊度范围 | |

**响应字段说明：**

列表接口每条记录额外包含 `has_alarm` 布尔字段，表示该条记录是否存在报警，由后端单次 IN 查询计算，前端无需再单独拉取全量报警数据。

**新增记录请求体示例：**
```json
{
  "point_id": 1,
  "chlorine": 0.15,
  "conductivity": 350.0,
  "ph": 7.2,
  "orp": 320.0,
  "turbidity": 1.5,
  "timestamp": "2024-06-01 08:00:00"
}
```

---

### 统计汇总 `/api/stats`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats` | 获取系统核心统计数据 |

**响应示例：**
```json
{
  "points":      3,
  "records":     120,
  "alarms":      15,
  "high_alarms": 10,
  "low_alarms":  5
}
```

> 总览页使用此接口替代拉取全量记录/报警数据，适合数据量较大的场景。

---

### 报警日志 `/api/alarms`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/alarms` | 查询报警记录 |

**查询参数：**

| 参数 | 说明 |
|------|------|
| `point_id` | 按监测点筛选 |
| `indicator` | 按指标筛选（chlorine / ph / orp 等） |

---

### 阈值管理 `/api/thresholds`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/thresholds` | 获取所有阈值 |
| PUT | `/api/thresholds/<indicator>` | 修改指定指标阈值 |

**默认阈值：**

| 指标 | 最小值 | 最大值 | 单位 |
|------|--------|--------|------|
| chlorine（余氯） | 0.05 | 0.3 | mg/L |
| conductivity（电导率） | 0.0 | 1000.0 | μS/cm |
| ph（酸碱度） | 6.5 | 8.5 | — |
| orp（氧化还原电位） | 200.0 | 500.0 | mV |
| turbidity（浊度） | 0.0 | 3.0 | NTU |

---

## 注意事项

- 数据库文件 `instance/water.db` 不含在仓库中，首次运行 `flask db upgrade` 时自动创建
- `instance/` 目录本身也不含在仓库中（空目录不被 Git 追踪），克隆后需手动创建，见第 5 步说明
- `.env` 文件不含在仓库中，请根据 `.env.example` 自行创建并修改 `SECRET_KEY`
- **`SECRET_KEY` 未在 `.env` 中设置时，系统启动时会打印警告并使用不安全的默认值，生产环境中请务必配置**
- 本项目为本地开发环境，不适用于直接生产部署

---

## 主要变更记录

### 事务安全修复
`alarm_service.check_and_log_alarms` 不再内部 `commit`，commit 权统一交由调用方持有。批量写入接口现在在全部记录处理完成后一次性提交，任何一条失败均可完整回滚，不再出现部分提交的情况。

### 性能优化
- 总览页改用 `/api/stats` 聚合接口（COUNT 查询），不再拉取全量记录和报警数据
- 水质数据列表的"超标"状态由后端通过单次 IN 查询附加 `has_alarm` 字段返回，前端不再额外请求全量报警

### 安全改进
- `showMsg` 显示服务端消息时改用 `textContent` 替代 `innerHTML`，消除 XSS 风险

### 其他改进
- 批量录入内联表格初始化改为直接异步请求监测点数据，去除了原有轮询 + 超时兜底逻辑
- `SECRET_KEY` 未配置时启动时打印 `warnings.warn` 提示
- 删除监测点和水质记录操作补全了错误处理，服务端报错时前端不再静默失败