from flask import Flask, request, jsonify
from marshmallow import ValidationError
from datetime import datetime
from itertools import product
import pytz
from sqlalchemy import types
from app import app, db
from app.models import Couriers, Orders, OrdersBundle
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
            if len(errors) != 0:
                return 'Bad Request', 400
            courier.update(data, synchronize_session=False)
            db.session.commit()

            """ This block of code checks whether new courier info
                complies with assigned orders and dismisses them if
                necessary.
            """
            for key, value in data.items():
                if key == 'courier_type':
                    ut.courier_type_upd(value, courier_id)
                elif key == 'regions':
                    ut.regions_upd(value, courier_id)
                elif key == 'working_hours':
                    ut.working_hours_upd(value, courier_id)

            return jsonify(courier_schema.dump(courier.first())), 200
        else:
            return 'Not Found', 404

    # TODO: rating and earnings will be added at stage 6
    if request.method == 'GET':
        courier = Couriers.query.get(courier_id)
        for bundle in courier.bundles:
            if bundle.completed is True:
                not_completed = False

        if len(courier.bundles) == 0 or not_completed is False:
            courier = courier_schema.dump(courier)
            del courier['earnings']
            del courier['rating']
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


@app.route("/orders/assign", methods=['POST'])
def assign_order():
    if request.method == 'POST':
        data = request.get_json()
        try:
            if list(data.keys()) != ['courier_id']:
                bad_request_msg = {
                    'Error': 'Additional properties are not allowed'
                }
                return jsonify(bad_request_msg), 400
        except AttributeError:
            return 'Bad Request', 400

        errors = courier_schema.validate(data, partial=True)
        if len(errors) != 0:
            return 'Bad Request', 400  # TODO: сделать пояснения ошибок

        courier = Couriers.query.get(data['courier_id'])
        if courier is None:
            bad_request_msg = {
                'Error': 'Courier id was not found'
            }
            return jsonify(bad_request_msg), 400

        if len(courier.orders) != 0:
            assigned_orders = []
            for order in courier.orders:
                if order.completed is False:
                    assigned_orders.append(order.order_id)
            if len(assigned_orders) != 0:
                assign_time = courier.orders[0].assign_time
                orders_msg = ut.assigned_orders_msg(assigned_orders,
                                                    assign_time)
                return jsonify(orders_msg), 200

        courier_ranges = ut.datetime_ranges(courier.working_hours)
        courier_capacity = ut.CAPACITY[courier.courier_type]

        available_orders = Orders.query.filter_by(assigned=False)
        assign_time = datetime.now(tz=pytz.timezone('Europe/Moscow'))
        assigned_orders = []
        bundle_id = ut.bundle_id()
        for order in available_orders:
            if order.region in courier.regions and \
                    courier_capacity >= order.weight:
                order_ranges = ut.datetime_ranges(order.delivery_hours)
                for c_range, o_range in product(courier_ranges, order_ranges):
                    if c_range.is_intersection(o_range):
                        order.assigned_courier = courier.courier_id
                        order.assign_time = assign_time
                        order.assigned = True
                        order.bundle = bundle_id
                        courier_capacity -= order.weight
                        assigned_orders.append(order.order_id)
                        break
                continue
            else:
                continue

        if len(assigned_orders) != 0:
            bundle = OrdersBundle(bundle_id=bundle_id,
                                  courier_id=courier.courier_id,
                                  init_courier_type=courier.courier_type,
                                  assign_time=assign_time)
            db.session.add(bundle)
            db.session.commit()
            # TODO: переписать, чтобы назначеные заказы брались именно из БД
            assignment_msg = ut.assigned_orders_msg(assigned_orders,
                                                    assign_time)
        else:
            assignment_msg = ut.assigned_orders_msg(assigned_orders)

        return jsonify(assignment_msg), 200

    return 'Method Not Allowed', 405


@app.route("/orders/complete", methods=['POST'])
def order_completed():
    if request.method == 'POST':
        valid_keys = ['complete_time', 'courier_id', 'order_id']
        data = request.get_json()

        try:
            keys_list = list(data.keys())
        except AttributeError:
            return 'Bad Request', 400

        keys_list.sort()
        if keys_list != valid_keys:
            return 'Bad Request', 400

        order = Orders.query.get(data['order_id'])
        if order is None or order.assigned is False or \
                order.assigned_courier != data['courier_id']:
            return 'Bad Request', 400

        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        if data['complete_time'][10] != 'T':
            date_format = '%Y-%m-%d %H:%M:%S.%f%z'
        try:
            complete_time = datetime.strptime(data['complete_time'],
                                              date_format)
        except ValueError:
            bad_request_msg = {
                'Error': 'Datetime format should be ISO 8601 or RFC3339'
            }
            return jsonify(bad_request_msg), 400

        order.completed = True
        order.complete_time = complete_time
        bundle = OrdersBundle.query.get(order.bundle)
        bundle.earning += (ut.EARNING_COEF[bundle.init_courier_type] *
                           ut.ORDER_EARNING)
        bundle_finished = ut.bundle_finished(bundle)
        if bundle_finished is True:
            ut.complete_bundle(bundle)

        db.session.commit()
        success_msg = {
            'order_id': order.order_id
        }

        return jsonify(success_msg), 200

    return 'Method Not Allowed', 405
