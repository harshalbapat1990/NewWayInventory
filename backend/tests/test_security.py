import os
os.environ['APP_ENV'] = 'development'

import pytest
from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import AuditLog, Customer, Invoice, User


@pytest.fixture
def app(tmp_path):
    database = tmp_path / 'security-test.sqlite'
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database.as_posix()}',
        'SECRET_KEY': 'test-secret-key-with-more-than-32-characters',
        'JWT_SECRET_KEY': 'test-jwt-key-with-more-than-32-characters',
        'JWT_COOKIE_SECURE': False,
        'TRUST_PROXY': False,
        'RATELIMIT_STORAGE_URI': 'memory://',
        'MAIL_SUPPRESS_SEND': True,
    })
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def add_user(app, username, role):
    with app.app_context():
        user = User(username=username, password=generate_password_hash('Correct horse battery staple', method='scrypt'), first_name='Test', last_name='User', role=role, is_active=True)
        db.session.add(user)
        db.session.commit()
        return user.id


def login(client, username='test-user'):
    response = client.post('/api/login', json={'username': username, 'password': 'Correct horse battery staple'})
    assert response.status_code == 200
    return response


def csrf(client, cookie='csrf_access_token'):
    return {'X-CSRF-TOKEN': client.get_cookie(cookie).value}


def test_public_registration_is_disabled(client):
    response = client.post('/api/register', json={
        'username': 'attacker', 'password': 'Correct horse battery staple',
        'first_name': 'A', 'last_name': 'B', 'role': 'admin',
    })
    assert response.status_code == 404


def test_startup_does_not_create_seeded_accounts(app):
    with app.app_context():
        assert User.query.filter(User.username.in_(['admin', 'accountant'])).count() == 0


def test_user_cannot_manage_users_or_clients(client, app):
    add_user(app, 'test-user', 'user')
    login(client)
    headers = csrf(client)
    users = client.post('/api/users', json={
        'username': 'new-admin', 'password': 'Correct horse battery staple',
        'first_name': 'New', 'last_name': 'Admin', 'role': 'admin',
    }, headers=headers)
    delete_client = client.delete('/api/customers/1', headers=headers)
    assert users.status_code == 403
    assert delete_client.status_code == 403


def test_admin_can_provision_an_account_but_public_cannot(client, app):
    add_user(app, 'root-admin', 'admin')
    login(client, 'root-admin')
    response = client.post('/api/users', json={
        'username': 'new-user', 'password': 'Correct horse battery staple',
        'first_name': 'New', 'last_name': 'User', 'role': 'user',
    }, headers=csrf(client))
    assert response.status_code == 201
    assert response.json['role'] == 'user'
    assert 'password' not in response.json


def test_last_active_admin_cannot_be_demoted(client, app):
    admin_id = add_user(app, 'only-admin', 'admin')
    login(client, 'only-admin')
    response = client.patch(
        f'/api/users/{admin_id}', json={'role': 'user'}, headers=csrf(client)
    )
    assert response.status_code == 409


def test_write_routes_require_csrf(client, app):
    add_user(app, 'test-user', 'user')
    login(client)
    response = client.post('/api/waste-plates', json={})
    assert response.status_code == 401


def test_invoice_payment_status_sets_payment_date_and_writes_audit(client, app):
    add_user(app, 'billing-user', 'accountant')
    with app.app_context():
        customer = Customer(
            company_name='Billing Co', contact_person='Accounts', address='Road', phone='1',
            mobile='2', email='billing@example.test'
        )
        db.session.add(customer)
        db.session.flush()
        invoice = Invoice(
            invoice_number='2627/GST/3', financial_year='2627', invoice_sequence=3,
            invoice_date=date(2026, 6, 1), due_date=date(2026, 7, 1), customer_id=customer.id,
            total_amount=100, cgst_amount=0, sgst_amount=0, igst_amount=0, grand_total=100,
        )
        db.session.add(invoice)
        db.session.commit()
        invoice_id = invoice.id

    login(client, 'billing-user')
    response = client.patch(
        f'/api/invoices/{invoice_id}/status', json={'status': 'paid'}, headers=csrf(client)
    )
    assert response.status_code == 200
    assert response.json['payment_date']

    invalid = client.patch(
        f'/api/invoices/{invoice_id}/status', json={'status': 'refunded'}, headers=csrf(client)
    )
    assert invalid.status_code == 400
    with app.app_context():
        event = AuditLog.query.filter_by(action='invoice.status_changed', entity_id=str(invoice_id)).one()
        assert event.actor_user_id is not None
