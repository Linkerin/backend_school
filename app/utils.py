def validation_error(invalid_ids):
    unique_ids = set(invalid_ids)
    bad_request = {
        'validation error': {
            'couriers': []
        }
    }

    for item in unique_ids:
        bad_request['validation error']['couriers'].append(
                    {'id': item}
                )

    return bad_request

def couriers_created(data):
    success_msg = {'couriers': []}
    for courier in data['data']:
        success_msg['couriers'].append({'id': courier['courier_id']})

    return success_msg