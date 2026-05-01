from extensions import db
from datetime import datetime, timezone


class MonitorPoint(db.Model):
    __tablename__ = 'monitor_points'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    latitude    = db.Column(db.Float, nullable=True)
    longitude   = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    records = db.relationship(
        'WaterRecord',
        backref='point',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'latitude':    self.latitude,
            'longitude':   self.longitude,
            'description': self.description,
            'created_at':  self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
