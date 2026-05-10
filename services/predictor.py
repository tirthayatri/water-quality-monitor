"""未来 24 小时水质综合预测：分类 + 异常检测 + 趋势回归三路结合。

(1) 分类  : RandomForestClassifier — "未来 24h 是否会出现指标越界" 概率
(2) 异常  : IsolationForest         — 无监督异常分数 (与分类互补，捕捉未见过的异常模式)
(3) 趋势  : MultiOutputRegressor    — 预测下一条记录的 5 个指标值，并标记潜在越界

特征 (32 维):
- 当前 5 个指标 + 距阈值中点的归一化偏离 (10 维)
- 滑动窗口 (3 条) 均值 / 极差 / 一阶斜率 (15 维)
- 时间: hour 的 sin/cos + weekday (3 维)
- 自身历史告警: 过去 24h / 7d 该点告警数 (2 维)
- 跨点空间联动: 其他点过去 24h 总告警 + 4-12h 滞后告警 (2 维)
"""
import os
import joblib
import numpy as np
from bisect import bisect_left
from datetime import timedelta

from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor,
                              IsolationForest)
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import mean_absolute_error

from extensions import db
from models import MonitorPoint, WaterRecord, AlarmLog, Threshold

INDICATORS    = ['chlorine', 'conductivity', 'ph', 'orp', 'turbidity']
WINDOW        = 3
HORIZON_HOURS = 24
ANOMALY_SCALE = 5.0  # IsolationForest decision_function 的 sigmoid 斜率

MODEL_PATH = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
    'instance', 'predictor.pkl'
)

_cache = {'pipe': None, 'iforest': None, 'regressor': None, 'metrics': None}


# ─── 特征工程 ──────────────────────────────────────────────────────────────
def _vals(r):
    return np.array([getattr(r, ind) for ind in INDICATORS], dtype=float)


def _time_features(ts):
    hour = ts.hour + ts.minute / 60.0
    return [np.sin(2 * np.pi * hour / 24),
            np.cos(2 * np.pi * hour / 24),
            float(ts.weekday())]


def _alarm_counts(sorted_alarm_ts, ts):
    upper = bisect_left(sorted_alarm_ts, ts)
    lo24  = bisect_left(sorted_alarm_ts, ts - timedelta(hours=24))
    lo7d  = bisect_left(sorted_alarm_ts, ts - timedelta(days=7))
    return [upper - lo24, upper - lo7d]


def _cross_alarm_counts(other_alarm_ts, ts):
    upper_24h = bisect_left(other_alarm_ts, ts)
    lo_24h    = bisect_left(other_alarm_ts, ts - timedelta(hours=24))
    lo_lag    = bisect_left(other_alarm_ts, ts - timedelta(hours=12))
    hi_lag    = bisect_left(other_alarm_ts, ts - timedelta(hours=4))
    return [upper_24h - lo_24h, hi_lag - lo_lag]


def _build_features(window, thresholds, ts, alarm_ts, other_alarm_ts):
    arr = np.stack([_vals(r) for r in window])
    cur = arr[-1]
    feats = list(cur)
    for i, ind in enumerate(INDICATORS):
        t   = thresholds[ind]
        rng = max(t['max'] - t['min'], 1e-6)
        mid = (t['max'] + t['min']) / 2
        feats.append((cur[i] - mid) / rng)
    feats.extend(arr.mean(axis=0))
    feats.extend(arr.max(axis=0) - arr.min(axis=0))
    feats.extend(arr[-1] - arr[0])
    feats.extend(_time_features(ts))
    feats.extend(_alarm_counts(alarm_ts, ts))
    feats.extend(_cross_alarm_counts(other_alarm_ts, ts))
    return np.array(feats, dtype=float)


def _label_for(record, future_records, thresholds):
    cutoff = record.timestamp + timedelta(hours=HORIZON_HOURS)
    for fr in future_records:
        if fr.timestamp <= record.timestamp:
            continue
        if fr.timestamp > cutoff:
            break
        v = _vals(fr)
        for i, ind in enumerate(INDICATORS):
            t = thresholds[ind]
            if v[i] < t['min'] or v[i] > t['max']:
                return 1
    return 0


