from flask import Blueprint, request, jsonify
from extensions import db
from models import MonitorPoint, WaterRecord

bp = Blueprint('points', __name__)

@bp.route('/api/points', methods=['GET'])
def get_points():
    points = MonitorPoint.query.all()
    return jsonify([p.to_dict() for p in points])


@bp.route('/api/points/<int:point_id>', methods=['GET'])
def get_point(point_id):
    point = db.get_or_404(MonitorPoint, point_id)
    return jsonify(point.to_dict())

@bp.route('/api/points', methods=['POST'])
def create_point():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': '缺少监测点名称'}), 400

    point = MonitorPoint(
        name        = data['name'],
        latitude    = data.get('latitude'),
        longitude   = data.get('longitude'),
        description = data.get('description')
    )
    db.session.add(point)
    db.session.commit()
    return jsonify(point.to_dict()), 201

@bp.route('/api/points/<int:point_id>', methods=['PUT'])
def update_point(point_id):
    point = db.get_or_404(MonitorPoint, point_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    if 'name' in data:
        if not data['name']:
            return jsonify({'error': '监测点名称不能为空'}), 400
        point.name = data['name']
    if 'latitude'    in data: point.latitude    = data['latitude']
    if 'longitude'   in data: point.longitude   = data['longitude']
    if 'description' in data: point.description = data['description']

    db.session.commit()
    return jsonify(point.to_dict())

@bp.route('/api/points/<int:point_id>', methods=['DELETE'])
def delete_point(point_id):
    point = db.get_or_404(MonitorPoint, point_id)
    record_count = WaterRecord.query.filter_by(point_id=point_id).count()
    db.session.delete(point)
    db.session.commit()
    return jsonify({
        'message': f'监测点「{point.name}」已删除，同时清除关联数据 {record_count} 条'
    })