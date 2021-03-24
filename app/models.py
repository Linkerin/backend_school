from app import db, ma


class Couriers(db.Model):
    __tablename__ = 'couriers'
    courier_id = db.Column(db.Integer, primary_key=True)
    courier_type = db.Column(db.String(8), nullable=False)
    regions = db.Column(db.PickleType, nullable=False)
    working_hours = db.Column(db.PickleType, nullable=False)
    orders = db.relationship('Orders', backref='courier', lazy=True)

    def __repr__(self):
        return (f'Couriers('
                f'courier_id={self.courier_id}, '
                f'courier_type="{self.courier_type}", '
                f'regions={self.regions}, '
                f'working_hours={self.working_hours})')

    def __str__(self):
        return f'<Courier id: {self.courier_id}>'


class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float(precision=2), nullable=False)
    region = db.Column(db.Integer, nullable=False)
    delivery_hours = db.Column(db.PickleType, nullable=False)
    assigned_courier = db.Column(db.Integer,
                                 db.ForeignKey('couriers.courier_id')) 
    assigned = db.Column(db.Boolean, default=False)
    assign_time = db.Column(db.DateTime(timezone=True))
    completed = db.Column(db.Boolean, default=False)
    complete_time = db.Column(db.DateTime(timezone=True))

    def __repr__(self):
        return (f'Orders('
                f'order_id={self.order_id}, '
                f'weight={self.weight}, '
                f'region={self.region}, '
                f'delivery_hours={self.delivery_hours})')

    def __str__(self):
        return f'<Order id: {self.order_id}>'


# class OrdersBundle(db.Model):
#     bundle_id = db.Column(db.Integer, primary_key=True)