def _load_thresholds():
    return {t.indicator: {'min': t.min_val, 'max': t.max_val}
            for t in Threshold.query.all()}


def _alarm_timestamps(point_id, exclude=False):
    q = (db.session.query(WaterRecord.timestamp)
         .join(AlarmLog, AlarmLog.record_id == WaterRecord.id))
    if exclude:
        q = q.filter(WaterRecord.point_id != point_id)
    else:
        q = q.filter(WaterRecord.point_id == point_id)
    return [r[0] for r in q.order_by(WaterRecord.timestamp.asc()).all()]


def _all_point_records():
    """预取每个监测点的 (records, alarm_ts, other_alarm_ts)，避免重复 DB 查询。"""
    out = []
    for p in MonitorPoint.query.all():
        rs = (WaterRecord.query
              .filter_by(point_id=p.id)
              .order_by(WaterRecord.timestamp.asc())
              .all())
        out.append((p.id, rs,
                    _alarm_timestamps(p.id, exclude=False),
                    _alarm_timestamps(p.id, exclude=True)))
    return out


# ─── 数据集构造 ────────────────────────────────────────────────────────────
def build_classification_dataset():
    thresholds = _load_thresholds()
    X, y = [], []
    for pid, rs, alarm_ts, other_alarm_ts in _all_point_records():
        if len(rs) < WINDOW + 1:
            continue
        for i in range(WINDOW - 1, len(rs)):
            window = rs[i - WINDOW + 1: i + 1]
            X.append(_build_features(window, thresholds, rs[i].timestamp,
                                     alarm_ts, other_alarm_ts))
            y.append(_label_for(rs[i], rs[i + 1:], thresholds))
    return np.array(X), np.array(y)


def build_regression_dataset():
    """目标 = 下一条记录的 5 个指标值。"""
    thresholds = _load_thresholds()
    X, Y = [], []
    for pid, rs, alarm_ts, other_alarm_ts in _all_point_records():
        if len(rs) < WINDOW + 1:
            continue
        for i in range(WINDOW - 1, len(rs) - 1):
            window = rs[i - WINDOW + 1: i + 1]
            X.append(_build_features(window, thresholds, rs[i].timestamp,
                                     alarm_ts, other_alarm_ts))
            Y.append(_vals(rs[i + 1]))
    return np.array(X), np.array(Y)


# 兼容旧名
build_dataset = build_classification_dataset


# ─── 训练 ──────────────────────────────────────────────────────────────────
def train():
    X, y = build_classification_dataset()
    if len(X) == 0:
        raise ValueError('训练数据不足，请先生成水质记录')
    if len(set(y.tolist())) < 2:
        X = np.vstack([X, X.mean(axis=0)])
        y = np.append(y, 1 - int(y[0]))

    # 1) 分类
    pipe = Pipeline([
        ('s', StandardScaler()),
        ('c', RandomForestClassifier(n_estimators=120, max_depth=8,
                                     class_weight='balanced', random_state=42)),
    ])
    try:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_auc = round(float(cross_val_score(pipe, X, y, cv=skf, scoring='roc_auc').mean()), 3)
        cv_pr  = round(float(cross_val_score(pipe, X, y, cv=skf, scoring='average_precision').mean()), 3)
    except Exception:
        cv_auc, cv_pr = None, None
    pipe.fit(X, y)

    # 2) 异常检测 (无监督，全量训练；contamination = 实际正样本率)
    contamination = max(min(float(y.mean()), 0.4), 0.01)
    iforest = Pipeline([
        ('s', StandardScaler()),
        ('iso', IsolationForest(contamination=contamination, n_estimators=120,
                                random_state=42)),
    ])
    iforest.fit(X)

    # 3) 趋势回归
    X_reg, Y_reg = build_regression_dataset()
    regressor = Pipeline([
        ('s', StandardScaler()),
        ('r', MultiOutputRegressor(RandomForestRegressor(
            n_estimators=80, max_depth=8, random_state=42))),
    ])
    regressor.fit(X_reg, Y_reg)
    pred_Y = regressor.predict(X_reg)
    reg_mae = {ind: round(float(mean_absolute_error(Y_reg[:, i], pred_Y[:, i])), 3)
               for i, ind in enumerate(INDICATORS)}

    metrics = {
        'samples':         int(len(X)),
        'positive_rate':   round(float(y.mean()), 3),
        'feature_count':   int(X.shape[1]),
        'window':          WINDOW,
        'horizon_hours':   HORIZON_HOURS,
        'classifier': {
            'train_accuracy': round(float(pipe.score(X, y)), 3),
            'cv_roc_auc':     cv_auc,
            'cv_pr_auc':      cv_pr,
        },
        'anomaly': {
            'contamination': round(contamination, 3),
        },
        'regressor': {
            'train_mae': reg_mae,
        },
    }
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({'pipe': pipe, 'iforest': iforest, 'regressor': regressor,
                 'metrics': metrics}, MODEL_PATH)
    _cache.update({'pipe': pipe, 'iforest': iforest,
                   'regressor': regressor, 'metrics': metrics})
    return metrics


