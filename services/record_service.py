from extensions import db
from models import WaterRecord, AlarmLog
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
            date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(WaterRecord.timestamp < date_to)

        if filters.get('chlorine_min') is not None:
            query = query.filter(WaterRecord.chlorine >= float(filters['chlorine_min']))
        if filters.get('chlorine_max') is not None:
            query = query.filter(WaterRecord.chlorine <= float(filters['chlorine_max']))

        if filters.get('conductivity_min') is not None:
            query = query.filter(WaterRecord.conductivity >= float(filters['conductivity_min']))
        if filters.get('conductivity_max') is not None:
            query = query.filter(WaterRecord.conductivity <= float(filters['conductivity_max']))

        if filters.get('ph_min') is not None:
            query = query.filter(WaterRecord.ph >= float(filters['ph_min']))
        if filters.get('ph_max') is not None:
            query = query.filter(WaterRecord.ph <= float(filters['ph_max']))

        if filters.get('orp_min') is not None:
            query = query.filter(WaterRecord.orp >= float(filters['orp_min']))
        if filters.get('orp_max') is not None:
            query = query.filter(WaterRecord.orp <= float(filters['orp_max']))

        if filters.get('turbidity_min') is not None:
            query = query.filter(WaterRecord.turbidity >= float(filters['turbidity_min']))
        if filters.get('turbidity_max') is not None:
            query = query.filter(WaterRecord.turbidity <= float(filters['turbidity_max']))

    records = query.all()
    if records:
        ids = [r.id for r in records]
        alarmed = {
            row[0] for row in
            db.session.query(AlarmLog.record_id)
            .filter(AlarmLog.record_id.in_(ids))
            .distinct()
            .all()
        }
    else:
        alarmed = set()

    result = []
    for r in records:
        d = r.to_dict()
        d['has_alarm'] = r.id in alarmed
        result.append(d)
    return result


def get_record_by_id(record_id):
    record = db.get_or_404(WaterRecord, record_id) 
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
    db.session.flush()
    return record


def update_record(record_id, data):
    from models import AlarmLog
    from services.alarm_service import check_and_log_alarms

    record = db.get_or_404(WaterRecord, record_id)

    if 'chlorine'     in data: record.chlorine     = data['chlorine']
    if 'conductivity' in data: record.conductivity = data['conductivity']
    if 'ph'           in data: record.ph           = data['ph']
    if 'orp'          in data: record.orp          = data['orp']
    if 'turbidity'    in data: record.turbidity    = data['turbidity']
    if 'timestamp'    in data: record.timestamp    = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')

    AlarmLog.query.filter_by(record_id=record_id).delete()
    check_and_log_alarms(record)
    db.session.commit()

    return record.to_dict()


def delete_record(record_id):
    record = db.get_or_404(WaterRecord, record_id)
    # 级联删除已在模型 relationship 中配置
    db.session.delete(record)
    db.session.commit()
    return {'message': f'记录 {record_id} 已删除'}