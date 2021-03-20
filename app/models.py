from app import db
from enum import Enum


class Couriers(db.Model):
    __tablename__ = 'couriers'
    courier_id = db.Column(db.Integer, primary_key=True)
    courier_type = db.Column(db.String(8), nullable=False)
    regions = db.Column(db.PickleType, nullable=False)
    working_hours = db.Column(db.PickleType, nullable=False)

    def __repr__(self):
        return (f'Couriers('
                        f'courier_id={self.courier_id}, '
                        f'courier_type="{self.courier_type}", '
                        f'regions={self.regions}, '
                        f'working_hours={self.working_hours})'
               )

    def __str__(self):
        return f'<Couriers id: {self.courier_id}>'
