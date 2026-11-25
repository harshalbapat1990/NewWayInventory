"""Challan and plate usage API routes."""
from datetime import date, datetime

from flask import jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from . import db
from .audit import record_audit_event
from .models import Challan, Customer, Job, PlateSize


def register_challan_routes(app, role_required, require_current_role, reserve_document_sequences):
    def validate_challan_payload(data):
        if not isinstance(data, dict):
            return None, 'Challan data must be an object'
        code = data.get('challan_code')
        parts = code.split('/') if isinstance(code, str) else []
        if (len(parts) != 3 or len(code) > 100 or len(parts[0]) != 4 or not parts[0].isdigit()
                or parts[1] != 'DC' or not parts[2].isdigit() or int(parts[2]) < 1):
            return None, 'Challan code must use FY/DC/SEQUENCE format'
        try:
            customer_id = int(data.get('customer_id'))
            challan_date = date.fromisoformat(data.get('date'))
            if customer_id < 1 or isinstance(data.get('customer_id'), bool):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            return None, 'Customer ID or challan date is invalid'
        jobs = data.get('jobs')
        if not isinstance(jobs, list) or not 1 <= len(jobs) <= 500:
            return None, 'Challan must contain between 1 and 500 jobs'
        normalized_jobs = []
        try:
            for job in jobs:
                if not isinstance(job, dict):
                    return None, 'Each challan job must be an object'
                size_id = int(job.get('plate_size_id'))
                colour = int(job.get('colour'))
                quantity = int(job.get('quantity'))
                plates = int(job.get('plates'))
                name, job_id = job.get('job_name'), job.get('job_id')
                remark = job.get('remark', '') or ''
                if (min(size_id, colour, quantity, plates) < 1 or max(quantity, plates) > 10000000
                        or any(isinstance(job.get(key), bool) for key in ('plate_size_id', 'colour', 'quantity', 'plates'))
                        or not isinstance(name, str) or not name.strip() or len(name) > 100
                        or not isinstance(job_id, str) or not job_id.strip() or len(job_id) > 100
                        or not isinstance(remark, str) or len(remark) > 200):
                    return None, 'Challan job fields are invalid'
                normalized_jobs.append({
                    **job, 'plate_size_id': size_id, 'colour': colour, 'quantity': quantity,
                    'plates': plates, 'job_name': name.strip(), 'job_id': job_id.strip(), 'remark': remark,
                })
        except (TypeError, ValueError, OverflowError):
            return None, 'Challan job fields are invalid'
        size_ids = {job['plate_size_id'] for job in normalized_jobs}
        existing_size_ids = {row[0] for row in db.session.query(PlateSize.id).filter(PlateSize.id.in_(size_ids)).all()}
        if existing_size_ids != size_ids:
            return None, 'One or more challan plate sizes do not exist'
        instructions = data.get('special_instructions', '') or ''
        if not isinstance(instructions, str) or len(instructions) > 4000:
            return None, 'Special instructions are too long'
        return {
            **data, 'customer_id': customer_id, 'date': challan_date.isoformat(),
            'jobs': normalized_jobs, 'special_instructions': instructions,
            'financial_year': parts[0], 'challan_sequence': int(parts[2]),
        }, None

    @app.route('/api/challans', methods=['GET', 'POST'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def manage_challans():
        if request.method == 'POST':
            if not require_current_role('user', 'editor', 'admin'):
                return jsonify({"message": "Access denied"}), 403
            data, error = validate_challan_payload(request.get_json(silent=True))
            if error:
                return jsonify({'message': error}), 400
            customer = Customer.query.get_or_404(data.get('customer_id'))
            if customer.is_archived:
                return jsonify({"message": "Archived clients cannot be assigned to new challans."}), 400
            new_challan = Challan(
                challan_code=data['challan_code'],
                financial_year=data['financial_year'],
                challan_sequence=data['challan_sequence'],
                date=date.fromisoformat(data['date']),
                customer_id=data['customer_id'],
                special_instructions=data.get('special_instructions', ''),
                printed=False  # Initialize as not printed
            )
            db.session.add(new_challan)
            try:
                db.session.flush()  # Flush to get the challan ID
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'That challan number is already in use. Request a new number.'}), 409

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

            try:
                record_audit_event('challan.created', 'challan', new_challan.id)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'That challan number is already in use. Request a new number.'}), 409
            return jsonify(new_challan.serialize()), 201

        # Handle GET request with pagination and filters
        try:
            # Pagination parameters
            per_page = min(max(request.args.get('per_page', 50, type=int) or 50, 1), 100)
            page = max(request.args.get('page', 1, type=int) or 1, 1)
            
            # Filter parameters
            challan_code = request.args.get('challan_code')
            date = request.args.get('date')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            customer_id = request.args.get('customer_id', type=int)
            printed = request.args.get('printed')
            financial_year = request.args.get('financial_year')
            archived = request.args.get('archived', 'false')

            # Build query
            query = Challan.query

            # archived=all → no filter; archived=true → only archived; default → only active
            if archived.lower() == 'all':
                pass  # return both archived and non-archived
            elif archived.lower() == 'true':
                query = query.filter(Challan.is_archived == True)
            else:
                query = query.filter(Challan.is_archived == False)

            if financial_year:
                query = query.filter(Challan.financial_year == financial_year)

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
            query = query.order_by(Challan.id.desc())
            
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
            app.logger.exception('Challan lookup failed')
            return jsonify({'error': 'Unable to fetch challans'}), 500

    # New endpoint to mark a challan as printed
    @app.route('/api/challans/<int:id>/mark-printed', methods=['PUT'])
    @role_required(['editor', 'admin'])
    def mark_challan_printed(id):
        challan = Challan.query.get_or_404(id)
        challan.printed = True
        record_audit_event('challan.printed', 'challan', challan.id)
        db.session.commit()
        return jsonify({"message": "Challan marked as printed", "challan": challan.serialize()}), 200

    # You could also add an endpoint to mark as not printed (if needed)
    @app.route('/api/challans/<int:id>/mark-not-printed', methods=['PUT'])
    @role_required(['editor', 'admin'])
    def mark_challan_not_printed(id):
        challan = Challan.query.get_or_404(id)
        challan.printed = False
        record_audit_event('challan.unprinted', 'challan', challan.id)
        db.session.commit()
        return jsonify({"message": "Challan marked as not printed", "challan": challan.serialize()}), 200

    @app.route('/api/challans/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def manage_single_challan(id):
        challan = Challan.query.get_or_404(id)

        if request.method == 'GET':
            return jsonify(challan.serialize()), 200

        if request.method == 'PUT':
            if not require_current_role('editor', 'admin'):
                return jsonify({"message": "Access denied"}), 403
            data, error = validate_challan_payload(request.get_json(silent=True))
            if error:
                return jsonify({'message': error}), 400
            selected_customer = Customer.query.get_or_404(data.get('customer_id'))
            if selected_customer.is_archived and selected_customer.id != challan.customer_id:
                return jsonify({"message": "Archived clients cannot be newly assigned to a challan."}), 400
            challan.date = date.fromisoformat(data['date'])
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

            record_audit_event('challan.updated', 'challan', challan.id)
            db.session.commit()
            return jsonify(challan.serialize()), 200

        if request.method == 'DELETE':
            if not require_current_role('admin'):
                return jsonify({"message": "Access denied"}), 403
            Job.query.filter_by(challan_id=id).delete()  # Remove associated jobs
            record_audit_event('challan.deleted', 'challan', challan.id)
            db.session.delete(challan)
            db.session.commit()
            return jsonify({"message": "Challan deleted successfully"}), 200

    @app.route('/api/challan-code', methods=['GET'])
    @role_required(['user', 'editor', 'admin'])
    def generate_challan_code():
        try:
            # Determine current financial year
            today = datetime.now()
            fy_start = today.year if today.month >= 4 else today.year - 1
            current_fy = f"{str(fy_start)[-2:]}{str(fy_start + 1)[-2:]}"

            next_seq = reserve_document_sequences(
                'challan', current_fy, 1,
                'SELECT COALESCE(MAX(challan_sequence), 0) FROM challan WHERE financial_year=:period'
            )[0]

            new_challan_code = f"{current_fy}/DC/{next_seq}"
            return jsonify({'challan_code': new_challan_code}), 200

        except Exception as e:
            app.logger.exception('Challan code generation failed')
            return jsonify({'error': 'Unable to generate challan code'}), 500

    @app.route('/api/used-plates', methods=['GET'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
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
              ps.id AS size_id,
              COALESCE(ps.prefix || ' ', '') ||
              ps.length || ' x ' || ps.width ||
              CASE WHEN ps.is_dl THEN ' - DL' ELSE '' END ||
              COALESCE(' ' || ps.suffix, '') AS size_label,
              SUM(j.quantity * j.colour) AS total_used,
              DATE(c.date) AS challan_date
            FROM job j
            JOIN plate_size ps ON j.plate_size_id = ps.id
            JOIN challan c ON j.challan_id = c.id
            WHERE c.date BETWEEN :start_date AND :end_date
            GROUP BY ps.id, c.date
            ORDER BY c.date;
        """)

        result = db.session.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()

        used_plates = [
            {
                "size_id": row[0],
                "item": row[1],           # size_label (prefix + "L x W" + DL + suffix)
                "quantity": row[2],
                "date": row[3]
            }
            for row in result
        ]

        return jsonify(used_plates), 200

    # -------------------------------------------------------------------------
    # Archive routes
    # -------------------------------------------------------------------------

    def _fy_date_range(fy):
        """Return (start_date, end_date) for a financial year string like '2526'."""
        from datetime import date
        fy_start_year = 2000 + int(fy[:2])
        return date(fy_start_year, 4, 1), date(fy_start_year + 1, 3, 31)

