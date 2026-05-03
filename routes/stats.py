from flask import Blueprint, jsonify
from extensions import db
from models import MonitorPoint, WaterRecord, AlarmLog
from sqlalchemy import func

bp = Blueprint('stats', __name__)


@bp.route('/api/stats', methods=['GET'])
def get_stats():
    points_count  = db.session.query(func.count(MonitorPoint.id)).scalar()
    records_count = db.session.query(func.count(WaterRecord.id)).scalar()
    alarms_count  = db.session.query(func.count(AlarmLog.id)).scalar()
    high_count    = db.session.query(func.count(AlarmLog.id)).filter(AlarmLog.alarm_type == 'high').scalar()
    low_count     = db.session.query(func.count(AlarmLog.id)).filter(AlarmLog.alarm_type == 'low').scalar()
    return jsonify({
        'points':      points_count,
        'records':     records_count,
        'alarms':      alarms_count,
        'high_alarms': high_count,
        'low_alarms':  low_count,
    })
