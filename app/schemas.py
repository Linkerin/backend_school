from datetime import date, datetime
from datetimerange import DateTimeRange
from marshmallow import fields, validate, ValidationError
from app import db, ma
from app.models import Couriers, Orders


def hours_validator(period):
    """ Validates that the received time period is in the
        following format: `'HH:MM-HH:MM'`
    """
    time_points = period.split('-')
    if len(time_points) != 2:
        error = "Working hours period should be separated by '-'"
        raise ValidationError(error)

    for time in time_points:
        time_check = time.split(':')
        if len(time_check) != 2:
            raise ValidationError('Time format is not HH:MM')
        if int(time_check[0]) not in range(0, 24) or \
                int(time_check[1]) not in range(0, 60):
            raise ValidationError('Time format is not HH:MM')

    # Checks whether there is no time inversion in the input range
    today = date.today()
    range_start = datetime.strptime(time_points[0], '%H:%M').time()
    range_end = datetime.strptime(time_points[1], '%H:%M').time()
    range_start_dt = datetime.combine(today, range_start)
    range_end_dt = datetime.combine(today, range_end)
    output_range = DateTimeRange(range_start_dt, range_end_dt)
    try:
        output_range.validate_time_inversion()
    except ValueError:
        raise ValidationError(f'Time inversion identified: "{period}"')


class StrictFloat(fields.Number):
    """ A strict float field: only float types are valid.

    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = float

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid float."}

    # override Number
    def _validated(self, value):
        if type(value) == self.num_type or type(value) == int:
            return super()._validated(value)
        raise self.make_error("invalid", input=value)

    def _format_num(self, value):
        """Return the number value for value, given this field's `num_type`."""
        return self.num_type(round(value, 2))


class CouriersSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Couriers
        load_instance = True
        sqla_session = db.session

    courier_id = fields.Int(required=True, strict=True,
                            validate=validate.Range(min=0))
    courier_type = fields.Str(required=True,
                              validate=validate.OneOf(['foot', 'bike', 'car']))
    regions = fields.List(fields.Int(strict=True,
                                     validate=validate.Range(min=0)),
                          required=True,
                          validate=validate.Length(min=1))
    working_hours = fields.List(fields.Str(validate=hours_validator),
                                required=True,
                                validate=validate.Length(min=1))
    earnings = fields.Int(strict=True)
    rating = fields.Float()


class OrdersSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Orders
        load_instance = True
        sqla_session = db.session

    order_id = fields.Int(required=True, strict=True,
                          validate=validate.Range(min=0))
    weight = StrictFloat(required=True,
                         validate=validate.Range(min=0.01, max=50))
    region = fields.Int(required=True, strict=True,
                        validate=validate.Range(min=0))
    delivery_hours = fields.List(fields.Str(validate=hours_validator),
                                 required=True,
                                 validate=validate.Length(min=1))
    assigned_courier = fields.Nested(CouriersSchema)
    assigned = fields.Boolean(truthy={True}, falsy={False})
    assign_time = fields.DateTime()
    completed = fields.Boolean(truthy={True}, falsy={False})
    complete_time = fields.DateTime()
    delivery_time = fields.Float(validate=validate.Range(min=0))


# Schemas initialization
courier_schema = CouriersSchema()
order_schema = OrdersSchema()
