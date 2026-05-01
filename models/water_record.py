from extensions import db
from datetime import datetime, timezone


class WaterRecord(db.Model):
    __tablename__ = 'water_records'

    id           = db.Column(db.Integer, primary_key=True)
    point_id     = db.Column(db.Integer, db.ForeignKey('monitor_points.id', ondelete='CASCADE'), nullable=False)
    timestamp    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    chlorine     = db.Column(db.Float, nullable=False)
    conductivity = db.Column(db.Float, nullable=False)
    ph           = db.Column(db.Float, nullable=False)
    orp          = db.Column(db.Float, nullable=False)
    turbidity    = db.Column(db.Float, nullable=False)

    alarms = db.relationship(
        'AlarmLog',
        backref='record',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def to_dict(self):
        return {
            'id':           self.id,
            'point_id':     self.point_id,
            'timestamp':    self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'chlorine':     self.chlorine,
            'conductivity': self.conductivity,
            'ph':           self.ph,
            'orp':          self.orp,
            'turbidity':    self.turbidity
        }
