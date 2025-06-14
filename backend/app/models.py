# filepath: backend/app/models.py
from . import db
from werkzeug.security import generate_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum('admin', 'editor', 'user', 'accountant', name='user_roles'), nullable=False)  # Added 'accountant' role

    @staticmethod
    def create_default_users():
        default_users = [
            {
                'username': 'admin',
                'password': 'admin',
                'first_name': 'Default',
                'last_name': 'Admin',
                'role': 'admin'
            },
            {
                'username': 'accountant',
                'password': 'accountant',
                'first_name': 'Default',
                'last_name': 'Accountant',
                'role': 'accountant'
            }
        ]

        for user_data in default_users:
            if not User.query.filter_by(username=user_data['username']).first():
                user = User(
                    username=user_data['username'],
                    password=generate_password_hash(user_data['password'], method='pbkdf2:sha256'),
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role']
                )
                db.session.add(user)
        db.session.commit()

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
            'code': self.code
        }
        
class PlateSize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    min_quantity = db.Column(db.Integer, nullable=True, default=20)
    is_dl = db.Column(db.Boolean, nullable=False, default=False)  # New field for DL type

    def serialize(self):
        return {
            'id': self.id,
            'length': self.length,
            'width': self.width,
            'min_quantity': self.min_quantity,
            'is_dl': self.is_dl
        }

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'size_id': self.size_id,
            'quantity': self.quantity
        }
    
class WastePlate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    quantity_wasted = db.Column(db.Integer, nullable=False)
    waste_date = db.Column(db.Date, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'size_id': self.size_id,
            'quantity_wasted': self.quantity_wasted,
            'waste_date': self.waste_date
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
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    special_instructions = db.Column(db.Text, nullable=True)  # New field for special instructions
    printed = db.Column(db.Boolean, default=False)  # New field to track if challan has been printed
    jobs = db.relationship('Job', backref='challan', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'challan_code': self.challan_code,
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
            'plate_rate': self.plate_rate,
            'baking_rate': self.baking_rate
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
    challan_references = db.Column(db.String(200), nullable=True) 
    status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, cancelled
    payment_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
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
            'total_amount': self.total_amount,
            'cgst_amount': self.cgst_amount,
            'sgst_amount': self.sgst_amount,
            'igst_amount': self.igst_amount,
            'grand_total': self.grand_total,
            'challan_references': self.challan_references,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'created_at': self.created_at.isoformat(),
            'items': [item.serialize() for item in self.items]
        }

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    plate_size_id = db.Column(db.Integer, db.ForeignKey('plate_size.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    colours = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    job_ids = db.Column(db.String(500), nullable=True)  # Comma-separated job IDs
    
    # Relationships
    plate_size = db.relationship('PlateSize', backref=db.backref('invoice_items', lazy=True))
    
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
            'rate': self.rate,
            'amount': self.amount,
            'job_ids': self.job_ids
        }
