from flask import Blueprint, request, jsonify
from extensions import db
from models import Threshold

bp = Blueprint('thresholds', __name__)


@bp.route('/api/thresholds', methods=['GET'])
def get_thresholds():
    thresholds = Threshold.query.all()
    return jsonify([t.to_dict() for t in thresholds])


@bp.route('/api/thresholds/<string:indicator>', methods=['PUT'])
def update_threshold(indicator):
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    t = Threshold.query.filter_by(indicator=indicator).first_or_404()

    if 'min_val' in data:
        t.min_val = data['min_val']
    if 'max_val' in data:
        t.max_val = data['max_val']

    # 校验 min < max
    if t.min_val >= t.max_val:
        return jsonify({'error': 'min_val 必须小于 max_val'}), 400

    db.session.commit()
    return jsonify(t.to_dict())
