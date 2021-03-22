from datetime import date, datetime
from datetimerange import DateTimeRange


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


# Constant describing courier's load capacity
CAPACITY = {
    'foot': 10,
    'bike': 15,
    'car': 50
}
