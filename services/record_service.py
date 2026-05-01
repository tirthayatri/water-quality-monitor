from extensions import db
from models import WaterRecord
from datetime import datetime, timezone, timedelta


def get_all_records(filters=None):
    query = WaterRecord.query.order_by(WaterRecord.timestamp.desc())

    if filters:
        if filters.get('point_id'):
            query = query.filter(WaterRecord.point_id == int(filters['point_id']))

        if filters.get('date_from'):
            date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
            query = query.filter(WaterRecord.timestamp >= date_from)

        if filters.get('date_to'):
            # +1天再取严格小于，确保 date_to 当天的数据都能被包含
            date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(WaterRecord.timestamp < date_to)

        if filters.get('chlorine_min'):
            query = query.filter(WaterRecord.chlorine >= float(filters['chlorine_min']))
        if filters.get('chlorine_max'):
            query = query.filter(WaterRecord.chlorine <= float(filters['chlorine_max']))

        if filters.get('conductivity_min'):
            query = query.filter(WaterRecord.conductivity >= float(filters['conductivity_min']))
        if filters.get('conductivity_max'):
            query = query.filter(WaterRecord.conductivity <= float(filters['conductivity_max']))

        if filters.get('ph_min'):
            query = query.filter(WaterRecord.ph >= float(filters['ph_min']))
        if filters.get('ph_max'):
            query = query.filter(WaterRecord.ph <= float(filters['ph_max']))

        if filters.get('orp_min'):
            query = query.filter(WaterRecord.orp >= float(filters['orp_min']))
        if filters.get('orp_max'):
            query = query.filter(WaterRecord.orp <= float(filters['orp_max']))

        if filters.get('turbidity_min'):
            query = query.filter(WaterRecord.turbidity >= float(filters['turbidity_min']))
        if filters.get('turbidity_max'):
            query = query.filter(WaterRecord.turbidity <= float(filters['turbidity_max']))

    return [r.to_dict() for r in query.all()]


def get_record_by_id(record_id):
    record = WaterRecord.query.get_or_404(record_id)
    return record.to_dict()


def create_record(data):
    record = WaterRecord(
        point_id     = data['point_id'],
        timestamp    = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S') if data.get('timestamp') else datetime.now(timezone.utc),
        chlorine     = data['chlorine'],
        conductivity = data['conductivity'],
        ph           = data['ph'],
        orp          = data['orp'],
        turbidity    = data['turbidity']
    )
    db.session.add(record)
    db.session.commit()
    return record


def update_record(record_id, data):
    from models import AlarmLog
    from services.alarm_service import check_and_log_alarms

    record = WaterRecord.query.get_or_404(record_id)

    if 'chlorine'     in data: record.chlorine     = data['chlorine']
    if 'conductivity' in data: record.conductivity = data['conductivity']
    if 'ph'           in data: record.ph           = data['ph']
    if 'orp'          in data: record.orp          = data['orp']
    if 'turbidity'    in data: record.turbidity    = data['turbidity']
    if 'timestamp'    in data: record.timestamp    = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')

    # 删除旧报警日志，重新计算
    AlarmLog.query.filter_by(record_id=record_id).delete()
    db.session.commit()

    check_and_log_alarms(record)

    return record.to_dict()


def delete_record(record_id):
    record = WaterRecord.query.get_or_404(record_id)
    # 级联删除已在模型 relationship 中配置，无需手动删除 alarm_logs
    db.session.delete(record)
    db.session.commit()
    return {'message': f'记录 {record_id} 已删除'}
