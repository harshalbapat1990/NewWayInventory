"""Invoice API routes and challan relationships."""
from datetime import date, datetime

from flask import jsonify, request
from flask_mail import Message
from sqlalchemy.exc import IntegrityError

from . import db
from .audit import record_audit_event
from .models import Challan, Customer, Invoice, InvoiceItem, PlateSize, _money_cents, invoice_item_challan


def register_invoice_routes(app, role_required, require_current_role, reserve_document_sequences, limiter, mail, smtp_credentials):
    def validate_invoice_payload(data, require_number=False):
        if not isinstance(data, dict):
            return None, 'Invoice data must be an object'
        invoice_number = data.get('invoice_number')
        if require_number:
            parts = invoice_number.split('/') if isinstance(invoice_number, str) else []
            if (len(parts) != 3 or len(invoice_number) > 50 or len(parts[0]) != 4
                    or not parts[0].isdigit() or not parts[2].isdigit() or int(parts[2]) < 1):
                return None, 'Invoice number must use FY/CODE/SEQUENCE format'
        normalized_customer_id = None
        if require_number or 'customer_id' in data:
            try:
                normalized_customer_id = int(data.get('customer_id'))
                if isinstance(data.get('customer_id'), bool) or normalized_customer_id < 1:
                    raise ValueError
            except (TypeError, ValueError, OverflowError):
                return None, 'Customer ID is invalid'
        dates = {}
        for field in ('invoice_date', 'due_date'):
            value = data.get(field)
            try:
                dates[field] = date.fromisoformat(value) if isinstance(value, str) else None
            except ValueError:
                dates[field] = None
            if dates[field] is None:
                return None, f'{field} must use YYYY-MM-DD format'
        if dates['due_date'] < dates['invoice_date']:
            return None, 'Due date cannot be before invoice date'
        for field in ('summary_start_date', 'summary_end_date'):
            value = data.get(field)
            if value is None or value == '':
                dates[field] = None
                continue
            try:
                dates[field] = date.fromisoformat(value) if isinstance(value, str) else None
            except ValueError:
                dates[field] = None
            if dates[field] is None:
                return None, f'{field} must use YYYY-MM-DD format'
        if dates['summary_start_date'] and dates['summary_end_date'] and dates['summary_end_date'] < dates['summary_start_date']:
            return None, 'Summary end date cannot be before its start date'
        status = data.get('status', 'unpaid')
        if status not in ('unpaid', 'paid', 'cancelled'):
            return None, 'Invoice status is invalid'
        try:
            for field in ('total_amount', 'grand_total'):
                _money_cents(data[field])
            for field in ('cgst_amount', 'sgst_amount', 'igst_amount'):
                _money_cents(data.get(field, 0))
        except (KeyError, TypeError, ValueError):
            return None, 'Invoice totals must be valid monetary values'
        items = data.get('items')
        if not isinstance(items, list) or not 1 <= len(items) <= 500:
            return None, 'Invoice must contain between 1 and 500 items'
        normalized_items = []
        try:
            for item in items:
                if not isinstance(item, dict):
                    return None, 'Each invoice item must be an object'
                plate_size_id = int(item.get('plate_size_id'))
                quantity = int(item.get('quantity'))
                if plate_size_id < 1 or quantity < 1 or quantity > 10000000:
                    return None, 'Invoice item size and quantity are invalid'
                if isinstance(item.get('quantity'), bool) or isinstance(item.get('plate_size_id'), bool):
                    return None, 'Invoice item size and quantity are invalid'
                if item.get('colours') is None or len(str(item['colours'])) > 50:
                    return None, 'Invoice item colours are invalid'
                _money_cents(item['rate'])
                _money_cents(item['amount'])
                jobs = item.get('jobs', [])
                challan_ids = item.get('challan_ids', [])
                if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
                    return None, 'Invoice item job references are invalid'
                if any('challan_no' not in job for job in jobs):
                    return None, 'Invoice item jobs must include their challan reference'
                if not isinstance(challan_ids, list):
                    return None, 'Invoice item challan references are invalid'
                if any(isinstance(value, bool) or not str(value).isdigit() or int(value) < 1 for value in challan_ids):
                    return None, 'Invoice item challan IDs are invalid'
                normalized_jobs = []
                for job in jobs:
                    ref = job.get('challan_no')
                    if (not isinstance(ref, (str, int)) or isinstance(ref, bool)
                            or len(str(ref)) > 100 or not str(ref).strip()):
                        return None, 'Invoice item challan reference is invalid'
                    challan_id = job.get('challan_id')
                    if challan_id is not None:
                        if isinstance(challan_id, bool) or not str(challan_id).isdigit() or int(challan_id) < 1:
                            return None, 'Invoice item challan ID is invalid'
                        challan_id = int(challan_id)
                    normalized_jobs.append({**job, 'challan_id': challan_id})
                description = item.get('description', '')
                if not isinstance(description, str) or len(description) > 200:
                    return None, 'Invoice item description is invalid'
                normalized_items.append({
                    **item,
                    'plate_size_id': plate_size_id,
                    'quantity': quantity,
                    'colours': str(item['colours']),
                    'description': description,
                    'jobs': normalized_jobs,
                    'challan_ids': [int(value) for value in challan_ids],
                })
        except (KeyError, TypeError, ValueError, OverflowError):
            return None, 'Invoice items contain invalid values'
        size_ids = {item['plate_size_id'] for item in normalized_items}
        existing_size_ids = {row[0] for row in db.session.query(PlateSize.id).filter(PlateSize.id.in_(size_ids)).all()}
        if existing_size_ids != size_ids:
            return None, 'One or more invoice plate sizes do not exist'
        normalized = {**data, 'status': status, 'items': normalized_items, **dates}
        if normalized_customer_id is not None:
            normalized['customer_id'] = normalized_customer_id
        return normalized, None

    def attach_invoice_item_challans(item, jobs, legacy_refs, customer_id, financial_year, explicit_ids=None, start_date=None, end_date=None):
        challan_ids = {job.get('challan_id') for job in jobs or [] if isinstance(job, dict) and job.get('challan_id')}
        challan_ids.update(explicit_ids or [])
        resolved = Challan.query.filter(
            Challan.id.in_(challan_ids), Challan.customer_id == customer_id
        ).all() if challan_ids else []
        found_ids = {challan.id for challan in resolved}
        for token in legacy_refs or []:
            try:
                sequence = int(token)
            except (TypeError, ValueError):
                continue
            if not start_date or not end_date:
                continue
            matches = Challan.query.filter(
                Challan.customer_id == customer_id,
                Challan.challan_sequence == sequence,
                Challan.date.between(start_date, end_date)
            ).all()
            if len(matches) == 1:
                found_ids.add(matches[0].id)
        if found_ids:
            item.challans = Challan.query.filter(Challan.id.in_(found_ids), Challan.customer_id == customer_id).all()

    @app.route('/api/invoices', methods=['GET', 'POST'])
    @role_required(['accountant', 'admin'])
    def manage_invoices():
        if request.method == 'POST':
            data, error = validate_invoice_payload(request.get_json(silent=True), require_number=True)
            if error:
                return jsonify({'message': error}), 400
            customer = Customer.query.get_or_404(data.get('customer_id'))
            if customer.is_archived:
                return jsonify({"message": "Archived clients cannot be assigned to new invoices."}), 400
            referenced_ids = {value for item in data['items'] for value in item['challan_ids']}
            referenced_ids.update(job['challan_id'] for item in data['items'] for job in item['jobs'] if job['challan_id'])
            if referenced_ids and Challan.query.filter(Challan.id.in_(referenced_ids), Challan.customer_id == customer.id).count() != len(referenced_ids):
                return jsonify({'message': 'Invoice challan references must belong to its client'}), 400
            
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
                invoice_date=data['invoice_date'],
                due_date=data['due_date'],
                customer_id=data['customer_id'],
                total_amount=data['total_amount'],
                cgst_amount=data.get('cgst_amount', 0),
                sgst_amount=data.get('sgst_amount', 0),
                igst_amount=data.get('igst_amount', 0),
                grand_total=data['grand_total'],
                challan_references=data.get('challan_references', ''),
                status=data.get('status', 'unpaid'),
                payment_date=datetime.now().date() if data.get('status', 'unpaid') == 'paid' else None,
                summary_start_date=data['summary_start_date'],
                summary_end_date=data['summary_end_date']
            )
            
            db.session.add(new_invoice)
            try:
                db.session.flush()  # Get the invoice ID
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'That invoice number is already in use. Reserve a new number.'}), 409
            
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
                attach_invoice_item_challans(
                    new_item, item_data.get('jobs'), challan_numbers,
                    new_invoice.customer_id, new_invoice.financial_year,
                    explicit_ids=item_data.get('challan_ids'),
                    start_date=new_invoice.summary_start_date, end_date=new_invoice.summary_end_date
                )
                db.session.add(new_item)
        
            try:
                record_audit_event('invoice.created', 'invoice', new_invoice.id)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'That invoice number is already in use. Reserve a new number.'}), 409
            return jsonify(new_invoice.serialize()), 201
        
        # Handle GET with filters and pagination
        invoice_number = request.args.get('invoice_number')
        customer_id = request.args.get('customer_id')
        invoice_date = request.args.get('date')
        status = request.args.get('status')
        
        # Pagination parameters
        page = max(request.args.get('page', 1, type=int) or 1, 1)
        per_page = min(max(request.args.get('per_page', 50, type=int) or 50, 1), 100)
        
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
                app.logger.info('Invoice query rejected an invalid date')
        
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
            data, error = validate_invoice_payload(request.get_json(silent=True))
            if error:
                return jsonify({'message': error}), 400
            selected_customer = Customer.query.get_or_404(data.get('customer_id', invoice.customer_id))
            if selected_customer.is_archived and selected_customer.id != invoice.customer_id:
                return jsonify({"message": "Archived clients cannot be newly assigned to an invoice."}), 400
            referenced_ids = {value for item in data['items'] for value in item['challan_ids']}
            referenced_ids.update(job['challan_id'] for item in data['items'] for job in item['jobs'] if job['challan_id'])
            if referenced_ids and Challan.query.filter(Challan.id.in_(referenced_ids), Challan.customer_id == selected_customer.id).count() != len(referenced_ids):
                return jsonify({'message': 'Invoice challan references must belong to its client'}), 400
            
            # Update invoice details
            invoice.invoice_date = data['invoice_date']
            invoice.due_date = data['due_date']
            invoice.customer_id = selected_customer.id
            invoice.total_amount = data['total_amount']
            invoice.cgst_amount = data.get('cgst_amount', 0)
            invoice.sgst_amount = data.get('sgst_amount', 0)
            invoice.igst_amount = data.get('igst_amount', 0)
            invoice.grand_total = data['grand_total']
            invoice.challan_references = data.get('challan_references', '')
            invoice.summary_start_date = data['summary_start_date']
            invoice.summary_end_date = data['summary_end_date']
            previous_status = invoice.status
            invoice.status = data.get('status', 'unpaid')
            if invoice.status == 'paid' and previous_status != 'paid':
                invoice.payment_date = datetime.now().date()
            elif invoice.status != 'paid':
                invoice.payment_date = None
            
            # Delete existing items
            item_ids = db.session.query(InvoiceItem.id).filter_by(invoice_id=id)
            db.session.execute(invoice_item_challan.delete().where(invoice_item_challan.c.invoice_item_id.in_(item_ids)))
            InvoiceItem.query.filter_by(invoice_id=id).delete()
            
            # Add updated items
            for item_data in data['items']:
                legacy_job_ids = item_data.get('job_ids', [])
                if isinstance(legacy_job_ids, str):
                    legacy_job_ids = [value for value in legacy_job_ids.split(',') if value]
                new_item = InvoiceItem(
                    invoice_id=invoice.id,
                    plate_size_id=item_data['plate_size_id'],
                    description=item_data.get('description', ''),
                    colours=item_data['colours'],
                    quantity=item_data['quantity'],
                    rate=item_data['rate'],
                    amount=item_data['amount'],
                    job_ids=','.join(map(str, legacy_job_ids))
                )
                attach_invoice_item_challans(
                    new_item, item_data.get('jobs'), legacy_job_ids,
                    invoice.customer_id, invoice.financial_year,
                    explicit_ids=item_data.get('challan_ids'),
                    start_date=invoice.summary_start_date, end_date=invoice.summary_end_date
                )
                db.session.add(new_item)
            
            record_audit_event('invoice.updated', 'invoice', invoice.id)
            db.session.commit()
            return jsonify(invoice.serialize()), 200
        
        if request.method == 'DELETE':
            if not require_current_role('admin'):
                return jsonify({"message": "Access denied"}), 403
            # First delete all related invoice items
            item_ids = db.session.query(InvoiceItem.id).filter_by(invoice_id=id)
            db.session.execute(invoice_item_challan.delete().where(invoice_item_challan.c.invoice_item_id.in_(item_ids)))
            InvoiceItem.query.filter_by(invoice_id=id).delete()
            # Then delete the invoice
            record_audit_event('invoice.deleted', 'invoice', invoice.id)
            db.session.delete(invoice)
            db.session.commit()
            return jsonify({"message": "Invoice deleted successfully"}), 200

    @app.route('/api/invoices/<int:id>/status', methods=['PATCH'])
    @role_required(['accountant', 'admin'])
    def update_invoice_status(id):
        invoice = Invoice.query.get_or_404(id)
        data = request.get_json(silent=True) or {}
        new_status = data.get('status')
        if new_status not in {'paid', 'unpaid', 'cancelled'}:
            return jsonify({"error": "Status must be paid, unpaid, or cancelled"}), 400

        previous_status = invoice.status
        invoice.status = new_status
        if new_status == 'paid' and previous_status != 'paid':
            invoice.payment_date = datetime.now().date()
        elif new_status != 'paid':
            invoice.payment_date = None
        record_audit_event('invoice.status_changed', 'invoice', invoice.id)
        db.session.commit()
        return jsonify(invoice.serialize()), 200

    @app.route('/api/invoice-number', methods=['GET'])
    @role_required(['accountant', 'admin'])
    def generate_invoice_number():
        current_year = datetime.now().year
        new_num = reserve_document_sequences(
            'invoice-legacy', str(current_year), 1,
            "SELECT COALESCE(MAX(CAST(substr(invoice_number, length('INV-' || :period || '-') + 1) AS INTEGER)), 0) "
            "FROM invoice WHERE invoice_number LIKE 'INV-' || :period || '-%'"
        )[0]
        new_invoice_number = f"INV-{current_year}-{new_num:04d}"
        return jsonify({"invoice_number": new_invoice_number}), 200

    @app.route('/api/invoices/next-sequences', methods=['GET'])
    @role_required(['accountant', 'admin'])
    def reserve_invoice_sequences():
        today = datetime.now()
        fy_start = today.year if today.month >= 4 else today.year - 1
        financial_year = f"{str(fy_start)[-2:]}{str(fy_start + 1)[-2:]}"
        count = request.args.get('count', 1, type=int) or 1
        sequences = reserve_document_sequences(
            'invoice', financial_year, count,
            'SELECT COALESCE(MAX(invoice_sequence), 0) FROM invoice WHERE financial_year=:period'
        )
        return jsonify({
            'financial_year': financial_year,
            'start': sequences[0],
            'count': len(sequences),
            'sequences': sequences,
            'invoice_numbers': [f'{financial_year}/GST/{sequence:02d}' for sequence in sequences]
        }), 200

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
        
        # Get the latest invoice from the current financial year only
        latest_invoice = Invoice.query.filter_by(financial_year=current_fy).order_by(Invoice.invoice_sequence.desc()).first()
        
        if latest_invoice:
            return jsonify(latest_invoice.serialize()), 200
        
        # No invoices for current FY — return current FY with sequence 0
        # (this handles new FY start, e.g. April 1st rollover from 2526 -> 2627)
        return jsonify({
            "financial_year": current_fy,
            "invoice_sequence": 0,
            "invoice_number": f"{current_fy}/GST/00"
        }), 200

    @app.route('/api/send-invoice-email', methods=['POST'])
    @role_required(['admin', 'accountant'])
    @limiter.limit('5 per hour')
    def send_invoice_email():
        try:
            try:
                smtp_username, smtp_password, _ = smtp_credentials()
            except RuntimeError:
                return jsonify({'error': 'Email service is not configured'}), 503
            if not smtp_username or not smtp_password:
                return jsonify({'error': 'Email service is not configured'}), 503
            app.config.update(MAIL_USERNAME=smtp_username, MAIL_PASSWORD=smtp_password, MAIL_SUPPRESS_SEND=False)
            invoice_id = request.form.get('invoice_id')
            subject = request.form.get('subject', '')
            message_text = request.form.get('message', '')
            if not invoice_id or not subject or len(subject) > 200 or any(c in subject for c in '\r\n'):
                return jsonify({'error': 'Invalid email fields'}), 400
            invoice = Invoice.query.get_or_404(invoice_id)
            customer = Customer.query.get_or_404(invoice.customer_id)
            recipients = [e.strip() for e in customer.email.split(',') if e.strip()]
            if not recipients or len(recipients) > 10:
                return jsonify({'error': 'Invoice client has no valid saved recipients'}), 400
            if len(message_text) > 10000:
                return jsonify({'error': 'Message is too long'}), 400
            msg = Message(subject=subject, recipients=recipients, body=message_text)
            for upload, filename in ((request.files.get('pdf'), 'invoice.pdf'), (request.files.get('summary_pdf'), 'customer_summary.pdf')):
                if upload:
                    payload = upload.read(5 * 1024 * 1024 + 1)
                    if len(payload) > 5 * 1024 * 1024 or not payload.startswith(b'%PDF-'):
                        return jsonify({'error': 'Attachments must be valid PDFs under 5 MB'}), 400
                    msg.attach(filename=filename, content_type='application/pdf', data=payload)
            mail.send(msg)
            record_audit_event('invoice.email_sent', 'invoice', invoice.id)
            db.session.commit()
            return jsonify({'message': 'Email sent successfully'})
        except Exception:
            app.logger.error('Invoice email send failed')
            return jsonify({'error': 'Email could not be sent'}), 500
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

