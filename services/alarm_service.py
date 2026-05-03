from extensions import db
from models import AlarmLog, Threshold


def check_and_log_alarms(record, thresholds=None):
    """检测单条记录并写入报警日志。

    Args:
        record:     WaterRecord 实例，必须已有 id（flush 之后即可，无需 commit）。
        thresholds: 可选，预先查询好的 Threshold 列表。
                    批量写入时由调用方统一查一次传入，避免每条记录各查一次。
    """
    if thresholds is None:
        thresholds = Threshold.query.all()

    indicator_map = {
        'chlorine':     record.chlorine,
        'conductivity': record.conductivity,
        'ph':           record.ph,
        'orp':          record.orp,
        'turbidity':    record.turbidity
    }

    for t in thresholds:
        actual = indicator_map.get(t.indicator)
        if actual is None:
            continue

        if actual > t.max_val:
            db.session.add(AlarmLog(
                record_id     = record.id,
                indicator     = t.indicator,
                actual_val    = actual,
                threshold_val = t.max_val,
                alarm_type    = 'high'
            ))
        elif actual < t.min_val:
            db.session.add(AlarmLog(
                record_id     = record.id,
                indicator     = t.indicator,
                actual_val    = actual,
                threshold_val = t.min_val,
                alarm_type    = 'low'
            ))


def get_alarms(point_id=None, indicator=None):
    query = AlarmLog.query.order_by(AlarmLog.created_at.desc())

    if indicator:
        query = query.filter(AlarmLog.indicator == indicator)

    if point_id:
        from models import WaterRecord
        query = query.join(WaterRecord).filter(WaterRecord.point_id == point_id)

    return [a.to_dict() for a in query.all()]