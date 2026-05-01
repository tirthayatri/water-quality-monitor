from flask import Blueprint, request, jsonify
from services import alarm_service

bp = Blueprint('alarms', __name__)


@bp.route('/api/alarms', methods=['GET'])
def get_alarms():
    point_id  = request.args.get('point_id')
    indicator = request.args.get('indicator')
    alarms = alarm_service.get_alarms(point_id=point_id, indicator=indicator)
    return jsonify(alarms)