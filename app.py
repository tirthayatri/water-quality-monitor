from flask import Flask, render_template
from config import Config
from extensions import db
from models import MonitorPoint, WaterRecord, Threshold, AlarmLog
import os, signal
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 确保数据库所在目录存在（Git 不追踪空文件夹，新环境克隆后需自动创建）
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)

    db.init_app(app)
    migrate = Migrate(app, db)

    from routes.records    import bp as records_bp
    from routes.points     import bp as points_bp
    from routes.alarms     import bp as alarms_bp
    from routes.thresholds import bp as thresholds_bp

    app.register_blueprint(records_bp)
    app.register_blueprint(points_bp)
    app.register_blueprint(alarms_bp)
    app.register_blueprint(thresholds_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        os.kill(os.getpid(), signal.SIGTERM)
        return 'OK'

    # 移除 db.create_all()，统一通过 flask db upgrade 建表
    with app.app_context():
        seed_thresholds()

    return app


def seed_thresholds():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    if 'thresholds' not in inspector.get_table_names():
        return  # 表不存在时直接跳过
    if Threshold.query.count() == 0:
        defaults = [
            Threshold(indicator='chlorine',     min_val=0.05, max_val=0.3),
            Threshold(indicator='conductivity', min_val=0.0,  max_val=1000.0),
            Threshold(indicator='ph',           min_val=6.5,  max_val=8.5),
            Threshold(indicator='orp',          min_val=200.0, max_val=500.0),
            Threshold(indicator='turbidity',    min_val=0.0,  max_val=3.0),
        ]
        db.session.add_all(defaults)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)