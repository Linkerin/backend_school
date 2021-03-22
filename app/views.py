from flask import Flask, request, jsonify
from marshmallow import ValidationError
from datetime import datetime
from itertools import product
from app import app, db
from app.models import Couriers, Orders
from app.schemas import courier_schema, order_schema
import app.utils as ut


@app.route("/")
def home():
    return 'Candy Delivery App API', 200


@app.route("/couriers", methods=['POST'])
def couriers():
    if request.method == 'POST':
        valid_keys = ['courier_id', 'courier_type',
                      'regions', 'working_hours']
        invalid_ids = {'couriers': []}
        couriers = []

        data = request.get_json()
        try:
            for element in data['data']:
                keys_list = list(element.keys())
                keys_list.sort()
                if keys_list != valid_keys:
                    invalid_ids['couriers'].append(element['courier_id'])
                    continue

                # Validation of data contained in received JSON via schema
                try:
                    courier = courier_schema.load(element)
                    if not Couriers.query.get(element['courier_id']):
                        couriers.append(courier)
                    else:
                        invalid_ids['couriers'].append(element['courier_id'])
                except ValidationError:
                    invalid_ids['couriers'].append(element['courier_id'])
        except KeyError:
            return 'Bad Request', 400

        if len(invalid_ids['couriers']) != 0:
            validation_response = ut.validation_error(invalid_ids)
            return jsonify(validation_response), 400

        else:
            for courier in couriers:
                db.session.add(courier)
            db.session.commit()
            success_response = ut.creation_success(data, 'couriers')

        return success_response, 201

    return 'Method Not Allowed', 405


@app.route("/couriers/<int:courier_id>", methods=['GET', 'PATCH'])
def courier_info(courier_id):
    if request.method == 'PATCH':
        courier = Couriers.query.filter_by(courier_id=courier_id)

        if courier.first() is not None:
            data = request.get_json()

            for key in data.keys():
                if key not in ['courier_type', 'regions', 'working_hours']:
                    return 'Bad Request', 400

            errors = courier_schema.validate(data, partial=True)
            if len(errors) == 0:
                courier.update(data, synchronize_session=False)
                db.session.commit()
            else:
                return 'Bad Request', 400

            return jsonify(courier_schema.dump(courier.first())), 200
        else:
            return 'Not Found', 404

    # TODO: rating and earnings will be added at stage 6
    if request.method == 'GET':
        courier = Couriers.query.get(courier_id)
        courier = courier_schema.dump(courier)
        return jsonify(courier), 200

    return 'Method Not Allowed', 405


@app.route("/orders", methods=['POST'])
def orders():
    if request.method == 'POST':
        valid_keys = ['delivery_hours', 'order_id', 'region', 'weight']
        invalid_ids = {'orders': []}
        orders = []

        data = request.get_json()
        try:
            for element in data['data']:
                keys_list = list(element.keys())
                keys_list.sort()
                if keys_list != valid_keys:
                    invalid_ids['orders'].append(element['order_id'])
                    continue

                # Validation of data contained in received JSON via schema
                try:
                    order = order_schema.load(element)
                    if not Orders.query.get(element['order_id']):
                        orders.append(order)
                    else:
                        invalid_ids['orders'].append(element['order_id'])
                except ValidationError:
                    invalid_ids['orders'].append(element['order_id'])
        except KeyError:
            return 'Bad Request', 400

        if len(invalid_ids['orders']) != 0:
            validation_response = ut.validation_error(invalid_ids)
            return jsonify(validation_response), 400

        else:
            for order in orders:
                db.session.add(order)
            db.session.commit()
            success_response = ut.creation_success(data, 'orders')

        return success_response, 201

    return 'Method Not Allowed', 405


@app.route('/orders/assign', methods=['POST'])
def assign_order():
    if request.method == 'POST':
        data = request.get_json()
        if list(data.keys()) != ['courier_id']:
            return 'Bad Request', 400

        errors = courier_schema.validate(data, partial=True)
        if len(errors) != 0:
            return 'Bad Request', 400

        courier = Couriers.query.get(data['courier_id'])
        if courier is None:
            return 'Bad Request', 400
        courier_ranges = ut.datetime_ranges(courier.working_hours)
        courier_capacity = ut.CAPACITY[courier.courier_type]

        available_orders = Orders.query.filter_by(order_assigned=False)
        for order in available_orders:
            if order.region in courier.regions and \
                    courier_capacity >= order.weight:
                order_ranges = ut.datetime_ranges(order.delivery_hours)
                for c_range, o_range in product(courier_ranges, order_ranges):
                    try:
                        if c_range.is_intersection(o_range):
                            order.assigned_courier = courier.courier_id
                            order.assign_time = datetime.now()
                            order.order_assigned = True
                            db.session.commit()
                            break
                    except ValueError:
                        # TODO: дописать валидатор времени работы при загрузке курьерских данных
                        return 'Impossible time ranges', 400
                continue
            else:
                continue

    return 'Method Not Allowed', 405
