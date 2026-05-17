# 河流水质监控数据管理系统

[![python](https://img.shields.io/badge/python-3.12+-grey)](https://www.python.org/)
[![flask](https://img.shields.io/badge/flask-3.x-blue)](https://flask.palletsprojects.com/)
[![database](https://img.shields.io/badge/database-SQLite-003B57)](https://www.sqlite.org/)
[![license](https://img.shields.io/badge/license-MIT-brightgreen)](https://opensource.org/licenses/MIT)

> 一个基于 Flask + SQLAlchemy + SQLite 的本地化河流水质监测数据管理平台，支持多监测点管理、水质数据录入与查询、超标自动报警，并集成基于 scikit-learn 的"未来 24 小时综合预测"模块

---

## 系统功能

- **监测点管理**：新增、查询、删除监测点，支持经纬度与描述信息
- **水质数据录入**：支持单条与批量录入，记录余氯、电导率、pH、ORP、浊度五项指标
- **条件查询**：按监测点、时间范围、各指标数值范围灵活过滤数据
- **超标报警**：数据录入时自动与阈值比对，生成高/低超标报警日志
- **阈值管理**：支持动态修改各指标的上下限阈值
- **数据编辑**：修改已有水质记录时自动重新计算报警状态
- **AI 综合预测**：基于历史数据训练RandomForest + IsolationForest + MultiOutputRegressor，输出未来 24h 告警概率、异常检测分数、下一时刻指标预测值
- **硬件自适应启动**：自动探测独立显卡 —— 有 GPU 的设备首次访问总览页自动训练并启用 AI；纯 CPU 设备默认关闭 AI，由用户点击「训练」按钮按需启动，避免在弱机型上长时间阻塞
- **可视化集成**：总览页 AI 预测卡片按风险等级染色；趋势曲线叠加历史染色点 + 预测虚线 + 持续超标时段红色背景带

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Flask 3.x |
| 数据库 ORM | Flask-SQLAlchemy 3.x + SQLAlchemy 2.x |
| 数据库 | SQLite |
| 数据库迁移 | Flask-Migrate 4.x (Alembic) |
| 机器学习 | scikit-learn 1.x（RandomForest / IsolationForest / MultiOutputRegressor）+ numpy + joblib |
| 前端 | 原生 HTML / CSS / JavaScript + ECharts 5 |
| 运行环境 | Python 3.12+ |

---

## 项目结构

```
water/
├── app.py                  # 应用工厂函数 create_app()
├── config.py               # 配置类
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
│   ├── alarm_service.py    # 报警检测与查询
│   └── predictor.py        # AI 综合预测：分类 + 异常检测 + 趋势回归
│
├── routes/                 # 路由层（Flask Blueprint）
│   ├── points.py           # 监测点 API
│   ├── records.py          # 水质记录 API
│   ├── alarms.py           # 报警日志 API
│   ├── thresholds.py       # 阈值管理 API
│   ├── stats.py            # 统计汇总 API
│   └── predict.py          # AI 综合预测 API
│
├── templates/
│   └── index.html          # 前端页面
├── static/
│   ├── css/style.css
│   └── js/main.js
│
├── test/
│   └── seed.py             # 演示数据生成脚本
│
├── instance/               # 运行时数据目录
│   ├── water.db            # SQLite 数据库
│   └── predictor.pkl       # 训练完成的模型
└── migrations/             # 数据库迁移文件
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

### 5. 初始化数据库

```bash
flask db upgrade
```

执行成功后将在 `instance/` 目录下生成 `water.db`，并初始化默认阈值

### 6. 写入演示数据

仓库默认带有 `instance/water.db`。如需重新生成，可在项目根目录执行：

```bash
python test/seed.py
```

> ⚠️ 该脚本会先**清空** `monitor_points / water_records / alarm_logs` 三张表再写入新数据，请确保不会覆盖正在使用的真实数据。

### 7. 启动服务

```bash
flask run
```

浏览器访问 [http://127.0.0.1:5000](http://127.0.0.1:5000)

> **AI 模块启动策略**：
> - **检测到独立显卡**（NVIDIA / AMD Radeon RX / Intel Arc 等）：首次打开总览页时自动训练并将模型缓存到 `instance/predictor.pkl`
> - **仅集显 / 核显**：AI 默认关闭，总览页"综合预测"卡片显示 `[CPU 模式]` 提示；点击右上角「训练」按钮后才会启动训练，训练完成后该按钮变为「重新训练」
> - 训练好的 `predictor.pkl` 一旦存在，后续启动会直接加载缓存，与硬件无关

---

## API 接口文档

### 监测点 `/api/points`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/points` | 获取所有监测点 |
| GET | `/api/points/<id>` | 获取单个监测点 |
| POST | `/api/points` | 新增监测点 |
| DELETE | `/api/points/<id>` | 删除监测点 |

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

### AI 综合预测 `/api/predict`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/predict` | 返回所有监测点的三路预测信号 |
| GET  | `/api/predict?point_id=N` | 仅返回指定监测点 |
| POST | `/api/predict/train` | 手动训练并返回评估指标 |
| GET  | `/api/predict/info`  | 返回模型元数据 + 硬件检测结果 + 模型就绪状态 |

**`/api/predict/info` 响应字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `window` / `horizon_hours` / `indicators` | — | 模型配置 |
| `has_gpu` | bool | 是否检测到独立显卡 |
| `model_ready` | bool | 模型是否已训练（缓存或磁盘可加载） |
| `metrics` | object \| null | 训练评估指标；未训练时为 `null`（不会触发训练） |

**`/api/predict` 在 CPU 设备且模型未训练时的响应：** HTTP `503` + `{"error": "...", "model_ready": false, "has_gpu": false}`

**响应示例（监测点 3）：**
```json
{
  "point_id": 3,
  "name": "监测点3",
  "last_timestamp": "2026-05-10 04:15:46",
  "based_on_records": 3,
  "classification": {
    "probability": 0.4295,
    "risk_level": "medium"
  },
  "anomaly": {
    "score": 0.5252,
    "is_anomaly": true
  },
  "forecast": {
    "next_values": {
      "chlorine": 0.142, "conductivity": 644.0,
      "ph": 6.93, "orp": 327.8, "turbidity": 1.48
    },
    "indicators_at_risk": [],
    "max_breach_ratio": 0.0
  }
}
```

模型未训练时：**有独立显卡**则首次调用接口自动训练；**仅 CPU** 则返回 503，由用户主动调用 `/api/predict/train` 触发。详细字段含义与阈值规则见下文 [AI 综合预测模块]。

---

## AI 综合预测模块

总览页"AI 综合预测"卡片对每个监测点并行运行 **三个独立模型**，输出三路独立信号 + 时序图表叠加。三路信号设计上互补 —— 分歧时往往揭示不同时间尺度或不同视角下的风险。

### 三路信号一览

| 信号字段 | 来源模型 | 判定阈值 |
|---|---|---|
| `classification.probability` | RandomForestClassifier | 0–1 概率值（连续） |
| `classification.risk_level`  | 同上                 | `≥0.50 → high`，`0.30–0.50 → medium`，`<0.30 → low` |
| `anomaly.score`              | IsolationForest      | 0–1 异常程度（sigmoid 归一化） |
| `anomaly.is_anomaly`         | 同上                 | `decision_function < 0` ⇔ `score > 0.5` |
| `forecast.next_values`       | MultiOutputRegressor(RandomForestRegressor) | 5 个指标的预测数值 |
| `forecast.indicators_at_risk`| 同上                 | 预测值越过 `thresholds` 表中对应指标的 min / max |
| `forecast.max_breach_ratio`  | 同上                 | 预测值越界距离 / (max−min)，归一化越界程度 |

### 1. 分类: 未来 24 小时告警概率

- **算法**：`RandomForestClassifier`（120 棵树，深度 8，`class_weight='balanced'`）
- **训练数据来源**：`water_records` + `alarm_logs` 表
  - 对每条记录构造 32 维特征
  - 标签 = 该记录之后 24 小时窗口内是否存在任意指标越界（`alarm_logs` 中是否有对应记录）
- **判定规则**（前端卡片显示）：

  | 概率区间 | risk_level | 卡片左边框 / 徽章颜色 |
  |---|---|---|
  | `prob ≥ 0.50` | `high`   | 红色 (#e53935) |
  | `0.30 ≤ prob < 0.50` | `medium` | 橙色 (#f59e0b) |
  | `prob < 0.30` | `low`    | 绿色 (#2e7d32) |

  阈值取自 `services/predictor.py` 第 188 行：`'high' if prob >= 0.50 else ('medium' if prob >= 0.30 else 'low')`。
- **诚实评估**：随机 5 折 CV ROC-AUC ≈ 0.78，PR-AUC ≈ 0.35；时间序列 5 折 CV ROC-AUC ≈ 0.58（时间外推能力弱，受异常事件稀疏性限制）

### 2. 异常检测: 当前样本是否罕见

- **算法**：`IsolationForest`（120 棵树，`contamination` = 训练集正样本率 ≈ 0.15）
- **数据来源**：与分类共用同一份 32 维特征，但 **无监督训练**（不使用任何标签）
- **`anomaly.score` 计算**：
  ```
  raw = iforest.decision_function(feats)        # 正数=正常, 负数=异常, 决策边界=0
  score = 1 / (1 + exp(5 × raw))                # sigmoid 映射到 [0, 1]
  ```
  - `raw = 0` → `score = 0.5`（决策边界）
  - `raw < 0` → `score → 1`（越异常）
  - `raw > 0` → `score → 0`（越典型）
- **`is_anomaly` 判定**：直接使用 `iforest.predict() == -1`，**等价于 `score > 0.5`**
  - sklearn 的 `decision_function` 内部已做 `score_samples - offset_`，`offset_` 由 `contamination` 决定，因此 `raw == 0` 自然就是异常 / 正常的分界
  - 我们的 sigmoid `1/(1+exp(5·raw))` 把 `raw=0` 映射到 0.5，所以 `score > 0.5` 与 `is_anomaly = true` 一一对应
- **设计意图**：与分类器互补 —— 分类器学的是"过去出现告警时长什么样"，异常检测发现的是"训练数据中罕见的特征组合"，可以捕捉到从未见过的异常模式

### 3. 趋势回归: 下一时刻指标值预测

- **算法**：`MultiOutputRegressor(RandomForestRegressor(n_estimators=80, max_depth=8))`
- **数据来源**：与分类共用 32 维特征，但 **目标变量改为下一条记录的 5 个指标值**（每条样本 5 维 Y）
- **`forecast.next_values`**：模型直接输出的下一记录预测值
- **`forecast.indicators_at_risk` 判定规则**：
  ```
  for each indicator in [chlorine, conductivity, ph, orp, turbidity]:
      if predicted > thresholds[indicator].max  →  加入 at_risk
      if predicted < thresholds[indicator].min  →  加入 at_risk
  ```
  阈值直接取自 `thresholds` 表（即用户在"阈值设置"页配置的值）
- **`forecast.max_breach_ratio`**：所有越界指标中，最大归一化越界距离
  ```
  breach_ratio = max((pred - max) / (max - min), (min - pred) / (max - min), 0)
  ```
  例如阈值范围 `[0, 1000]`，预测值 1080，则 `breach_ratio = 0.08`（越界 8%）

### 32 维特征工程

所有三个模型共用同一份特征向量，避免训练数据漂移：

| 维度 | 说明 | 数据来源 |
|---|---|---|
| 5 | 当前 5 个指标的瞬时值 | `water_records` 最新一条 |
| 5 | 距阈值中点的归一化偏离 | `thresholds` 表 + 当前记录 |
| 5 | 滑动窗口（最近 3 条）均值 | `water_records` 最近 3 条 |
| 5 | 滑动窗口极差（max−min） | 同上 |
| 5 | 滑动窗口斜率（last−first） | 同上 |
| 3 | 时间编码：hour 的 sin/cos + weekday | 当前时间戳 |
| 2 | 自身历史告警计数：过去 24h、过去 7d | `alarm_logs` (该监测点) |
| 2 | 跨点空间联动：其他监测点过去 24h、过去 4-12h 滞后 | `alarm_logs` (其他监测点) |

最后一组 "跨点滞后窗口" 对应模拟环境中"工业排放 → 下游 4-16h 延迟"的物理传导，引入后时间序列 PR-AUC 提升约 24%。

### 模型生命周期

- **硬件自适应启动**：第一次调用 `/api/predict` 时若 `instance/predictor.pkl` 不存在
  - **检测到独立显卡** → 自动训练
  - **仅 CPU** → 跳过自动训练，接口返回 503 + `model_ready: false`；前端总览页显示 `[CPU 模式] AI 未启用` 提示
- **独立显卡探测**：优先 `nvidia-smi`；Windows 回落 `Get-CimInstance Win32_VideoController` 并按关键字过滤集显；Linux 回落 `lspci`；结果模块级缓存，整个进程生命周期只探测一次
- **手动训练**：调用 `POST /api/predict/train` 或前端"AI 综合预测"卡片右上角按钮（首次显示「▶ 训练」，已有模型后变为「↻ 重新训练」）
- **持久化**：训练完成后 `joblib` 序列化到 `instance/predictor.pkl`（已 gitignore，不入库）。一旦该文件存在，后续启动直接加载，与硬件无关
- **缓存**：进程内字典缓存模型对象，避免每次推理重新加载

### 时序图表的可视化叠加

总览页"最近水质趋势"图集成了三类视觉信号：

| 元素 | 数据来源 | 含义 |
|---|---|---|
| 绿色平滑折线 | `/api/records?point_id=N` | 历史轨迹 |
| 绿色 ● / 红色 ● | 每条记录的 `has_alarm` 字段 | 单点正常 / 已超标 |
| 红色半透明背景带 | 前端扫描连续 ≥ 2 条越界 | 持续超标时段（"事件级"风险，非单点抖动） |
| 红/橙水平虚线 | `/api/thresholds` | 上限 / 下限阈值参考线 |
| 蓝色虚线 + 蓝菱形 ◆ | `forecast.next_values[indicator]` | 24h 预测点（预测正常） |
| 红色虚线 + 红菱形 ◆ | 同上 + `indicators_at_risk` 包含当前指标 | 24h 预测点（预测越界） |

---

## 注意事项

- `instance/water.db` **已随仓库提供演示数据**。如需空库可删除该文件后执行 `flask db upgrade`
- `instance/predictor.pkl` 已通过 `*.pkl` 规则忽略；有独立显卡时首次推理自动训练生成，纯 CPU 设备需手动点击「训练」按钮
- `instance/` 目录已通过 `.gitkeep` 纳入版本控制，克隆后无需手动创建
- `.env` 文件不含在仓库中，请根据 `.env.example` 自行创建并修改 `SECRET_KEY`
- **`SECRET_KEY` 未在 `.env` 中设置时，系统启动时会打印警告并使用不安全的默认值，生产环境中请务必配置**
- AI 预测模块的评估指标显示 **时间序列 5 折 CV ROC-AUC ≈ 0.58**，外推能力受异常事件稀疏性限制，仅作演示用途，不适用于真实业务决策
- 本项目为本地开发环境，不适用于直接生产部署

---

## 主要变更记录

### AI 模块硬件自适应启动
- 新增独立显卡检测（`nvidia-smi` / Windows WMI / Linux `lspci`），结果模块级缓存
- 仅 CPU 设备首次访问总览页不再阻塞自动训练；`/api/predict` 在模型未就绪时返回 503 + `model_ready`/`has_gpu`，由用户按需点击「训练」按钮启动
- `/api/predict/info` 暴露 `has_gpu` / `model_ready`，且不再因查询元数据而隐式触发训练
- 前端按钮文案与状态联动：未训练显示「▶ 训练」、训练中禁用并显示「训练中…」、训练完成自动切换为「↻ 重新训练」

### AI 综合预测模块（新增）
- **三模型集成**：RandomForestClassifier（24h 告警概率）+ IsolationForest（无监督异常分数）+ MultiOutputRegressor(RandomForestRegressor)（下一时刻 5 指标值预测），三路独立信号互补
- **32 维特征工程**：覆盖瞬时值、距阈值偏离、滑动窗口统计、时间编码、自身/跨监测点历史告警计数；上下游传导建模（4-12h 滞后特征）使时间序列 PR-AUC 提升约 24%
- **诚实评估**：同时给出训练精度、随机 5 折 CV、时间序列 5 折 CV，明确标注模型外推局限
- **API**：单一 `/api/predict` 接口返回三路信号；`/api/predict/train` 支持手动重训

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