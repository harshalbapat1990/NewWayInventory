"""Customer and customer rate API routes."""
from flask import current_app, jsonify, request

from . import db
from .audit import record_audit_event
from .models import Customer, CustomerRate, PlateSize, _money_cents
from .validation import json_object


def _validated_customer_payload(data):
    limits = {
        'company_name': 100, 'contact_person': 100, 'address': 200,
        'phone': 20, 'mobile': 20,
    }
    for field, maximum in limits.items():
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            return None, f'{field} is required and must be at most {maximum} characters'
    emails = data.get('email')
    if isinstance(emails, list):
        if len(emails) > 10 or any(not isinstance(email, str) for email in emails):
            return None, 'Email addresses are invalid'
        emails = ','.join(email.strip() for email in emails)
    if not isinstance(emails, str) or len(emails) > 500:
        return None, 'Email addresses are invalid'
    for field, maximum in (('gstin', 15), ('state', 50), ('code', 10)):
        value = data.get(field)
        if value is not None and (not isinstance(value, str) or len(value) > maximum):
            return None, f'{field} is invalid'
    return {**data, 'email': emails}, None


def register_customer_routes(app, role_required, require_current_role):
    @app.route('/api/customers', methods=['GET', 'POST'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def manage_customers():
        if request.method == 'POST':
            if not require_current_role('editor', 'admin'):
                return jsonify({'message': 'Access denied'}), 403
            data = json_object()
            if data is None:
                return jsonify({'message': 'Customer data must be an object'}), 400
            data, error = _validated_customer_payload(data)
            if error:
                return jsonify({'message': error}), 400
            new_customer = Customer(
                company_name=data['company_name'], contact_person=data['contact_person'],
                address=data['address'], phone=data['phone'], mobile=data['mobile'],
                email=data['email'],
                gstin=data.get('gstin'), state=data.get('state', 'Maharashtra'),
                code=data.get('code', '27')
            )
            db.session.add(new_customer)
            db.session.flush()
            record_audit_event('customer.created', 'customer', new_customer.id)
            db.session.commit()
            return jsonify(new_customer.serialize()), 201

        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        query = Customer.query
        if not include_archived:
            query = query.filter_by(is_archived=False)
        return jsonify([customer.serialize() for customer in query.order_by(Customer.company_name.asc()).all()]), 200

    @app.route('/api/customers/<int:id>', methods=['GET'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def get_customer(id):
        return jsonify(Customer.query.get_or_404(id).serialize()), 200

    @app.route('/api/customers/<int:id>/archive', methods=['PATCH'])
    @role_required(['editor', 'admin'])
    def archive_customer(id):
        customer = Customer.query.get_or_404(id)
        customer.is_archived = True
        record_audit_event('customer.archived', 'customer', customer.id)
        db.session.commit()
        return jsonify(customer.serialize()), 200

    @app.route('/api/customers/<int:id>/restore', methods=['PATCH'])
    @role_required(['editor', 'admin'])
    def restore_customer(id):
        customer = Customer.query.get_or_404(id)
        customer.is_archived = False
        record_audit_event('customer.restored', 'customer', customer.id)
        db.session.commit()
        return jsonify(customer.serialize()), 200

    @app.route('/api/customers/<int:id>', methods=['PUT', 'DELETE'])
    @role_required(['editor', 'admin'])
    def update_delete_customer(id):
        customer = Customer.query.get_or_404(id)
        if request.method == 'PUT':
            data = json_object()
            if data is None:
                return jsonify({'message': 'Customer data must be an object'}), 400
            data, error = _validated_customer_payload(data)
            if error:
                return jsonify({'message': error}), 400
            customer.company_name = data['company_name']
            customer.contact_person = data['contact_person']
            customer.address = data['address']
            customer.phone = data['phone']
            customer.mobile = data['mobile']
            customer.email = data['email']
            customer.gstin = data.get('gstin')
            customer.state = data.get('state', 'Maharashtra')
            customer.code = data.get('code', '27')
            record_audit_event('customer.updated', 'customer', customer.id)
            db.session.commit()
            return jsonify(customer.serialize()), 200
        if not require_current_role('admin'):
            return jsonify({'message': 'Access denied'}), 403
        db.session.delete(customer)
        record_audit_event('customer.deleted', 'customer', customer.id)
        db.session.commit()
        return jsonify({'message': 'Customer deleted successfully'}), 200

    @app.route('/api/customer-rates/<int:customer_id>', methods=['GET'])
    @role_required(['accountant', 'admin'])
    def get_customer_rates(customer_id):
        rates = CustomerRate.query.filter_by(customer_id=customer_id).all()
        return jsonify([rate.to_dict() for rate in rates])

    @app.route('/api/customer-rates', methods=['POST'])
    @role_required(['accountant', 'admin'])
    def save_customer_rates():
        data = json_object()
        if data is None:
            return jsonify({'error': 'Rate data must be an object'}), 400
        customer_id = data.get('customer_id')
        rates_data = data.get('rates', [])
        if isinstance(customer_id, bool):
            return jsonify({'error': 'Customer ID is required'}), 400
        try:
            customer_id = int(customer_id)
        except (TypeError, ValueError, OverflowError):
            return jsonify({'error': 'Customer ID is required'}), 400
        if customer_id < 1:
            return jsonify({'error': 'Customer ID is required'}), 400
        if not isinstance(rates_data, list):
            return jsonify({'error': 'Rates must be a list'}), 400
        if len(rates_data) > 500:
            return jsonify({'error': 'Too many customer rates in one request'}), 400
        if any(not isinstance(rate_data, dict) or not rate_data.get('plate_size_id') for rate_data in rates_data):
            return jsonify({'error': 'Each rate requires a plate size'}), 400
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        validated_rates = []
        try:
            for rate_data in rates_data:
                if not isinstance(rate_data, dict):
                    return jsonify({'error': 'Each rate must be an object'}), 400
                plate_size_id = rate_data.get('plate_size_id')
                if isinstance(plate_size_id, bool):
                    return jsonify({'error': 'Plate size is invalid'}), 400
                plate_size_id = int(plate_size_id)
                if plate_size_id < 1 or not db.session.get(PlateSize, plate_size_id):
                    return jsonify({'error': 'Plate size not found'}), 404
                plate_rate = rate_data.get('plate_rate', 0)
                baking_rate = rate_data.get('baking_rate', 0)
                plate_cents, baking_cents = _money_cents(plate_rate), _money_cents(baking_rate)
                if min(plate_cents, baking_cents) < 0 or max(plate_cents, baking_cents) > 100000000000:
                    return jsonify({'error': 'Rates are outside the allowed range'}), 400
                validated_rates.append((plate_size_id, plate_rate, baking_rate))
            for plate_size_id, plate_rate_value, baking_rate_value in validated_rates:
                existing_rate = CustomerRate.query.filter_by(
                    customer_id=customer_id, plate_size_id=plate_size_id
                ).first()
                if existing_rate:
                    existing_rate.plate_rate = plate_rate_value
                    existing_rate.baking_rate = baking_rate_value
                else:
                    db.session.add(CustomerRate(
                        customer_id=customer_id, plate_size_id=plate_size_id,
                        plate_rate=plate_rate_value, baking_rate=baking_rate_value
                    ))
            record_audit_event('customer.rates_updated', 'customer', customer_id)
            db.session.commit()
            return jsonify({'message': 'Rates saved successfully'})
        except (TypeError, ValueError):
            db.session.rollback()
            return jsonify({'error': 'Rates must be valid monetary values'}), 400
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Customer rate save failed')
            return jsonify({'error': 'Unable to save customer rates'}), 500
