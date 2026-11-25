# filepath: backend/app/models.py
from . import db
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from sqlalchemy.orm import validates


def _money_cents(value):
    """Convert API-compatible numeric money values to exact cents."""
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('Monetary values must be valid numbers')
    if not amount.is_finite():
        raise ValueError('Monetary values must be finite')
    return int(amount * 100)


def _money_float(cents, fallback):
    return float(Decimal(cents) / 100) if cents is not None else fallback

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum('admin', 'editor', 'user', 'accountant', name='user_roles'), nullable=False)  # Added 'accountant' role
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    auth_version = db.Column(db.Integer, default=0, nullable=False)

    @staticmethod
    def disable_known_default_credentials():
        defaults = {'admin': 'admin', 'accountant': 'accountant'}
        changed = False
        for username, password in defaults.items():
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                user.password = generate_password_hash(secrets.token_urlsafe(48), method='scrypt')
                user.is_active = False
                user.auth_version = (user.auth_version or 0) + 1
                changed = True
        if changed:
            db.session.commit()


class RevokedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)

class AppSetting(db.Model):
    """Encrypted application settings; SMTP secrets are never serialized."""
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=False)

class AuditLog(db.Model):
    """Minimal audit record for security and finance state changes."""
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), index=True)

class DocumentSequence(db.Model):
    """Atomic sequence high-water marks for document number reservations."""
    name = db.Column(db.String(40), primary_key=True)
    period = db.Column(db.String(12), primary_key=True)
    value = db.Column(db.Integer, nullable=False, default=0)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'price': self.price
        }

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), unique=True, nullable=False)
    contact_person = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(500), nullable=False)  # Increase length for multiple emails
    gstin = db.Column(db.String(15), nullable=True)
    state = db.Column(db.String(50), nullable=True, default="Maharashtra")
    code = db.Column(db.String(10), nullable=True, default="27")
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'contact_person': self.contact_person,
            'address': self.address,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': self.email.split(',') if self.email else [],
            'gstin': self.gstin,
            'state': self.state,
            'code': self.code,
            'is_archived': self.is_archived
        }
        
class PlateSize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    length = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    min_quantity = db.Column(db.Integer, nullable=True)
    is_dl = db.Column(db.Boolean, default=False)
    # New columns
    prefix = db.Column(db.String(50), nullable=True)
    suffix = db.Column(db.String(50), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "length": self.length,
            "width": self.width,
            "min_quantity": self.min_quantity,
            "is_dl": self.is_dl,
            "prefix": self.prefix,
            "suffix": self.suffix
        }

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'size_id': self.size_id,
            'quantity': self.quantity,
            'is_archived': self.is_archived
        }
    
class WastePlate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    quantity_wasted = db.Column(db.Integer, nullable=False)
    waste_date = db.Column(db.Date, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'size_id': self.size_id,
            'quantity_wasted': self.quantity_wasted,
            'waste_date': self.waste_date,
            'is_archived': self.is_archived
        }

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), nullable=False)
    challan_id = db.Column(db.Integer, db.ForeignKey('challan.id'), nullable=False)  # Updated to link directly to Challan
    plate_size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    colour = db.Column(db.Integer, nullable=False)
    job_id = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    plates = db.Column(db.Integer, nullable=False)
    remark = db.Column(db.String(200), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'challan_id': self.challan_id,
            'plate_size_id': self.plate_size_id,
            'colour': self.colour,
            'job_id': self.job_id,
            'quantity': self.quantity,
            'plates': self.plates,
            'remark': self.remark,
        }

class Plate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity
        }