def _ensure_model():
    if _cache['pipe'] is None:
        if os.path.exists(MODEL_PATH):
            try:
                data = joblib.load(MODEL_PATH)
                _cache.update({
                    'pipe':      data['pipe'],
                    'iforest':   data.get('iforest'),
                    'regressor': data.get('regressor'),
                    'metrics':   data.get('metrics'),
                })
                return
            except Exception:
                pass
        train()


# ─── 推理 ──────────────────────────────────────────────────────────────────
def predict_for_point(point_id):
    _ensure_model()
    pipe, iforest, regressor = _cache['pipe'], _cache['iforest'], _cache['regressor']

    rs = (WaterRecord.query
          .filter_by(point_id=point_id)
          .order_by(WaterRecord.timestamp.desc())
          .limit(WINDOW).all())
    if len(rs) < WINDOW:
        return None
    rs = list(reversed(rs))
    thresholds = _load_thresholds()
    feats = _build_features(rs, thresholds, rs[-1].timestamp,
                            _alarm_timestamps(point_id, exclude=False),
                            _alarm_timestamps(point_id, exclude=True)).reshape(1, -1)

    # 1) 分类
    prob = float(pipe.predict_proba(feats)[0][1])
    risk = 'high' if prob >= 0.50 else ('medium' if prob >= 0.30 else 'low')

    # 2) 异常分数: decision_function 越负越异常 → sigmoid 转 [0,1]，1=最异常
    raw = float(iforest.decision_function(feats)[0])
    anomaly_score = round(float(1.0 / (1.0 + np.exp(ANOMALY_SCALE * raw))), 4)
    is_anomaly = bool(iforest.predict(feats)[0] == -1)

    # 3) 趋势预测：下一条记录的 5 个指标值 + 是否预测越界
    forecast_vals = regressor.predict(feats)[0]
    forecast, at_risk, max_breach = {}, [], 0.0
    for i, ind in enumerate(INDICATORS):
        v = float(forecast_vals[i])
        forecast[ind] = round(v, 3)
        t = thresholds[ind]
        rng = max(t['max'] - t['min'], 1e-6)
        breach = max(0.0, (v - t['max']) / rng, (t['min'] - v) / rng)
        if breach > 0:
            at_risk.append(ind)
            max_breach = max(max_breach, breach)

    return {
        'point_id':         point_id,
        'last_timestamp':   rs[-1].timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'based_on_records': len(rs),
        'classification': {
            'probability': round(prob, 4),
            'risk_level':  risk,
        },
        'anomaly': {
            'score':      anomaly_score,
            'is_anomaly': is_anomaly,
        },
        'forecast': {
            'next_values':         forecast,
            'indicators_at_risk':  at_risk,
            'max_breach_ratio':    round(float(max_breach), 4),
        },
    }


def get_metrics():
    _ensure_model()
    return _cache.get('metrics')
