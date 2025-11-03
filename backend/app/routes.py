from flask import request, jsonify, render_template_string, send_file, send_from_directory
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import text, and_
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from .models import User, Customer, PlateSize, WastePlate, Job, Purchase, Plate, Challan, CustomerRate, Invoice, InvoiceItem  # Added Invoice and InvoiceItem to imports
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from functools import wraps
import os
import sys
from flask_mail import Mail, Message

# Initialize Mail
mail = Mail()

def role_required(required_roles):
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = get_jwt()  # Use get_jwt() to retrieve the full JWT claims
            roles_hierarchy = {'admin': 1, 'editor': 2, 'user': 3}
            user_role_level = roles_hierarchy.get(user.get('role', ''), 0)
            required_role_level = max([roles_hierarchy.get(role, 0) for role in required_roles])

            if user_role_level > required_role_level:
                return jsonify({"message": "Access denied"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

def register_routes(app):
    @app.route('/api/')
    def home():
        return render_template_string("<h1>Welcome to the Inventory Management App</h1>")

    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json()
        valid_roles = ['admin', 'editor', 'user']
        if data['role'] not in valid_roles:
            return jsonify({"message": "Invalid role"}), 400

        new_user = User(
            username=data['username'],
            password=generate_password_hash(data['password'], method='pbkdf2:sha256'),
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role']
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and check_password_hash(user.password, data['password']):
            # Create both access and refresh tokens
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={"username": user.username, "role": user.role}
            )
            refresh_token = create_refresh_token(identity=str(user.id))
            return jsonify(access_token=access_token, refresh_token=refresh_token), 200
        return jsonify({"message": "Invalid credentials"}), 401

    # Add this new refresh token endpoint
    @app.route('/api/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        # Create a new access token
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"username": user.username, "role": user.role}
        )
        return jsonify(access_token=access_token), 200

    @app.route('/api/customers', methods=['GET', 'POST'])
    @role_required(['user', 'editor', 'admin'])  # Accessible by all roles
    def manage_customers():
        if request.method == 'POST':
            data = request.get_json()
            new_customer = Customer(
                company_name=data['company_name'],
                contact_person=data['contact_person'],
                address=data['address'],
                phone=data['phone'],
                mobile=data['mobile'],
                email=','.join(data['email']) if isinstance(data['email'], list) else data['email'],
                gstin=data.get('gstin'),
                state=data.get('state', 'Maharashtra'),
                code=data.get('code', '27')
            )
            db.session.add(new_customer)
            db.session.commit()
            return jsonify(new_customer.serialize()), 201

        # Debugging: Print the query results
        customers = Customer.query.all()
        return jsonify([customer.serialize() for customer in customers]), 200

    @app.route('/api/customers/<int:id>', methods=['PUT', 'DELETE'])
    @role_required(['editor', 'admin', 'accountant'])  # Editor, admin, and accountant can update or delete customers
    def update_delete_customer(id):
        customer = Customer.query.get_or_404(id)
        if request.method == 'PUT':
            data = request.get_json()
            customer.company_name = data['company_name']
            customer.contact_person = data['contact_person']
            customer.address = data['address']
            customer.phone = data['phone']
            customer.mobile = data['mobile']
            customer.email = ','.join(data['email']) if isinstance(data['email'], list) else data['email']
            customer.gstin = data.get('gstin')
            customer.state = data.get('state', 'Maharashtra')
            customer.code = data.get('code', '27')
            db.session.commit()
            return jsonify(customer.serialize()), 200
        elif request.method == 'DELETE':
            db.session.delete(customer)
            db.session.commit()
            return jsonify({"message": "Customer deleted successfully"}), 200

    @app.route('/api/plate-sizes', methods=['GET'])
    @role_required(['user', 'editor', 'admin'])
    def get_plate_sizes():
        plate_sizes = PlateSize.query.all()
        return jsonify([plate_size.serialize() for plate_size in plate_sizes]), 200

    @app.route('/api/plate-sizes', methods=['POST', 'PUT'])
    @role_required(['editor', 'admin'])
    def manage_plate_sizes():
        data = request.get_json()
        # print(data)
        length = data['length']
        width = data['width']
        is_dl = data.get('is_dl', False)  # Default to False if not provided
        prefix = data.get('prefix')  # <-- new
        suffix = data.get('suffix')  # <-- new

        # Check if a plate size with the same dimensions (in any order) and DL condition already exists
        existing_plate = PlateSize.query.filter(
            (
            ((PlateSize.length == length) & (PlateSize.width == width)) |
            ((PlateSize.length == width) & (PlateSize.width == length))
            ) & (PlateSize.is_dl == is_dl)
        ).first()

        if existing_plate:
            if is_dl:
                return jsonify({"message": f"A plate size of {existing_plate.length} x {existing_plate.width} with DL type enabled already exists."}), 400
            else:
                return jsonify({"message": f"A plate size of {existing_plate.length} x {existing_plate.width} already exists."}), 400

        if request.method == 'POST':
            new_plate_size = PlateSize(
                length=length,
                width=width,
                min_quantity=data.get('min_quantity', None),
                is_dl=data.get('is_dl', False),
                prefix=prefix,  # <-- set
                suffix=suffix   # <-- set
            )
            db.session.add(new_plate_size)
            db.session.commit()
            return jsonify(new_plate_size.serialize()), 201

        if request.method == 'PUT':
            plate_size_id = data['id']
            plate_size = PlateSize.query.get_or_404(plate_size_id)
            plate_size.length = length
            plate_size.width = width
            plate_size.min_quantity = data.get('min_quantity', None)
            plate_size.is_dl = data.get('is_dl', False)
            plate_size.prefix = prefix  # <-- update
            plate_size.suffix = suffix  # <-- update
            db.session.commit()
            return jsonify(plate_size.serialize()), 200

    @app.route('/api/plate-sizes/<int:id>', methods=['PUT', 'DELETE'])
    @role_required(['editor', 'admin'])
    def update_delete_plate_size(id):
        plate_size = PlateSize.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            plate_size.length = data.get('length', plate_size.length)
            plate_size.width = data.get('width', plate_size.width)
            plate_size.min_quantity = data.get('min_quantity', plate_size.min_quantity)
            plate_size.is_dl = data.get('is_dl', plate_size.is_dl)
            plate_size.prefix = data.get('prefix', plate_size.prefix)
            plate_size.suffix = data.get('suffix', plate_size.suffix)
            db.session.commit()
            return jsonify(plate_size.serialize()), 200

        if request.method == 'DELETE':
            # Check references in related tables
            referenced_messages = []

            if Purchase.query.filter_by(size_id=id).first():
                referenced_messages.append("purchase records")
            if Job.query.filter_by(plate_size_id=id).first():
                referenced_messages.append("delivery challan jobs")
            if InvoiceItem.query.filter_by(plate_size_id=id).first():
                referenced_messages.append("invoice items")

            if referenced_messages:
                # Concatenate messages with ' and ' (no priority)
                message = "Cannot delete plate size as it is referenced in: " + " and ".join(referenced_messages) + "."
                return jsonify({"message": message}), 409

            # safe to delete
            db.session.delete(plate_size)
            db.session.commit()
            return jsonify({"message": "Plate size deleted"}), 200

    @app.route('/api/plate-sizes/<int:size_id>/min-quantity', methods=['PUT'])
    @role_required(['user', 'editor', 'admin'])  # Editor and admin can update or delete plate sizes
    def update_min_quantity(size_id):
        data = request.get_json()
        min_quantity = data.get('min_quantity')

        if min_quantity is None:
            return jsonify({"message": "min_quantity is required"}), 400

        plate_size = PlateSize.query.get(size_id)
        if not plate_size:
            return jsonify({"message": "Plate size not found"}), 404

        try:
            plate_size.min_quantity = min_quantity
            db.session.commit()
            return jsonify({"message": "Minimum quantity updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Failed to update minimum quantity", "error": str(e)}), 500

    @app.route('/api/plate-sizes/<int:id>', methods=['GET'])
    def get_plate_size(id):
        plate_size = PlateSize.query.get_or_404(id)
        return jsonify(plate_size.serialize()), 200

    @app.route('/api/waste-plates', methods=['GET', 'POST'])
    @jwt_required()
    def manage_waste_plates():
        if request.method == 'POST':
            data = request.get_json()
            new_waste_plate = WastePlate(
                size_id=data['size_id'],
                quantity_wasted=data['quantity_wasted'],
                waste_date=datetime.strptime(data['waste_date'], '%Y-%m-%d').date()
            )
            db.session.add(new_waste_plate)
            db.session.commit()
            return jsonify(new_waste_plate.serialize()), 201
        waste_plates = WastePlate.query.all()
        return jsonify([waste_plate.serialize() for waste_plate in waste_plates]), 200

    @app.route('/api/waste-plates/<int:id>', methods=['DELETE'])
    @role_required(['admin'])  # Only admin can delete waste plates
    def delete_waste_plate(id):
        waste_plate = WastePlate.query.get_or_404(id)
        db.session.delete(waste_plate)
        db.session.commit()
        return jsonify({"message": "Waste plate deleted successfully"}), 200

    @app.route('/api/jobs', methods=['GET', 'POST'])
    @jwt_required()
    def manage_jobs():
        if request.method == 'POST':
            data = request.get_json()
            new_job = Job(
                job_code=data['job_code'],
                job_date=data['job_date'],
                customer_id=data['customer_id'],
                remark=data['remark']
            )
            db.session.add(new_job)
            db.session.commit()
            return jsonify(new_job.serialize()), 201
        jobs = Job.query.all()
        return jsonify([job.serialize() for job in jobs]), 200

    @app.route('/api/job-code', methods=['GET'])
    @jwt_required()
    def generate_job_code():
        # Query the JobOrder table for the maximum job_code
        max_job_code = db.session.query(db.func.max(Job.id)).scalar()
        # Generate the next job_code
        new_job_code = f"JC-{max_job_code + 1:04d}" if max_job_code else "JC-0001"
        return jsonify({"job_code": new_job_code}), 200

    @app.route('/api/stock-summary', methods=['GET'])
    @jwt_required()
    def get_stock_summary():
        result = db.session.execute(text("SELECT * FROM stock_summary_view")).fetchall()
        stock_summary = [dict(row) for row in result]
        return jsonify(stock_summary), 200

    @app.route('/api/customer-summary', methods=['GET'])
    @jwt_required()
    def get_customer_summary():
        result = db.session.execute(text("SELECT * FROM customer_summary_view")).fetchall()
        customer_summary = [dict(row) for row in result]
        return jsonify(customer_summary), 200

    @app.route('/api/plate-summary', methods=['GET'])
    @jwt_required()
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
        user_id = get_jwt_identity()  # Get the user ID from the token
        claims = get_jwt()  # Get additional claims (e.g., username, role)
        if request.method == 'POST':
            data = request.get_json()
            new_purchase = Purchase(
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                size_id=data['size_id'],
                quantity=data['quantity']
            )
            db.session.add(new_purchase)
            db.session.commit()
            return jsonify(new_purchase.serialize()), 201

        purchases = Purchase.query.all()
        return jsonify([purchase.serialize() for purchase in purchases]), 200

    @app.route('/api/purchases/<int:id>', methods=['PUT'])
    @role_required(['editor', 'admin'])  # Editor and admin can update purchases
    def update_purchase(id):
        purchase = Purchase.query.get_or_404(id)
        data = request.get_json()
        purchase.date = data['date']
        purchase.size_id = data['size_id']
        purchase.quantity = data['quantity']
        db.session.commit()
        return jsonify(purchase.serialize()), 200

    @app.route('/api/purchases/<int:id>', methods=['DELETE'])
    @role_required(['admin'])  # Only admin can delete purchases
    def delete_purchase(id):
        purchase = Purchase.query.get_or_404(id)
        db.session.delete(purchase)
        db.session.commit()
        return jsonify({"message": "Purchase deleted successfully"}), 200

    @app.route('/api/print-data', methods=['POST'])
    @role_required(['user', 'editor', 'admin'])  # Editor and admin can print data
    def print_data():
        data = request.json
        title = 'NEW WAY'
        subtitle = data.get('subtitle', '')
        headers = data.get('headers', [])
        rows = data.get('rows', [])

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.fontSize = 18
        title_style.fontName = 'Helvetica-Bold'
        title_paragraph = Paragraph(title, title_style)
        subtitle_paragraph = Paragraph(subtitle, styles['Heading2'])
        elements.append(title_paragraph)
        elements.append(subtitle_paragraph)

        table_data = [headers] + rows
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)

        return send_file(buffer, download_name='data_summary.pdf', as_attachment=True)

    @app.route('/api/user-details', methods=['GET'])
    @jwt_required()
    def get_user_details():
        user = get_jwt()
        user_record = User.query.filter_by(username=user['username']).first()
        if not user_record:
            return jsonify({"message": "User not found"}), 404
        return jsonify({
            "id": user_record.id,
            "username": user_record.username,
            "first_name": user_record.first_name,
            "last_name": user_record.last_name,
            "role": user_record.role
        }), 200
    
    @app.route('/api/reset-password', methods=['POST'])
    @jwt_required()
    def reset_password():
        data = request.get_json()
        user = get_jwt_identity()
        user_record = User.query.filter_by(id=user['id']).first()
        if not user_record:
            return jsonify({"message": "User not found"}), 404

        new_password = data.get('new_password')
        if not new_password or len(new_password) < 6:
            return jsonify({"message": "Password must be at least 6 characters long"}), 400

        user_record.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        return jsonify({"message": "Password reset successfully"}), 200

    @app.route('/api/customer-rates/<int:customer_id>', methods=['GET'])
    @role_required(['accountant'])
    def get_customer_rates(customer_id):
        rates = CustomerRate.query.filter_by(customer_id=customer_id).all()
        return jsonify([rate.to_dict() for rate in rates])

    @app.route('/api/customer-rates', methods=['POST'])
    @role_required(['accountant'])
    def save_customer_rates():
        data = request.get_json()
        customer_id = data.get('customer_id')
        rates_data = data.get('rates', [])
        
        if not customer_id:
            return jsonify({'error': 'Customer ID is required'}), 400
        
        # Check if customer exists
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        try:
            for rate_data in rates_data:
                plate_size_id = rate_data.get('plate_size_id')
                plate_rate_value = rate_data.get('plate_rate', 0)
                baking_rate_value = rate_data.get('baking_rate', 0)
                
                # Try to find existing rate
                existing_rate = CustomerRate.query.filter_by(
                    customer_id=customer_id,
                    plate_size_id=plate_size_id
                ).first()
                
                if existing_rate:
                    existing_rate.plate_rate = plate_rate_value
                    existing_rate.baking_rate = baking_rate_value
                else:
                    new_rate = CustomerRate(
                        customer_id=customer_id,
                        plate_size_id=plate_size_id,
                        plate_rate=plate_rate_value,
                        baking_rate=baking_rate_value
                    )
                    db.session.add(new_rate)
            
            db.session.commit()
            return jsonify({'message': 'Rates saved successfully'})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error saving rates: {str(e)}'}), 500

    @app.route('/api/challans', methods=['GET', 'POST'])
    @jwt_required()
    def manage_challans():
        if request.method == 'POST':
            data = request.get_json()
            new_challan = Challan(
                challan_code=data['challan_code'],
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                customer_id=data['customer_id'],
                special_instructions=data.get('special_instructions', ''),
                printed=False  # Initialize as not printed
            )
            db.session.add(new_challan)
            db.session.flush()  # Flush to get the challan ID

            # Add jobs directly to the challan
            for job_data in data['jobs']:
                new_job = Job(
                    job_name=job_data['job_name'],
                    challan_id=new_challan.id,
                    plate_size_id=job_data['plate_size_id'],
                    colour=job_data['colour'],
                    job_id=job_data['job_id'],
                    quantity=job_data['quantity'],
                    plates=job_data['plates'],
                    remark=job_data['remark']
                )
                db.session.add(new_job)

            db.session.commit()
            return jsonify(new_challan.serialize()), 201

        # Handle GET request with pagination and filters
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            
            # Filter parameters
            challan_code = request.args.get('challan_code')
            date = request.args.get('date')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            customer_id = request.args.get('customer_id', type=int)
            printed = request.args.get('printed')

            # Build query
            query = Challan.query

            if challan_code:
                query = query.filter(Challan.challan_code.ilike(f'%{challan_code}%'))
            
            # Handle single date or date range
            if date:
                query = query.filter(Challan.date == datetime.strptime(date, '%Y-%m-%d').date())
            elif start_date and end_date:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Challan.date.between(start, end))
            
            if customer_id:
                query = query.filter(Challan.customer_id == customer_id)
            if printed is not None:
                # Convert string 'true'/'false' to boolean
                is_printed = printed.lower() == 'true'
                query = query.filter(Challan.printed == is_printed)

            # Order by challan_code descending
            query = query.order_by(Challan.challan_code.desc())
            
            # Paginate
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            # Format response
            challans = [challan.serialize() for challan in pagination.items]
            
            return jsonify({
                'challans': challans,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next,
                    'prev_num': pagination.prev_num,
                    'next_num': pagination.next_num
                }
            }), 200
            
        except Exception as e:
            print(f"Error fetching challans: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # New endpoint to mark a challan as printed
    @app.route('/api/challans/<int:id>/mark-printed', methods=['PUT'])
    @jwt_required()
    def mark_challan_printed(id):
        challan = Challan.query.get_or_404(id)
        challan.printed = True
        db.session.commit()
        return jsonify({"message": "Challan marked as printed", "challan": challan.serialize()}), 200

    # You could also add an endpoint to mark as not printed (if needed)
    @app.route('/api/challans/<int:id>/mark-not-printed', methods=['PUT'])
    @jwt_required()
    def mark_challan_not_printed(id):
        challan = Challan.query.get_or_404(id)
        challan.printed = False
        db.session.commit()
        return jsonify({"message": "Challan marked as not printed", "challan": challan.serialize()}), 200

    @app.route('/api/challans/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def manage_single_challan(id):
        challan = Challan.query.get_or_404(id)

        if request.method == 'GET':
            return jsonify(challan.serialize()), 200

        if request.method == 'PUT':
            data = request.get_json()
            challan.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            challan.customer_id = data['customer_id']
            challan.special_instructions = data.get('special_instructions', '')  # Update special instructions

            # Update jobs
            Job.query.filter_by(challan_id=id).delete()  # Remove existing jobs
            for job_data in data['jobs']:
                new_job = Job(
                    job_name=job_data['job_name'],
                    challan_id=id,
                    plate_size_id=job_data['plate_size_id'],
                    colour=job_data['colour'],
                    job_id=job_data['job_id'],
                    quantity=job_data['quantity'],
                    plates=job_data['plates'],
                    remark=job_data['remark']
                )
                db.session.add(new_job)

            db.session.commit()
            return jsonify(challan.serialize()), 200

        if request.method == 'DELETE':
            Job.query.filter_by(challan_id=id).delete()  # Remove associated jobs
            db.session.delete(challan)
            db.session.commit()
            return jsonify({"message": "Challan deleted successfully"}), 200

    @app.route('/api/challan-code', methods=['GET'])
    @jwt_required()
    def generate_challan_code():
        try:
            # Get the latest challan code from the database
            latest_challan = Challan.query.order_by(Challan.id.desc()).first()
            
            if latest_challan:
                # Extract number from the latest challan code
                latest_code = latest_challan.challan_code
                if '-' in latest_code:
                    prefix, number_str = latest_code.split('-', 1)
                    try:
                        number = int(number_str) + 1
                    except ValueError:
                        number = 1
                else:
                    try:
                        number = int(latest_code) + 1
                    except ValueError:
                        number = 1
            else:
                number = 1
            
            # Return without zero padding - just the raw number
            new_challan_code = f"DC-{number}"
            
            return jsonify({'challan_code': new_challan_code}), 200
            
        except Exception as e:
            print(f"Error generating challan code: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/used-plates', methods=['GET'])
    @jwt_required()
    def get_used_plates():
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({"message": "Start date and end date are required"}), 400

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

        query = text("""
            SELECT
            ps.length || ' x ' || ps.width || CASE WHEN ps.is_dl THEN ' - DL' ELSE '' END AS size,
            SUM(j.quantity * j.colour) AS total_used,
            DATE(c.date) AS challan_date
            FROM
            job j
            JOIN
            plate_size ps ON j.plate_size_id = ps.id
            JOIN
            challan c ON j.challan_id = c.id
            WHERE
            c.date BETWEEN :start_date AND :end_date
            GROUP BY
            ps.length, ps.width, ps.is_dl, c.date
            ORDER BY
            c.date;
        """)

        result = db.session.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()

        used_plates = [
            {
                "item": row[0],
                "quantity": row[1],
                "date": row[2]  # No need for isoformat as it's already a string
            }
            for row in result
        ]

        return jsonify(used_plates), 200

    @app.route('/api/invoices', methods=['GET', 'POST'])
    @role_required(['accountant'])
    def manage_invoices():
        if request.method == 'POST':
            data = request.get_json()
            
            # Check if invoice number already exists
            existing_invoice = Invoice.query.filter_by(invoice_number=data['invoice_number']).first()
            if existing_invoice:
                return jsonify({
                    'error': f'Invoice number {data["invoice_number"]} already exists',
                    'existing_invoice': {
                        'id': existing_invoice.id,
                        'customer_name': existing_invoice.customer.company_name,
                        'invoice_date': existing_invoice.invoice_date.isoformat(),
                        'grand_total': existing_invoice.grand_total
                    }
                }), 409  # 409 Conflict status code
        
            # Parse financial year and sequence from invoice_number (format: 2526/GST/34)
            invoice_parts = data['invoice_number'].split('/')
            financial_year = invoice_parts[0]
            invoice_sequence = int(invoice_parts[2])
            
            # Create new invoice
            new_invoice = Invoice(
                invoice_number=data['invoice_number'],
                financial_year=financial_year,
                invoice_sequence=invoice_sequence,
                invoice_date=datetime.strptime(data['invoice_date'], '%Y-%m-%d').date(),
                due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
                customer_id=data['customer_id'],
                total_amount=data['total_amount'],
                cgst_amount=data.get('cgst_amount', 0),
                sgst_amount=data.get('sgst_amount', 0),
                igst_amount=data.get('igst_amount', 0),
                grand_total=data['grand_total'],
                challan_references=data.get('challan_references', ''),
                status=data.get('status', 'unpaid'),
                summary_start_date=datetime.strptime(data.get('summary_start_date'), '%Y-%m-%d').date() if data.get('summary_start_date') else None,
                summary_end_date=datetime.strptime(data.get('summary_end_date'), '%Y-%m-%d').date() if data.get('summary_end_date') else None
            )
            
            db.session.add(new_invoice)
            db.session.flush()  # Get the invoice ID
            
            # Add invoice items
            for item_data in data['items']:
                # Extract unique challan numbers from the jobs array
                challan_numbers = list(set(job['challan_no'] for job in item_data.get('jobs', [])))
                
                new_item = InvoiceItem(
                    invoice_id=new_invoice.id,
                    plate_size_id=item_data['plate_size_id'],
                    description=item_data.get('description', ''),
                    colours=item_data['colours'],
                    quantity=item_data['quantity'],
                    rate=item_data['rate'],
                    amount=item_data['amount'],
                    job_ids=','.join(map(str, challan_numbers))  # Store challan numbers instead of job IDs
                )
                db.session.add(new_item)
        
            db.session.commit()
            return jsonify(new_invoice.serialize()), 201
        
        # Handle GET with filters and pagination
        invoice_number = request.args.get('invoice_number')
        customer_id = request.args.get('customer_id')
        invoice_date = request.args.get('date')
        status = request.args.get('status')
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 50)  # Max 50 per page
        
        # print(f"DEBUG: Filtering invoices - invoice_number={invoice_number}, customer_id={customer_id}, date={invoice_date}, status={status}, page={page}, per_page={per_page}")
        
        query = Invoice.query
        
        if invoice_number:
            # Use simple substring matching without case sensitivity
            query = query.filter(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
            # print(f"DEBUG: Applied invoice number filter: {invoice_number}")
        
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        
        if invoice_date:
            try:
                date_obj = datetime.strptime(invoice_date, '%Y-%m-%d').date()
                query = query.filter(Invoice.invoice_date == date_obj)
                # print(f"DEBUG: Applied date filter: {date_obj}")
            except ValueError as e:
                print(f"DEBUG: Invalid date format: {invoice_date}, error: {str(e)}")
        
        if status:
            query = query.filter(Invoice.status == status)
        
        # Order by newest first (financial year desc, sequence desc, then by date desc)
        query = query.order_by(
            Invoice.financial_year.desc(),
            Invoice.invoice_sequence.desc(),
            Invoice.invoice_date.desc()
        )
        
        # Apply pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'invoices': [invoice.serialize() for invoice in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        }), 200

    @app.route('/api/invoices/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @role_required(['accountant', 'admin'])
    def manage_single_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        
        if request.method == 'GET':
            return jsonify(invoice.serialize()), 200
        
        if request.method == 'PUT':
            data = request.get_json()
            
            # Update invoice details
            invoice.invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
            invoice.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            invoice.total_amount = data['total_amount']
            invoice.cgst_amount = data.get('cgst_amount', 0)
            invoice.sgst_amount = data.get('sgst_amount', 0)
            invoice.igst_amount = data.get('igst_amount', 0)
            invoice.grand_total = data['grand_total']
            invoice.challan_references = data.get('challan_references', '')
            invoice.status = data.get('status', 'unpaid')
            
            if data.get('status') == 'paid' and invoice.status != 'paid':
                invoice.payment_date = datetime.now().date()
            
            # Delete existing items
            InvoiceItem.query.filter_by(invoice_id=id).delete()
            
            # Add updated items
            for item_data in data['items']:
                new_item = InvoiceItem(
                    invoice_id=invoice.id,
                    plate_size_id=item_data['plate_size_id'],
                    description=item_data.get('description', ''),
                    colours=item_data['colours'],
                    quantity=item_data['quantity'],
                    rate=item_data['rate'],
                    amount=item_data['amount'],
                    job_ids=','.join(map(str, item_data.get('job_ids', [])))
                )
                db.session.add(new_item)
            
            db.session.commit()
            return jsonify(invoice.serialize()), 200
        
        if request.method == 'DELETE':
            # First delete all related invoice items
            InvoiceItem.query.filter_by(invoice_id=id).delete()
            # Then delete the invoice
            db.session.delete(invoice)
            db.session.commit()
            return jsonify({"message": "Invoice deleted successfully"}), 200

    @app.route('/api/invoices/<int:id>/status', methods=['PATCH'])
    @role_required(['accountant', 'admin'])
    def update_invoice_status(id):
        invoice = Invoice.query.get_or_404(id)
        data = request.get_json()
        
        if 'status' in data:
            invoice.status = data['status']
            
            # Update payment date if marked as paid
            if data['status'] == 'paid' and invoice.status != 'paid':
                invoice.payment_date = datetime.now().date()
                
            db.session.commit()
            return jsonify(invoice.serialize()), 200
        
        return jsonify({"error": "Status field is required"}), 400

    @app.route('/api/invoice-number', methods=['GET'])
    @role_required(['accountant', 'admin'])
    def generate_invoice_number():
        current_year = datetime.now().year
        # Find the highest invoice number for the current year
        highest_invoice = Invoice.query.filter(
            Invoice.invoice_number.like(f'INV-{current_year}-%')
        ).order_by(Invoice.invoice_number.desc()).first()
        
        if highest_invoice:
            # Extract the numeric part and increment
            last_num = int(highest_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            # Start with 0001 if no invoices for this year
            new_num = 1
        
        new_invoice_number = f"INV-{current_year}-{new_num:04d}"
        return jsonify({"invoice_number": new_invoice_number}), 200

    @app.route('/api/invoices/latest', methods=['GET'])
    @role_required(['accountant', 'admin'])
    def get_latest_invoice():
        """Get the latest invoice by financial year and sequence"""
        # Determine current financial year
        today = datetime.now()
        if today.month >= 4:  # April or later
            current_fy_start = today.year
            current_fy_end = today.year + 1
        else:
            current_fy_start = today.year - 1
            current_fy_end = today.year
            
        current_fy = f"{str(current_fy_start)[-2:]}{str(current_fy_end)[-2:]}"
        
        # First try to get the latest invoice from the current financial year
        latest_invoice = Invoice.query.filter_by(financial_year=current_fy).order_by(Invoice.invoice_sequence.desc()).first()
        
        # If no invoice found for current FY, get the latest from any FY
        if not latest_invoice:
            latest_invoice = Invoice.query.order_by(
                Invoice.financial_year.desc(),
                Invoice.invoice_sequence.desc()
            ).first()
        
        if latest_invoice:
            return jsonify(latest_invoice.serialize()), 200
        return jsonify({
            "financial_year": current_fy,
            "invoice_sequence": 0,
            "invoice_number": f"{current_fy}/GST/00"
        }), 200

    @app.route('/api/send-invoice-email', methods=['POST'])
    @jwt_required()
    def send_invoice_email():
        try:
            # print("DEBUG: Starting send_invoice_email function")
            
            # Get form data
            invoice_id = request.form.get('invoice_id')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message_text = request.form.get('message')
            pdf_file = request.files.get('pdf')
            summary_pdf_file = request.files.get('summary_pdf')  # <-- Add this line

            if not all([invoice_id, email, subject]):
                return jsonify({'error': 'Missing required fields'}), 400

            # Handle multiple email addresses
            email_list = []
            if isinstance(email, list):
                email_list.extend([e.strip() for e in email if e.strip()])
            elif isinstance(email, str):
                email_list.extend([e.strip() for e in email.split(',') if e.strip()])

            if not email_list:
                return jsonify({'error': 'No valid email addresses found'}), 400

            try:
                # Create email
                msg = Message(
                    subject=subject,
                    recipients=email_list,
                    body=message_text
                )

                # Attach invoice PDF if provided
                if pdf_file:
                    msg.attach(
                        filename='invoice.pdf',
                        content_type='application/pdf',
                        data=pdf_file.read()
                    )

                # Attach summary PDF if provided
                if summary_pdf_file:
                    msg.attach(
                        filename='customer_summary.pdf',
                        content_type='application/pdf',
                        data=summary_pdf_file.read()
                    )

                mail.send(msg)
                return jsonify({'message': 'Email sent successfully'})

            except Exception as email_error:
                return jsonify({'error': f'Failed to send email: {str(email_error)}'}), 500

        except Exception as e:
            print(f"Unexpected Error: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    @app.route('/api/invoices/check-number/<invoice_number>', methods=['GET'])
    @role_required(['accountant', 'admin'])
    def check_invoice_number_exists(invoice_number):
        """Check if an invoice with the given number already exists"""
        existing_invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
        
        if existing_invoice:
            return jsonify({
                'exists': True,
                'invoice_id': existing_invoice.id,
                'invoice_number': existing_invoice.invoice_number,
                'customer_name': existing_invoice.customer.company_name,
                'invoice_date': existing_invoice.invoice_date.isoformat(),
                'grand_total': existing_invoice.grand_total
            }), 200
        else:
            return jsonify({'exists': False}), 404

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # Dynamically locate the dist folder relative to the executable
        if getattr(sys, 'frozen', False):  # Check if running as a PyInstaller executable
            dist_folder = os.path.join(sys._MEIPASS, 'dist')
        else:
            dist_folder = os.path.join(os.path.dirname(__file__), '..', 'dist')

        # print(f"Dist folder path: {dist_folder}")  # Debugging: Print the dist folder path
        if path != "" and os.path.exists(os.path.join(dist_folder, path)):
            return send_from_directory(dist_folder, path)
        else:
            return send_from_directory(dist_folder, 'index.html')