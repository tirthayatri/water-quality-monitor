from flask import Blueprint, request, jsonify
from services import record_service, alarm_service

bp = Blueprint('records', __name__)

@bp.route('/api/records', methods=['GET'])
def get_records():
    filters = {
        'point_id':         request.args.get('point_id'),
        'date_from':        request.args.get('date_from'),
        'date_to':          request.args.get('date_to'),
        'chlorine_min':     request.args.get('chlorine_min'),
        'chlorine_max':     request.args.get('chlorine_max'),
        'conductivity_min': request.args.get('conductivity_min'),
        'conductivity_max': request.args.get('conductivity_max'),
        'ph_min':           request.args.get('ph_min'),
        'ph_max':           request.args.get('ph_max'),
        'orp_min':          request.args.get('orp_min'),
        'orp_max':          request.args.get('orp_max'),
        'turbidity_min':    request.args.get('turbidity_min'),
        'turbidity_max':    request.args.get('turbidity_max'),
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    records = record_service.get_all_records(filters)
    return jsonify(records)


@bp.route('/api/records/<int:record_id>', methods=['GET'])
def get_record(record_id):
    record = record_service.get_record_by_id(record_id)
    return jsonify(record)


@bp.route('/api/records', methods=['POST'])
def create_record():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    required = ['point_id', 'chlorine', 'conductivity', 'ph', 'orp', 'turbidity']
    for field in required:
        if field not in data:
            return jsonify({'error': f'缺少字段: {field}'}), 400

    record = record_service.create_record(data)
    alarm_service.check_and_log_alarms(record)
    return jsonify(record.to_dict()), 201


@bp.route('/api/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    result = record_service.update_record(record_id, data)
    return jsonify(result)


@bp.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    result = record_service.delete_record(record_id)
    return jsonify(result)

@bp.route('/api/records/batch', methods=['POST'])
def create_records_batch():
    data_list = request.get_json()
    if not data_list or not isinstance(data_list, list):
        return jsonify({'error': '请求体必须是数组'}), 400

    required = ['point_id', 'chlorine', 'conductivity', 'ph', 'orp', 'turbidity']
    results = []
    for i, data in enumerate(data_list):
        for field in required:
            if field not in data:
                return jsonify({'error': f'第 {i+1} 条数据缺少字段: {field}'}), 400
        record = record_service.create_record(data)
        alarm_service.check_and_log_alarms(record)
        results.append(record.to_dict())

    return jsonify({'saved': len(results), 'records': results}), 201