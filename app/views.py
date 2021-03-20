from flask import Flask, request, jsonify
from marshmallow import ValidationError
from app import app, db
from app.models import Couriers
from app.schemas import courier_schema
import app.utils as ut


@app.route("/")
def home():
    return 'Candy Delivery App API'


@app.route("/couriers", methods=['POST'])
def couriers():
    valid_keys = ['courier_id', 'courier_type', 'regions', 'working_hours']
    invalid_ids = []
    couriers = []

    if request.method == 'POST':
        data = request.get_json()
        for element in data['data']:
            keys_list = list(element.keys())
            keys_list.sort()
            if keys_list != valid_keys:
                invalid_ids.append(element['courier_id'])
                continue

            #Validation of data contained in received JSON via schema
            try:
                courier = courier_schema.load(element)
                if not Couriers.query.get(element['courier_id']):
                    couriers.append(courier)
                else:
                    invalid_ids.append(element['courier_id'])
            except ValidationError:
                invalid_ids.append(element['courier_id'])

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