class UsedPlate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_id = db.Column(db.Integer, db.ForeignKey('plate.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'plate_id': self.plate_id,
            'quantity': self.quantity
        }

class Challan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challan_code = db.Column(db.String(100), unique=True, nullable=False)
    financial_year = db.Column(db.String(4), nullable=True)   # e.g. "2627" for 2026-27
    challan_sequence = db.Column(db.Integer, nullable=True)   # e.g. 1, 2, 3 within the FY
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    special_instructions = db.Column(db.Text, nullable=True)  # New field for special instructions
    printed = db.Column(db.Boolean, default=False)  # New field to track if challan has been printed
    jobs = db.relationship('Job', backref='challan', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'challan_code': self.challan_code,
            'financial_year': self.financial_year,
            'challan_sequence': self.challan_sequence,
            'is_archived': self.is_archived,
            'date': self.date.isoformat(),
            'customer_id': self.customer_id,
            'special_instructions': self.special_instructions,  # Include in serialization
            'printed': self.printed,  # Include printed status in serialization
            'jobs': [job.serialize() for job in self.jobs]
        }

class CustomerRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    plate_size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    plate_rate = db.Column(db.Float, nullable=False, default=0.0)  # Changed from rate to plate_rate
    baking_rate = db.Column(db.Float, nullable=False, default=0.0) # Added new baking_rate field
    plate_rate_cents = db.Column(db.Integer, nullable=False, default=0)
    baking_rate_cents = db.Column(db.Integer, nullable=False, default=0)

    @validates('plate_rate', 'baking_rate')
    def store_rate_cents(self, key, value):
        cents = _money_cents(value)
        setattr(self, f'{key}_cents', cents)
        return cents / 100
    
    # Define unique constraint for customer_id and plate_size_id
    __table_args__ = (
        db.UniqueConstraint('customer_id', 'plate_size_id', name='unique_customer_plate_size'),
    )
    
    # Relationships
    customer = db.relationship('Customer', backref=db.backref('rates', lazy=True))
    plate_size = db.relationship('PlateSize', backref=db.backref('rates', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'plate_size_id': self.plate_size_id,
            'plate_rate': _money_float(self.plate_rate_cents, self.plate_rate),
            'baking_rate': _money_float(self.baking_rate_cents, self.baking_rate)
        }

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    financial_year = db.Column(db.String(4), nullable=False)  # Store as "2526" for 2025-26
    invoice_sequence = db.Column(db.Integer, nullable=False)  # Store as 34
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    cgst_amount = db.Column(db.Float, nullable=False, default=0.0)
    sgst_amount = db.Column(db.Float, nullable=False, default=0.0)
    igst_amount = db.Column(db.Float, nullable=False, default=0.0)
    grand_total = db.Column(db.Float, nullable=False, default=0.0)
    total_amount_cents = db.Column(db.Integer, nullable=False, default=0)
    cgst_amount_cents = db.Column(db.Integer, nullable=False, default=0)
    sgst_amount_cents = db.Column(db.Integer, nullable=False, default=0)
    igst_amount_cents = db.Column(db.Integer, nullable=False, default=0)
    grand_total_cents = db.Column(db.Integer, nullable=False, default=0)
    challan_references = db.Column(db.String(200), nullable=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, cancelled
    payment_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    summary_start_date = db.Column(db.Date, nullable=True)
    summary_end_date = db.Column(db.Date, nullable=True)

    @validates('total_amount', 'cgst_amount', 'sgst_amount', 'igst_amount', 'grand_total')
    def store_total_cents(self, key, value):
        cents = _money_cents(value)
        setattr(self, f'{key}_cents', cents)
        return cents / 100
    
    # Relationships
    customer = db.relationship('Customer', backref=db.backref('invoices', lazy=True))
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade="all, delete-orphan")
    
    def serialize(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'financial_year': self.financial_year,
            'invoice_sequence': self.invoice_sequence,
            'invoice_date': self.invoice_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'customer_id': self.customer_id,
            'customer_name': self.customer.company_name,
            'total_amount': _money_float(self.total_amount_cents, self.total_amount),
            'cgst_amount': _money_float(self.cgst_amount_cents, self.cgst_amount),
            'sgst_amount': _money_float(self.sgst_amount_cents, self.sgst_amount),
            'igst_amount': _money_float(self.igst_amount_cents, self.igst_amount),
            'grand_total': _money_float(self.grand_total_cents, self.grand_total),
            'challan_references': self.challan_references,
            'is_archived': self.is_archived,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'created_at': self.created_at.isoformat(),
            'summary_start_date': self.summary_start_date.isoformat() if self.summary_start_date else None,
            'summary_end_date': self.summary_end_date.isoformat() if self.summary_end_date else None,
            'items': [item.serialize() for item in self.items]
        }

invoice_item_challan = db.Table(
    'invoice_item_challan',
    db.Column('invoice_item_id', db.Integer, db.ForeignKey('invoice_item.id', ondelete='CASCADE'), primary_key=True),
    db.Column('challan_id', db.Integer, db.ForeignKey('challan.id'), primary_key=True),
)

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    plate_size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    colours = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    rate_cents = db.Column(db.Integer, nullable=False, default=0)
    amount_cents = db.Column(db.Integer, nullable=False, default=0)
    job_ids = db.Column(db.String(500), nullable=True)  # Comma-separated job IDs
    
    # Relationships
    plate_size = db.relationship('PlateSize', backref=db.backref('invoice_items', lazy=True))
    challans = db.relationship('Challan', secondary=invoice_item_challan, lazy=True)

    @validates('rate', 'amount')
    def store_item_money_cents(self, key, value):
        cents = _money_cents(value)
        setattr(self, f'{key}_cents', cents)
        return cents / 100
    
    def serialize(self):
        plate_size = self.plate_size
        size_description = f"{plate_size.length}x{plate_size.width}"
        if plate_size.is_dl:
            size_description += "-DL"
            
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'plate_size_id': self.plate_size_id,
            'plate_size': size_description,
            'description': self.description,
            'colours': self.colours,
            'quantity': self.quantity,
            'rate': _money_float(self.rate_cents, self.rate),
            'amount': _money_float(self.amount_cents, self.amount),
            'job_ids': self.job_ids,
            'challan_ids': [challan.id for challan in self.challans],
            'challan_codes': [challan.challan_code for challan in self.challans]
        }
