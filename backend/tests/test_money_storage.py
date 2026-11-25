import os
from datetime import date

os.environ['APP_ENV'] = 'development'

import pytest
from sqlalchemy import text
from app import create_app, db, _apply_money_migration
from app.models import Customer, Invoice, InvoiceItem, PlateSize


@pytest.fixture
def app(tmp_path):
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(tmp_path / 'money.sqlite').as_posix()}",
        'SECRET_KEY': 'test-secret-key-with-more-than-32-characters',
        'JWT_SECRET_KEY': 'test-jwt-key-with-more-than-32-characters',
        'JWT_COOKIE_SECURE': False,
        'TRUST_PROXY': False,
        'RATELIMIT_STORAGE_URI': 'memory://',
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


def test_money_assignments_store_cents_and_keep_api_numeric(app):
    with app.app_context():
        customer = Customer(
            company_name='Example Co', contact_person='A', address='Address', phone='1',
            mobile='2', email='accounts@example.test'
        )
        size = PlateSize(length=10, width=20, is_dl=False)
        db.session.add_all([customer, size])
        db.session.flush()
        invoice = Invoice(
            invoice_number='2627/GST/1', financial_year='2627', invoice_sequence=1,
            invoice_date=date(2026, 6, 30), due_date=date(2026, 7, 30), customer_id=customer.id,
            total_amount='1.005', cgst_amount='0', sgst_amount='0', igst_amount='0',
            grand_total='1.005'
        )
        db.session.add(invoice)
        db.session.flush()
        item = InvoiceItem(
            invoice_id=invoice.id, plate_size_id=size.id, description='10x20', colours='1',
            quantity=1, rate='2.675', amount='2.675'
        )
        db.session.add(item)
        db.session.commit()

        assert invoice.total_amount_cents == 101
        assert invoice.grand_total_cents == 101
        assert item.rate_cents == 268
        assert item.amount_cents == 268
        assert invoice.serialize()['grand_total'] == 1.01
        assert item.serialize()['amount'] == 2.68


def test_money_migration_backfills_legacy_float_with_half_up_rounding(app):
    with app.app_context():
        customer = Customer(
            company_name='Example Co', contact_person='A', address='Address', phone='1',
            mobile='2', email='accounts@example.test'
        )
        size = PlateSize(length=10, width=20, is_dl=False)
        db.session.add_all([customer, size])
        db.session.flush()
        invoice = Invoice(
            invoice_number='2627/GST/2', financial_year='2627', invoice_sequence=2,
            invoice_date=date(2026, 6, 30), due_date=date(2026, 7, 30), customer_id=customer.id,
            total_amount=0, cgst_amount=0, sgst_amount=0, igst_amount=0, grand_total=0
        )
        db.session.add(invoice)
        db.session.flush()
        item = InvoiceItem(
            invoice_id=invoice.id, plate_size_id=size.id, description='10x20', colours='1',
            quantity=1, rate=0, amount=0
        )
        db.session.add(item)
        db.session.commit()

        db.session.execute(text(
            'UPDATE invoice_item SET amount = 2.675, amount_cents = NULL WHERE id = :id'
        ), {'id': item.id})
        db.session.commit()
        _apply_money_migration(db)
        db.session.expire_all()
        item = db.session.get(InvoiceItem, item.id)

        assert item.amount_cents == 268
        assert item.serialize()['amount'] == 2.68
