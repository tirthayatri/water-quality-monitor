from extensions import db
from datetime import datetime, timezone


class Threshold(db.Model):
    __tablename__ = 'thresholds'

    id         = db.Column(db.Integer, primary_key=True)
    indicator  = db.Column(db.String(50), nullable=False, unique=True)
    min_val    = db.Column(db.Float, nullable=False)
    max_val    = db.Column(db.Float, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            'id':         self.id,
            'indicator':  self.indicator,
            'min_val':    self.min_val,
            'max_val':    self.max_val,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
