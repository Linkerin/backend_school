import pytz
from flask import Flask, request, jsonify
from datetime import datetime
from itertools import product
from marshmallow import ValidationError
from sqlalchemy import types
import app.utils as ut
from app import app, db
from app.models import Couriers, Orders, OrdersBundle, Regions
from app.schemas import courier_schema, order_schema


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
        errors = []

        data = request.get_json()
        try:
            for element in data['data']:
                keys_list = list(element.keys())
                keys_list.sort()
                if keys_list != valid_keys:
                    errors.append({
                        f"id {element['order_id']}": 'Incorrect properties'
                    })
                    invalid_ids['couriers'].append(element['courier_id'])
                    continue

                # Validation of data contained in received JSON via schema
                try:
                    courier = courier_schema.load(element)
                    if not Couriers.query.get(element['courier_id']):
                        couriers.append(courier)
                    else:
                        errors.append({
                            f"id {element['order_id']}": 'id already exists'
                        })
                        invalid_ids['couriers'].append(element['courier_id'])
                except ValidationError as err:
                    invalid_ids['couriers'].append(element['courier_id'])
                    errors.append({f"id {element['courier_id']}": str(err)})
        except KeyError:
            bad_request_msg = {
                'Error': "'data' key was not found"
            }
            return jsonify(bad_request_msg), 400

        if len(invalid_ids['couriers']) != 0:
            validation_response = ut.validation_error(invalid_ids, errors)
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
                    bad_request_msg = {
                        'Error': 'Incorrect properties'
                    }
                    return jsonify(bad_request_msg), 400

            errors = courier_schema.validate(data, partial=True)
            if len(errors) != 0:
                bad_request_msg = {
                    'Error': errors
                }
                return jsonify(bad_request_msg), 400
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
            response = courier_schema.dump(courier.first())
            del response['earnings']
            del response['rating']
            return jsonify(response), 200

        else:
            return 'Not Found', 404

    if request.method == 'GET':
        courier = Couriers.query.get(courier_id)
        not_completed = True
        for bundle in courier.bundles:
            if bundle.completed is True and bundle.deleted is False:
                not_completed = False

        if len(courier.bundles) == 0 or not_completed is True:
            courier = courier_schema.dump(courier)
            del courier['earnings']
            del courier['rating']
        else:
            courier = courier_schema.dump(courier)

        return jsonify(courier), 200

    return 'Method Not Allowed', 405


@app.route("/orders", methods=['POST'])
def orders():
    if request.method == 'POST':
        valid_keys = ['delivery_hours', 'order_id', 'region', 'weight']
        invalid_ids = {'orders': []}
        orders = []
        errors = []

        data = request.get_json()
        try:
            for element in data['data']:
                keys_list = list(element.keys())
                keys_list.sort()
                if keys_list != valid_keys:
                    invalid_ids['orders'].append(element['order_id'])
                    errors.append({
                        f"id {element['order_id']}": 'Incorrect properties'
                    })
                    continue

                # Validation of data contained in received JSON via schema
                try:
                    order = order_schema.load(element)
                    if not Orders.query.get(element['order_id']):
                        orders.append(order)
                    else:
                        invalid_ids['orders'].append(element['order_id'])
                        errors.append({
                            f"id {element['order_id']}": 'id already exists'
                        })
                except ValidationError as err:
                    invalid_ids['orders'].append(element['order_id'])
                    errors.append({f"id {element['order_id']}": str(err)})
        except KeyError:
            bad_request_msg = {
                'Error': "'data' key was not found"
            }
            return jsonify(bad_request_msg), 400

        if len(invalid_ids['orders']) != 0:
            validation_response = ut.validation_error(invalid_ids, errors)
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
            bad_request_msg = {
                'Error': errors
            }
            return jsonify(bad_request_msg), 400

        courier = Couriers.query.get(data['courier_id'])
        if courier is None:
            bad_request_msg = {
                'Error': 'Courier id was not found'
            }
            return jsonify(bad_request_msg), 400

        # The following block checks whether the courier already
        # has assigned and not completed orders
        orders = Orders.query.filter_by(assigned_courier=data['courier_id'],
                                        completed=False).all()
        if len(orders) != 0:
            orders_msg = ut.assigned_orders_msg(orders,
                                                orders[0].assign_time)
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
                        assigned_orders.append(order)
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
            orders = (Orders.query
                      .filter_by(completed=False,
                                 assigned_courier=courier.courier_id)
                      .all())
            assignment_msg = ut.assigned_orders_msg(orders,
                                                    orders[0].assign_time)
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
            bad_request_msg = {
                'Error': 'POST data is incorrect'
            }
            return jsonify(bad_request_msg), 400

        keys_list.sort()
        if keys_list != valid_keys:
            bad_request_msg = {
                'Error': 'Incorrect properties'
            }
            return jsonify(bad_request_msg), 400

        order = Orders.query.get(data['order_id'])
        if order is None or order.assigned is False or \
                order.assigned_courier != data['courier_id']:
            bad_request_msg = {
                'Error': 'Sent values are incorrect'
            }
            return jsonify(bad_request_msg), 400

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

        delivery_time = ut.order_delivery_time(order, complete_time)
        if type(delivery_time) != float:
            bad_request_msg = {
                'Error': f'{delivery_time}'
            }
            return jsonify(bad_request_msg), 400

        if order.completed is False:
            order.completed = True
            order.complete_time = complete_time
            order.delivery_time = delivery_time
            db.session.commit()

            # The following block updates average delivery time
            # per region when the order is completed
            regions = (Regions.query.filter_by(region_id=order.region,
                                               courier_id=data['courier_id'])
                                    .first())
            if regions is not None:
                average = regions.avg_delivery_time
                average = (average + delivery_time) / 2
                regions.avg_delivery_time = average
            else:
                new_region = Regions(region_id=order.region,
                                     courier_id=order.assigned_courier,
                                     avg_delivery_time=delivery_time)
                db.session.add(new_region)

            bundle = OrdersBundle.query.get(order.bundle)
            bundle_finished = ut.bundle_finished(bundle)
            if bundle_finished is True:
                ut.complete_bundle(bundle, complete_time)
            db.session.commit()

        success_msg = {
            'order_id': order.order_id
        }

        return jsonify(success_msg), 200

    return 'Method Not Allowed', 405
