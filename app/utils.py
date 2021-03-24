from datetime import date, datetime
from datetimerange import DateTimeRange
from app import db
from app.models import Orders


def validation_error(invalid_ids):
    """ Message that will be returned for `'POST'`
        routings in case some invalid data were sent. \n
        Example:\n
        `{"validation_error" : {"couriers": [{"id": 1}, {"id": 2}]}}`
    """
    unique_ids = set(list(invalid_ids.values())[0])
    data_type = list(invalid_ids.keys())[0]
    bad_request = {
        'validation error': {
            data_type: []
        }
    }

    for item in unique_ids:
        try:
            item = int(item)
        except ValueError:
            pass
        bad_request['validation error'][data_type].append({'id': item})

    return bad_request


def creation_success(data, data_type):
    """ Message that will be returned for `'POST'`
        routings in case of successful database entry. \n
        Example:\n
        `{"couriers": [{"id": 1}, {"id": 2}]}`
    """
    if data_type == 'couriers':
        id_type = 'courier_id'
    elif data_type == 'orders':
        id_type = 'order_id'

    success_msg = {data_type: []}
    for element in data['data']:
        success_msg[data_type].append({'id': element[id_type]})

    return success_msg


def datetime_ranges(time_ranges):
    """ This functions takes a `list` of time ranges presented
        as `string`s in the following format: `'HH:MM'`,
        converts them into `DateTimeRange` objects and returns
        a `list` of these objects
    """
    output_dt_ranges = []
    for time_range in time_ranges:

        range_list = time_range.split('-')
        range_start = datetime.strptime(range_list[0], '%H:%M').time()
        range_end = datetime.strptime(range_list[1], '%H:%M').time()

        today = date.today()
        range_start_dt = datetime.combine(today, range_start)
        range_end_dt = datetime.combine(today, range_end)
        output_range = DateTimeRange(range_start_dt, range_end_dt)
        output_dt_ranges.append(output_range)

    return output_dt_ranges


def assigned_orders_msg(assigned_orders, assign_time=None):
    """ This function takes a `list` of orders' ids assigned
    to the courier and their assign time in as a `datetime`
    object. Output is a dictionary of assigned orders in the
    following format:\n
    `{"orders": [{"id": 1}, {"id": 2}],`\n
    `"assign_time": "2021-03-24T18:39:11.404228+03:00"}`
    """
    if assign_time is not None:
        orders_msg = {
            'orders': [],
            'assign_time': assign_time.isoformat()
        }
    else:
        orders_msg = {
            'orders': []
        }
        return orders_msg

    for order_id in assigned_orders:
        orders_msg['orders'].append({'id': order_id})

    return orders_msg


def regions_upd(new_regions, courier_id):
    """This function takes a `list` of update courier's
    regions and courier's id to check whethere his assigned
    orders comply with new regions list and makes them
    available for assignment if not.
    """
    orders = Orders.query.filter_by(assigned_courier=courier_id,
                                    completed=False)
    for order in orders:
        if order.region not in new_regions:
            order.assigned_courier = None,
            order.assign_time = None,
            order.assigned = False
    db.session.commit()

    return


def courier_type_upd(new_type, courier_id):
    """This function takes a `list` of updated courier's
    type and courier's id to check whethere his assigned
    orders comply with load capabilities and makes them
    available for assignment if not.
    """
    orders = Orders.query.filter_by(assigned_courier=courier_id,
                                    completed=False)
    current_load = 0
    for order in orders:
        if CAPACITY[new_type] >= current_load + order.weight:
            current_load += order.weight
        else:
            order.assigned_courier = None,
            order.assign_time = None,
            order.assigned = False
    db.session.commit()

    return

def working_hours_upd(new_hours, courier_id):
    """This function takes a `list` of updated courier's
    working hours and courier's id to check whethere his
    assigned orders comply with new hours and makes them
    available for assignment if not.
    """
    courier_ranges = datetime_ranges(new_hours)
    orders = Orders.query.filter_by(assigned_courier=courier_id,
                                    completed=False)
    for order in orders:
        reassign = True
        order_ranges = datetime_ranges(order.delivery_hours)
        for c_range, o_range in product(courier_ranges, order_ranges):
            if c_range.is_intersection(o_range):
                reassign = False
                break
        if reassign:
            order.assigned_courier = None,
            order.assign_time = None,
            order.assigned = False
    db.session.commit()

    return


# Constant describing courier's load capacity
CAPACITY = {
    'foot': 10,
    'bike': 15,
    'car': 50
}
