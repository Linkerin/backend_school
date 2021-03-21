#Validation error message sending for 'POST' routings
def validation_error(invalid_ids):
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


#Message of successful database entry for 'POST' routings
def couriers_created(data, data_type):
    if data_type == 'couriers':
        id_type = 'courier_id'
    elif data_type == 'orders':
        id_type = 'order_id'

    success_msg = {data_type: []}
    for element in data['data']:
        success_msg[data_type].append({'id': element[id_type]})

    return success_msg