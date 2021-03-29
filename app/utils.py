import pytz
from datetime import date, datetime, timedelta
from datetimerange import DateTimeRange
from itertools import product
from app import db
from app.models import Couriers, Orders, OrdersBundle, Regions


def validation_error(invalid_ids, errors):
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
        },
        'Errors': errors
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
    """ This function takes a `list` of `Orders` objects
    assigned to the courier and their assign time in as
    a `datetime` object. Output is a dictionary of assigned
    orders in the following format:\n
    `{"orders": [{"id": 1}, {"id": 2}],`\n
    `"assign_time": "2021-03-24T18:39:11.404228+00:00"}`
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

    for order in assigned_orders:
        order_id = order.order_id
        orders_msg['orders'].append({'id': order_id})

    return orders_msg


def regions_upd(new_regions, courier_id):
    """This function takes a `list` of update courier's
    regions and courier's id to check whether his assigned
    orders comply with new regions list and makes them
    available for assignment if not.
    """
    orders = Orders.query.filter_by(assigned_courier=courier_id,
                                    completed=False)
    for order in orders:
        if order.region not in new_regions:
            order.assigned_courier = None
            order.assign_time = None
            order.assigned = False
            order.bundle = None
    db.session.commit()
    upd_bundle_check(courier_id)

    return


def courier_type_upd(new_type, courier_id):
    """This function takes a `list` of updated courier's
    type and courier's id to check whether his assigned
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
            order.assigned_courier = None
            order.assign_time = None
            order.assigned = False
            order.bundle = None
    db.session.commit()
    upd_bundle_check(courier_id)

    return


def working_hours_upd(new_hours, courier_id):
    """This function takes a `list` of updated courier's
    working hours and courier's id to check whether his
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
            order.assigned_courier = None
            order.assign_time = None
            order.assigned = False
            order.bundle = None
    db.session.commit()
    upd_bundle_check(courier_id)

    return


def upd_bundle_check(courier_id):
    """ This function updates orders' bundle attributes
        and checks whether it is completed or not when
        courier's attributes are changed.\n
        Input: `courier_id`
    """
    bundle = (OrdersBundle.query.filter_by(courier_id=courier_id,
                                           completed=False)
                                .order_by(OrdersBundle.bundle_id.desc())
                                .first())
    if bundle is None:
        return

    if len(bundle.orders) == 0:
        bundle.completed = True
        bundle.complete_time = datetime.now(tz=pytz.timezone('Europe/Moscow'))
        bundle.deleted = True
        db.session.commit()
        return

    finished = bundle_finished(bundle)
    if finished is True:
        complete_bundle(bundle)
        db.session.commit()

    return


def bundle_id():
    """ Function creates orders' bundle id: #1 if there are no bundles
        in the table and 'latest + 1' if the table is not empty.
    """
    last_bundle = OrdersBundle.query.order_by(OrdersBundle.bundle_id
                                              .desc()).first()
    if last_bundle is not None:
        return last_bundle.bundle_id + 1
    else:
        return 1


def bundle_finished(bundle):
    """ Function checks whether all orders
        in the bundle are finished or not
        and returns respective boolean value
    """
    for order in bundle.orders:
        if order.completed is False:
            return False
    return True


def complete_bundle(bundle, complete_time=None):
    """ Function that makes all necessary attributes' changes
        in `OrdersBundle` and `Couriers` objects when all orders
        in the bundle are delivered.\n
        As the input it takes an `OrdersBundle` object and
        optionally a bundle completion time in `datetime` format.
    """
    if complete_time is None:
        complete_time = datetime.now(tz=pytz.timezone('Europe/Moscow'))
    bundle.completed = True
    bundle.complete_time = complete_time
    courier = Couriers.query.get(bundle.courier_id)
    courier.earnings += (EARNING_COEF[bundle.init_courier_type] *
                         BUNDLE_EARNING)
    courier.rating = rating(courier)
    return


def order_delivery_time(order, complete_time):
    """ This function calculates time consumed to deliver
        the order taking as an input `Orders` object and
        order completion time in `datetime` format.\n
        If this is the first delivered order in the bundle,
        delivery time is a difference between completion time
        and bundle assign time. In case there were some
        previously delivered orders delivery time is
        a difference between completion time and previous
        order completion time.
    """
    bundle_orders = Orders.query.filter_by(bundle=order.bundle)
    first_order = True
    for b_order in bundle_orders:
        if b_order.completed is True:
            first_order = False
            break

    if first_order is True:
        delivery_time = complete_time - order.assign_time
    else:
        prev_order = (Orders.query.filter_by(bundle=order.bundle,
                                             completed=True)
                                  .order_by(Orders.complete_time.desc())
                                  .first())
        delivery_time = complete_time - prev_order.complete_time
    if delivery_time < timedelta():
        return 'Order completion time is less than the previous'

    return delivery_time.total_seconds()


def rating(courier):
    """ Function calculates courier's rating based on minimal value of
        average delivery time per each region. If no orders were delivered,
        the function returns `0`.\n
        Input: `Couriers` object\n
        Output: `float` value
    """
    regions = Regions.query.filter_by(courier_id=courier.courier_id)
    delivery_times = []
    for region in regions:
        delivery_times.append(region.avg_delivery_time)
    if len(delivery_times) == 0:
        return 0

    t = min(delivery_times)
    rating = (60 * 60 - min(t, 60 * 60)) / (60 * 60) * 5

    return round(rating, 2)


""" Constant describing courier's load capacity """
CAPACITY = {
    'foot': 10,
    'bike': 15,
    'car': 50
}


""" Constant containing earnings coefficient
    per order depending on courier type
"""
EARNING_COEF = {
    'foot': 2,
    'bike': 5,
    'car': 9
}

BUNDLE_EARNING = 500
