import os
from datetime import date

os.environ['APP_ENV'] = 'development'

import pytest
from app import create_app, db
from app.models import Challan, Customer, Invoice, InvoiceItem, PlateSize
from app import _backfill_invoice_item_challans


@pytest.fixture
def app(tmp_path):
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(tmp_path / 'invoice-links.sqlite').as_posix()}",
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


def seed_invoice_with_legacy_reference():
    customer = Customer(
        company_name='Example Co', contact_person='A', address='Address', phone='1',
        mobile='2', email='accounts@example.test'
    )
    size = PlateSize(length=10, width=20, is_dl=False)
    db.session.add_all([customer, size])
    db.session.flush()
    challan = Challan(
        challan_code='2627/DC/7', financial_year='2627', challan_sequence=7,
        date=date(2026, 6, 10), customer_id=customer.id
    )
    invoice = Invoice(
        invoice_number='2627/GST/1', financial_year='2627', invoice_sequence=1,
        invoice_date=date(2026, 6, 30), due_date=date(2026, 7, 30),
        customer_id=customer.id, total_amount=10, cgst_amount=0, sgst_amount=0,
        igst_amount=0, grand_total=10, summary_start_date=date(2026, 6, 1),
        summary_end_date=date(2026, 6, 30)
    )
    db.session.add_all([challan, invoice])
    db.session.flush()
    item = InvoiceItem(
        invoice_id=invoice.id, plate_size_id=size.id, description='10x20',
        colours='1', quantity=1, rate=10, amount=10, job_ids='7'
    )
    db.session.add(item)
    db.session.commit()
    return item.id, challan.id, customer.id


def test_legacy_invoice_challan_reference_backfills_without_changing_compatibility_field(app):
    with app.app_context():
        item_id, challan_id, _ = seed_invoice_with_legacy_reference()
        _backfill_invoice_item_challans()
        item = db.session.get(InvoiceItem, item_id)
        assert item.job_ids == '7'
        assert [challan.id for challan in item.challans] == [challan_id]
        assert item.serialize()['challan_codes'] == ['2627/DC/7']


def test_ambiguous_legacy_sequence_is_left_unlinked(app):
    with app.app_context():
        item_id, _, customer_id = seed_invoice_with_legacy_reference()
        duplicate = Challan(
            challan_code='2627/DC/7-duplicate', financial_year='2627', challan_sequence=7,
            date=date(2026, 6, 15), customer_id=customer_id
        )
        db.session.add(duplicate)
        db.session.commit()
        _backfill_invoice_item_challans()
        item = db.session.get(InvoiceItem, item_id)
        assert item.job_ids == '7'
        assert item.challans == []
