"""Plate size API routes."""
from flask import current_app, jsonify, request

from . import db
from .models import CustomerRate, InvoiceItem, Job, PlateSize, Purchase
from .validation import json_object


def register_plate_size_routes(app, role_required):
    def normalize_payload(data):
        try:
            length, width = int(data.get('length')), int(data.get('width'))
            if isinstance(data.get('length'), bool) or isinstance(data.get('width'), bool):
                raise ValueError
            minimum = data.get('min_quantity')
            minimum = None if minimum in (None, '') else int(minimum)
            if minimum is not None and (isinstance(data.get('min_quantity'), bool) or minimum < 0):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            return None, 'Length, width, or minimum quantity is invalid'
        if not 1 <= length <= 100000 or not 1 <= width <= 100000:
            return None, 'Plate dimensions are outside the allowed range'
        is_dl = data.get('is_dl', False)
        prefix, suffix = data.get('prefix'), data.get('suffix')
        if (not isinstance(is_dl, bool) or prefix is not None and (not isinstance(prefix, str) or len(prefix) > 50)
                or suffix is not None and (not isinstance(suffix, str) or len(suffix) > 50)):
            return None, 'Plate size options are invalid'
        return {
            'length': length, 'width': width, 'min_quantity': minimum,
            'is_dl': is_dl, 'prefix': prefix, 'suffix': suffix,
        }, None

    def duplicate_plate(payload, exclude_id=None):
        query = PlateSize.query.filter(
            (((PlateSize.length == payload['length']) & (PlateSize.width == payload['width'])) |
             ((PlateSize.length == payload['width']) & (PlateSize.width == payload['length']))) &
            (PlateSize.is_dl == payload['is_dl']) &
            ((PlateSize.prefix == payload['prefix']) | (PlateSize.prefix.is_(None) & (payload['prefix'] is None))) &
            ((PlateSize.suffix == payload['suffix']) | (PlateSize.suffix.is_(None) & (payload['suffix'] is None)))
        )
        if exclude_id is not None:
            query = query.filter(PlateSize.id != exclude_id)
        return query.first()

    def duplicate_error(existing_plate):
        suffix_text = ' with DL type enabled' if existing_plate.is_dl else ''
        return jsonify({'message': f'A plate size of {existing_plate.length} x {existing_plate.width}{suffix_text} already exists.'}), 400

    @app.route('/api/plate-sizes', methods=['GET'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def get_plate_sizes():
        return jsonify([size.serialize() for size in PlateSize.query.all()]), 200

    @app.route('/api/plate-sizes', methods=['POST', 'PUT'])
    @role_required(['editor', 'admin'])
    def manage_plate_sizes():
        data = json_object()
        if data is None:
            return jsonify({'message': 'Plate size data must be an object'}), 400
        payload, error = normalize_payload(data)
        if error:
            return jsonify({'message': error}), 400
        exclude_id = data.get('id') if request.method == 'PUT' else None
        if exclude_id is not None and (isinstance(exclude_id, bool) or not str(exclude_id).isdigit()):
            return jsonify({'message': 'Plate size ID is invalid'}), 400
        if request.method == 'PUT' and exclude_id is None:
            return jsonify({'message': 'Plate size ID is required'}), 400
        existing_plate = duplicate_plate(payload, int(exclude_id) if exclude_id is not None else None)
        if existing_plate:
            return duplicate_error(existing_plate)

        if request.method == 'POST':
            plate_size = PlateSize(**payload)
            db.session.add(plate_size)
            db.session.commit()
            return jsonify(plate_size.serialize()), 201

        plate_size = PlateSize.query.get_or_404(int(exclude_id))
        for key, value in payload.items():
            setattr(plate_size, key, value)
        db.session.commit()
        return jsonify(plate_size.serialize()), 200

    @app.route('/api/plate-sizes/<int:id>', methods=['PUT', 'DELETE'])
    @role_required(['editor', 'admin'])
    def update_delete_plate_size(id):
        plate_size = PlateSize.query.get_or_404(id)
        if request.method == 'PUT':
            data = json_object()
            if data is None:
                return jsonify({'message': 'Plate size data must be an object'}), 400
            payload, error = normalize_payload({
                **data,
                'length': data.get('length', plate_size.length),
                'width': data.get('width', plate_size.width),
                'min_quantity': data.get('min_quantity', plate_size.min_quantity),
                'is_dl': data.get('is_dl', plate_size.is_dl),
                'prefix': data.get('prefix', plate_size.prefix),
                'suffix': data.get('suffix', plate_size.suffix),
            })
            if error:
                return jsonify({'message': error}), 400
            if duplicate := duplicate_plate(payload, id):
                return duplicate_error(duplicate)
            for key, value in payload.items():
                setattr(plate_size, key, value)
            db.session.commit()
            return jsonify(plate_size.serialize()), 200

        try:
            referenced = []
            if Purchase.query.filter_by(size_id=id).first():
                referenced.append('purchase records')
            if Job.query.filter_by(plate_size_id=id).first():
                referenced.append('delivery challan jobs')
            if InvoiceItem.query.filter_by(plate_size_id=id).first():
                referenced.append('invoice items')
            if CustomerRate.query.filter_by(plate_size_id=id).first():
                referenced.append('customer rates')
            if referenced:
                message = 'Cannot delete plate size as it is referenced in: ' + ' and '.join(referenced) + '.'
                return jsonify({'message': message}), 409
            db.session.delete(plate_size)
            db.session.commit()
            return jsonify({'message': 'Plate size deleted'}), 200
        except Exception:
            current_app.logger.exception('Plate size delete failed')
            return jsonify({'message': 'Server error deleting plate size'}), 500

    @app.route('/api/plate-sizes/<int:size_id>/min-quantity', methods=['PUT'])
    @role_required(['editor', 'admin'])
    def update_min_quantity(size_id):
        data = json_object()
        if data is None:
            return jsonify({'message': 'Minimum quantity data must be an object'}), 400
        min_quantity = data.get('min_quantity')
        if min_quantity is None:
            return jsonify({'message': 'min_quantity is required'}), 400
        if isinstance(min_quantity, bool) or not isinstance(min_quantity, int) or min_quantity < 0 or min_quantity > 10000000:
            return jsonify({'message': 'min_quantity must be a non-negative integer'}), 400
        plate_size = PlateSize.query.get(size_id)
        if not plate_size:
            return jsonify({'message': 'Plate size not found'}), 404
        try:
            plate_size.min_quantity = min_quantity
            db.session.commit()
            return jsonify({'message': 'Minimum quantity updated successfully'}), 200
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Plate minimum quantity update failed')
            return jsonify({'message': 'Failed to update minimum quantity'}), 500

    @app.route('/api/plate-sizes/<int:id>', methods=['GET'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def get_plate_size(id):
        return jsonify(PlateSize.query.get_or_404(id).serialize()), 200
