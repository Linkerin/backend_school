from marshmallow import fields, validate, ValidationError
from app import db, ma
from app.models import Couriers


def hours_validator(period):
    time_points = period.split('-')
    if len(time_points) != 2:
        raise ValidationError('Working hours have to a period separated by "-"')

    for time in time_points:
        time_check = time.split(':')
        if len(time_check) != 2:
            raise ValidationError('Time format is not HH:MM')
        if int(time_check[0]) not in range(0, 24) or \
            int (time_check[1]) not in range(0, 60):
            raise ValidationError('Time format is not HH:MM')


class CouriersSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Couriers
        load_instance = True
        sqla_session = db.session

    courier_id = fields.Int(required=True, strict=True)
    courier_type = fields.Str(required=True,
                              validate=validate.OneOf(['foot', 'bike', 'car']))
    regions = fields.List(fields.Int(strict=True), required=True,
                          validate=validate.Length(min=1))
    working_hours = fields.List(fields.Str(validate=hours_validator),
                                required=True,
                                validate=validate.Length(min=1))


courier_schema = CouriersSchema()
