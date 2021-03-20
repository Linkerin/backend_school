from flask import Flask, request, jsonify
from app import app, db
from app.models import Couriers
import app.utils as ut


@app.route("/")
def home():
    return 'Candy Delivery App API'

@app.route("/couriers", methods=['POST'])
def couriers():
    # post_keys = ['courier_id', 'courier_type', 'regions', 'working_hours']
    invalid_ids = []
    couriers = []

    data_types = {
        'courier_id': int,
        'courier_type': str,
        'regions': list,
        'working_hours': list
    }

    courier_type = ['foot', 'bike', 'car']
    # Добавить валидацию, что значение поля - не пустое
    if request.method == 'POST':
        data = request.get_json()
        for element in data['data']:
            keys_list = list(element.keys())
            keys_list.sort()
            if keys_list != list(data_types.keys()):
                invalid_ids.append(element['courier_id'])
                continue

            for key, item in element.items():
                if type(element[key]) != data_types[key]:
                    invalid_ids.append(element['courier_id'])
                    

            # if element['courier_type'] not in courier_type:
            #     bad_request['validation error']['couriers'].append(
            #         {'id': element['courier_id']}
            #     )
            
            for region in element['regions']:
                if type(region) != int:
                    invalid_ids.append(element['courier_id'])

            # for hour in element['working_hours']:
            #     if type(region) != str:
            #         bad_request['validation error']['couriers'].append(
            #         {'id': element['courier_id']}
            #     )
            if element['courier_id'] not in invalid_ids:
                courier = Couriers(
                                   courier_id=element['courier_id'],
                                   courier_type=element['courier_type'],
                                   regions=element['regions'],
                                   working_hours=element['working_hours']
                                   )
                couriers.append(courier)

        if len(invalid_ids) != 0:
            validation_response = ut.validation_error(invalid_ids)
            return jsonify(validation_response), 400
        else:
            for courier in couriers:
                db.session.add(courier)
            db.session.commit()
            success_response = ut.couriers_created(data)
    else:
        return 405

    return success_response, 201
