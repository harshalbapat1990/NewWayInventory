"""Inventory, stock summary, purchase and waste API routes."""
from datetime import date

from flask import jsonify, request
from sqlalchemy import text

from . import db
from .audit import record_audit_event
from .models import PlateSize, Purchase, WastePlate


def register_inventory_routes(app, role_required, require_current_role):
    def positive_integer(value, maximum=10000000):
        if isinstance(value, bool) or not (isinstance(value, int) or isinstance(value, str) and value.isdigit()):
            return None
        parsed = int(value)
        return parsed if 1 <= parsed <= maximum else None

    @app.route('/api/waste-plates', methods=['GET', 'POST'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def manage_waste_plates():
        if request.method == 'POST':
            if not require_current_role('user', 'editor', 'admin'):
                return jsonify({"message": "Access denied"}), 403
            data = request.get_json(silent=True)
            size_id = positive_integer(data.get('size_id')) if isinstance(data, dict) else None
            quantity = positive_integer(data.get('quantity_wasted')) if isinstance(data, dict) else None
            try:
                waste_date = date.fromisoformat(data.get('waste_date')) if isinstance(data, dict) else None
            except (TypeError, ValueError):
                waste_date = None
            if not size_id or not quantity or not waste_date:
                return jsonify({'message': 'Waste size, quantity, and date are required and must be valid'}), 400
            if not db.session.get(PlateSize, size_id):
                return jsonify({'message': 'Plate size not found'}), 404
            new_waste_plate = WastePlate(size_id=size_id, quantity_wasted=quantity, waste_date=waste_date)
            db.session.add(new_waste_plate)
            db.session.flush()
            record_audit_event('waste.created', 'waste_plate', new_waste_plate.id)
            db.session.commit()
            return jsonify(new_waste_plate.serialize()), 201
        waste_plates = WastePlate.query.filter_by(is_archived=False).all()
        return jsonify([waste_plate.serialize() for waste_plate in waste_plates]), 200

    @app.route('/api/waste-plates/<int:id>', methods=['DELETE'])
    @role_required(['admin'])  # Only admin can delete waste plates
    def delete_waste_plate(id):
        waste_plate = WastePlate.query.get_or_404(id)
        record_audit_event('waste.deleted', 'waste_plate', waste_plate.id)
        db.session.delete(waste_plate)
        db.session.commit()
        return jsonify({"message": "Waste plate deleted successfully"}), 200

    @app.route('/api/stock-summary', methods=['GET'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def get_stock_summary():
        result = db.session.execute(text("SELECT * FROM stock_summary_view")).fetchall()
        stock_summary = [dict(row._mapping) for row in result]
        return jsonify(stock_summary), 200

    @app.route('/api/customer-summary', methods=['GET'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def get_customer_summary():
        result = db.session.execute(text("SELECT * FROM customer_summary_view")).fetchall()
        customer_summary = [dict(row._mapping) for row in result]
        return jsonify(customer_summary), 200

    @app.route('/api/plate-summary', methods=['GET'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def get_plate_summary():
        size_id = request.args.get('size_id', type=int)
        query = "SELECT * FROM plate_summary_view"
        
        if size_id:
            query += " WHERE size_id = :size_id"
            result = db.session.execute(text(query), {"size_id": size_id}).fetchall()
        else:
            result = db.session.execute(text(query)).fetchall()
        
        plate_summary = [
            {
                "size_id": row[0],
                "length": row[1],
                "width": row[2],
                "min_quantity": row[3],
                "is_dl": row[4],
                "prefix": row[5],        # new
                "suffix": row[6],        # new
                "available_quantity": row[7]
            }
            for row in result
        ]
        return jsonify(plate_summary), 200

    @app.route('/api/purchases', methods=['GET', 'POST'])
    @role_required(['user', 'editor', 'admin'])  # Accessible by all roles
    def manage_purchases():
        if request.method == 'POST':
            data = request.get_json(silent=True)
            quantity = positive_integer(data.get('quantity')) if isinstance(data, dict) else None
            size_id = positive_integer(data.get('size_id')) if isinstance(data, dict) else None
            try:
                purchase_date = date.fromisoformat(data.get('date')) if isinstance(data, dict) else None
            except (TypeError, ValueError):
                purchase_date = None
            if not quantity or not size_id or not purchase_date:
                return jsonify({'message': 'Purchase size, quantity, and date are required and must be valid'}), 400
            if not db.session.get(PlateSize, size_id):
                return jsonify({'message': 'Plate size not found'}), 404
            new_purchase = Purchase(
                date=purchase_date,
                size_id=size_id,
                quantity=quantity
            )
            db.session.add(new_purchase)
            db.session.flush()
            record_audit_event('purchase.created', 'purchase', new_purchase.id)
            db.session.commit()
            return jsonify(new_purchase.serialize()), 201

        purchases = Purchase.query.filter_by(is_archived=False).all()
        return jsonify([purchase.serialize() for purchase in purchases]), 200

    @app.route('/api/purchases/<int:id>', methods=['PUT'])
    @role_required(['editor', 'admin'])  # Editor and admin can update purchases
    def update_purchase(id):
        purchase = Purchase.query.get_or_404(id)
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'message': 'Purchase data must be an object'}), 400
        size_id = positive_integer(data.get('size_id'))
        quantity = positive_integer(data.get('quantity'))
        try:
            purchase_date = date.fromisoformat(data.get('date'))
        except (TypeError, ValueError):
            purchase_date = None
        if not size_id or not quantity or not purchase_date:
            return jsonify({'message': 'Purchase size, quantity, and date are required and must be valid'}), 400
        if not db.session.get(PlateSize, size_id):
            return jsonify({'message': 'Plate size not found'}), 404
        purchase.date = purchase_date
        purchase.size_id = size_id
        purchase.quantity = quantity
        record_audit_event('purchase.updated', 'purchase', purchase.id)
        db.session.commit()
        return jsonify(purchase.serialize()), 200

    @app.route('/api/purchases/<int:id>', methods=['DELETE'])
    @role_required(['admin'])  # Only admin can delete purchases
    def delete_purchase(id):
        purchase = Purchase.query.get_or_404(id)
        record_audit_event('purchase.deleted', 'purchase', purchase.id)
        db.session.delete(purchase)
        db.session.commit()
        return jsonify({"message": "Purchase deleted successfully"}), 200

