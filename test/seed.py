"""
重置数据库并填充5个监测点 × 540 条模拟数据（每 4 小时一次，跨度 90 天，含合理超标比例）。
运行方式: python test/seed.py    (在项目根目录执行)
"""
import sys
import os
import random
from datetime import datetime, timedelta, timezone

# 该脚本位于 test/，需要把项目根目录加入 sys.path 才能 import app/extensions/models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import MonitorPoint, WaterRecord, AlarmLog, Threshold

random.seed(42)

# ── 阈值常量（与 app.py seed_thresholds 保持一致）──────────────────────────
THRESHOLDS = {
    'chlorine':     {'min': 0.05, 'max': 0.30},
    'conductivity': {'min': 0.0,  'max': 1000.0},
    'ph':           {'min': 6.5,  'max': 8.5},
    'orp':          {'min': 200.0,'max': 500.0},
    'turbidity':    {'min': 0.0,  'max': 3.0},
}

# ── 采样设置 ───────────────────────────────────────────────────────────────
DAYS               = 90
INTERVAL_HOURS     = 4                                # 每 4 小时一条
JITTER_MINUTES     = 25                               # 时间小幅抖动
RECORDS_PER_POINT  = DAYS * (24 // INTERVAL_HOURS)    # 90 * 6 = 540

# ── 监测点定义 ─────────────────────────────────────────────────────────────
POINTS = [
    {'name': '监测点1', 'latitude': 31.2304, 'longitude': 121.4737, 'description': '上游进水口'},
    {'name': '监测点2', 'latitude': 31.2200, 'longitude': 121.4800, 'description': '中游水处理站'},
    {'name': '监测点3', 'latitude': 31.2100, 'longitude': 121.4900, 'description': '工业区排放口'},
    {'name': '监测点4', 'latitude': 31.2000, 'longitude': 121.5000, 'description': '居民区供水点'},
    {'name': '监测点5', 'latitude': 31.1900, 'longitude': 121.5100, 'description': '下游出水口'},
]

# ── 各监测点正常值范围（均值, 标准差），生成正态分布后 clip 到合理区间 ──────
NORMAL_PROFILES = [
    # 监测点1 上游进水口：水质较好
    {'ph': (7.3, 0.15), 'chlorine': (0.16, 0.04), 'conductivity': (420, 60),  'orp': (370, 30), 'turbidity': (0.8, 0.3)},
    # 监测点2 水处理站：处理后出水，最为稳定
    {'ph': (7.5, 0.10), 'chlorine': (0.20, 0.03), 'conductivity': (350, 50),  'orp': (420, 25), 'turbidity': (0.3, 0.15)},
    # 监测点3 工业区：波动大，超标最多
    {'ph': (7.1, 0.40), 'chlorine': (0.14, 0.06), 'conductivity': (620, 150), 'orp': (330, 60), 'turbidity': (1.5, 0.6)},
    # 监测点4 居民区：基本达标，偶有异常
    {'ph': (7.4, 0.18), 'chlorine': (0.17, 0.04), 'conductivity': (480, 80),  'orp': (360, 35), 'turbidity': (0.9, 0.3)},
    # 监测点5 下游出水口：受上游影响，略有劣化
    {'ph': (7.2, 0.25), 'chlorine': (0.13, 0.05), 'conductivity': (560, 100), 'orp': (340, 45), 'turbidity': (1.2, 0.5)},
]

# ── 各监测点的"事件强度"（每个时段触发一次超标事件的概率）────────────────
# 事件持续 1~3 条记录（即 4~12 小时），并随机选 1~2 个指标越界
ANOMALY_PROFILES = [
    # 监测点1：偶发，主要是 turbidity / ph
    {'event_prob': 0.018, 'event_len': (1, 2), 'preferred': ['turbidity', 'ph'], 'multi_prob': 0.10},
    # 监测点2：极少
    {'event_prob': 0.008, 'event_len': (1, 1), 'preferred': ['ph', 'turbidity'], 'multi_prob': 0.0},
    # 监测点3：高发，常多指标
    {'event_prob': 0.060, 'event_len': (1, 3), 'preferred': ['conductivity', 'turbidity', 'ph', 'orp', 'chlorine'], 'multi_prob': 0.45},
    # 监测点4：低发
    {'event_prob': 0.015, 'event_len': (1, 2), 'preferred': ['turbidity', 'chlorine', 'ph'], 'multi_prob': 0.05},
    # 监测点5：中发
    {'event_prob': 0.030, 'event_len': (1, 2), 'preferred': ['turbidity', 'conductivity', 'ph', 'orp', 'chlorine'], 'multi_prob': 0.20},
]

# ── 上下游传导：上游异常事件后，下游在指定时延窗口内触发概率倍增 ──────────
# point_id -> {'from': 上游 point_id, 'delay_h': (lo, hi), 'boost': 概率倍数}
PROPAGATION = {
    2: {'from': 1, 'delay_h': (2, 8),  'boost': 3.0},   # 上游进水 → 处理站（处理后会衰减）
    4: {'from': 2, 'delay_h': (2, 8),  'boost': 3.0},   # 处理站 → 居民供水
    5: {'from': 3, 'delay_h': (4, 16), 'boost': 6.0},   # 工业排放 → 下游出水（最强联动）
}


def normal_val(mean, std, lo, hi):
    return round(max(lo, min(hi, random.gauss(mean, std))), 3)


def generate_normal(profile):
    return {
        'ph':           normal_val(*profile['ph'],           6.5, 8.5),
        'chlorine':     normal_val(*profile['chlorine'],     0.05, 0.30),
        'conductivity': normal_val(*profile['conductivity'], 50,   980),
        'orp':          normal_val(*profile['orp'],          210,  490),
        'turbidity':    normal_val(*profile['turbidity'],    0.05, 2.8),
    }


def push_out_of_range(indicator):
    """生成一个"刚好"超标的越界值——避免极端异常值。"""
    t = THRESHOLDS[indicator]
    direction = random.choice(['high', 'low'])
    if indicator == 'conductivity' or indicator == 'turbidity':
        # 这两个下限是 0，强制 high
        direction = 'high'
    if direction == 'high':
        return round(t['max'] * random.uniform(1.05, 1.40), 3)
    else:
        # 下限可能很小，避免负值
        low = max(t['min'] * random.uniform(0.20, 0.85), 0.0)
        return round(low, 3)


def inject_anomaly(values, profile):
    """在 values 上注入 1~2 个指标的越界。"""
    indicators = list(profile['preferred'])
    random.shuffle(indicators)
    n = 2 if random.random() < profile['multi_prob'] else 1
    chosen = indicators[:n]
    for ind in chosen:
        values[ind] = push_out_of_range(ind)
    return chosen


def build_alarms(record, values):
    alarms = []
    for indicator, val in values.items():
        t = THRESHOLDS[indicator]
        if val < t['min']:
            alarms.append(AlarmLog(record_id=record.id, indicator=indicator,
                                   actual_val=val, threshold_val=t['min'], alarm_type='low'))
        elif val > t['max']:
            alarms.append(AlarmLog(record_id=record.id, indicator=indicator,
                                   actual_val=val, threshold_val=t['max'], alarm_type='high'))
    return alarms


def main():
    app = create_app()
    with app.app_context():
        print("清空现有数据...")
        db.session.query(AlarmLog).delete()
        db.session.query(WaterRecord).delete()
        db.session.query(MonitorPoint).delete()
        db.session.commit()

        print(f"创建 {len(POINTS)} 个监测点...")
        points = []
        for pd in POINTS:
            p = MonitorPoint(**pd)
            db.session.add(p)
            points.append(p)
        db.session.commit()

        base_time = datetime.now(timezone.utc) - timedelta(days=DAYS)
        total_records = 0
        total_alarms  = 0
        upstream_anomaly_ts = {}  # point_id -> [事件起始时间戳]，供下游查询

        for i, point in enumerate(points):
            normal_profile  = NORMAL_PROFILES[i]
            anomaly_profile = ANOMALY_PROFILES[i]
            prop            = PROPAGATION.get(point.id)
            upstream_ts     = sorted(upstream_anomaly_ts.get(prop['from'], [])) if prop else []
            print(f"  生成 {point.name} 的 {RECORDS_PER_POINT} 条记录...")

            event_remaining = 0
            this_anomaly_ts = []

            for k in range(RECORDS_PER_POINT):
                ts = base_time + timedelta(
                    hours=k * INTERVAL_HOURS,
                    minutes=random.randint(-JITTER_MINUTES, JITTER_MINUTES),
                )

                values = generate_normal(normal_profile)

                # 上下游传导：若处于上游事件的延迟窗口，提升触发概率
                event_prob = anomaly_profile['event_prob']
                if prop and upstream_ts:
                    lo_d, hi_d = prop['delay_h']
                    for u_ts in upstream_ts:
                        if u_ts + timedelta(hours=lo_d) <= ts <= u_ts + timedelta(hours=hi_d):
                            event_prob = min(0.5, event_prob * prop['boost'])
                            break

                if event_remaining == 0 and random.random() < event_prob:
                    lo, hi = anomaly_profile['event_len']
                    event_remaining = random.randint(lo, hi)
                    this_anomaly_ts.append(ts)   # 记录事件起始

                if event_remaining > 0:
                    inject_anomaly(values, anomaly_profile)
                    event_remaining -= 1

                record = WaterRecord(
                    point_id     = point.id,
                    timestamp    = ts,
                    ph           = values['ph'],
                    chlorine     = values['chlorine'],
                    conductivity = values['conductivity'],
                    orp          = values['orp'],
                    turbidity    = values['turbidity'],
                )
                db.session.add(record)
                db.session.flush()

                for a in build_alarms(record, values):
                    db.session.add(a)
                    total_alarms += 1
                total_records += 1

            upstream_anomaly_ts[point.id] = this_anomaly_ts

        db.session.commit()
        print(f"\n完成！共写入 {total_records} 条水质记录，{total_alarms} 条报警日志。")
        print("\n各监测点超标汇总:")
        for point in points:
            cnt = AlarmLog.query.join(WaterRecord).filter(WaterRecord.point_id == point.id).count()
            rec = WaterRecord.query.filter_by(point_id=point.id).count()
            rate = cnt / rec if rec else 0
            print(f"  {point.name}（{point.description}）: {rec} 条记录 / {cnt} 条超标 ({rate:.1%})")


if __name__ == '__main__':
    main()
