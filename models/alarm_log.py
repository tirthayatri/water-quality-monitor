from extensions import db
from datetime import datetime, timezone


class AlarmLog(db.Model):
    __tablename__ = 'alarm_logs'

    id            = db.Column(db.Integer, primary_key=True)
    record_id     = db.Column(db.Integer, db.ForeignKey('water_records.id', ondelete='CASCADE'), nullable=False)
    indicator     = db.Column(db.String(50), nullable=False)
    actual_val    = db.Column(db.Float, nullable=False)
    threshold_val = db.Column(db.Float, nullable=False)
    alarm_type    = db.Column(db.String(10), nullable=False)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':            self.id,
            'record_id':     self.record_id,
            'indicator':     self.indicator,
            'actual_val':    self.actual_val,
            'threshold_val': self.threshold_val,
            'alarm_type':    self.alarm_type,
            'created_at':    self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
