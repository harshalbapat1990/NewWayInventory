import os
from datetime import date

os.environ['APP_ENV'] = 'development'

import pytest
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from app import create_app, create_views, db
from app.models import Challan, Customer, Job, PlateSize, Purchase, User, WastePlate


@pytest.fixture
def app(tmp_path):
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(tmp_path / 'reports.sqlite').as_posix()}",
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


@pytest.fixture
def client(app):
    return app.test_client()


def test_stock_and_customer_summary_views_return_consistent_totals(app, client):
    with app.app_context():
        user = User(
            username='report-user', password=generate_password_hash('test-password-here', method='scrypt'),
            first_name='Report', last_name='User', role='user'
        )
        customer = Customer(
            company_name='Report Co', contact_person='Accounts', address='Road', phone='1',
            mobile='2', email='report@example.test'
        )
        size = PlateSize(length=10, width=20, is_dl=False)
        db.session.add_all([user, customer, size])
        db.session.flush()
        challan = Challan(
            challan_code='2627/DC/1', financial_year='2627', challan_sequence=1,
            date=date(2026, 6, 1), customer_id=customer.id
        )
        db.session.add_all([
            challan,
            Purchase(date=date(2026, 6, 1), size_id=size.id, quantity=100),
            WastePlate(size_id=size.id, quantity_wasted=7, waste_date=date(2026, 6, 2)),
        ])
        db.session.flush()
        db.session.add(Job(
            job_name='Fixture', challan_id=challan.id, plate_size_id=size.id,
            colour=2, job_id='R1', quantity=3, plates=6, remark=''
        ))
        db.session.commit()

    login = client.post('/api/login', json={
        'username': 'report-user', 'password': 'test-password-here'
    })
    assert login.status_code == 200

    stock = client.get('/api/stock-summary')
    assert stock.status_code == 200
    assert stock.json[0]['total_purchased'] == 100
    assert stock.json[0]['total_wasted'] == 7
    assert stock.json[0]['total_used'] == 6
    assert stock.json[0]['current_stock'] == 87

    summary = client.get('/api/customer-summary')
    assert summary.status_code == 200
    assert summary.json == [{'customer_name': 'Report Co', 'total_jobs': 1, 'total_plates': 3}]

    # Re-running view setup must leave a valid report view in place.
    with app.app_context():
        create_views()
        assert db.session.execute(text('SELECT current_stock FROM stock_summary_view')).scalar() == 87
