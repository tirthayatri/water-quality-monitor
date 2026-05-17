from flask import Blueprint, request, jsonify
from models import MonitorPoint
from services import predictor

bp = Blueprint('predict', __name__)


@bp.route('/api/predict', methods=['GET'])
def predict():
    """预测未来 24 小时是否会出现指标超标。

    GET /api/predict             —— 返回所有监测点的预测结果
    GET /api/predict?point_id=N  —— 仅返回指定监测点
    """
    point_id = request.args.get('point_id', type=int)
    try:
        if point_id is not None:
            result = predictor.predict_for_point(point_id)
            if result is None:
                return jsonify({'error': '历史数据不足，至少需要 3 条记录'}), 400
            p = MonitorPoint.query.get(point_id)
            if p is not None:
                result['name'] = p.name
            return jsonify(result)

        results = []
        for p in MonitorPoint.query.order_by(MonitorPoint.id.asc()).all():
            r = predictor.predict_for_point(p.id)
            if r is not None:
                r['name'] = p.name
                results.append(r)
        return jsonify(results)
    except predictor.ModelNotReady as e:
        return jsonify({'error': str(e), 'model_ready': False,
                        'has_gpu': predictor.has_discrete_gpu()}), 503


@bp.route('/api/predict/train', methods=['POST'])
def train():
    try:
        metrics = predictor.train()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'message': '模型已重新训练', 'metrics': metrics})


@bp.route('/api/predict/info', methods=['GET'])
def info():
    return jsonify({
        'window':        predictor.WINDOW,
        'horizon_hours': predictor.HORIZON_HOURS,
        'indicators':    predictor.INDICATORS,
        'has_gpu':       predictor.has_discrete_gpu(),
        'model_ready':   predictor.is_model_ready(),
        'metrics':       predictor.get_metrics_if_ready(),
    })
