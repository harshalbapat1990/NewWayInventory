import os

os.environ['APP_ENV'] = 'development'

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Customer, User


@pytest.fixture
def app(tmp_path):
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(tmp_path / 'customers.sqlite').as_posix()}",
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


def login_as(app, client, role):
    with app.app_context():
        user = User(
            username=f'{role}-test', password=generate_password_hash('a-secure-test-password', method='scrypt'),
            first_name='Test', last_name='User', role=role,
        )
        db.session.add(user)
        db.session.commit()
    result = client.post('/api/login', json={
        'username': f'{role}-test', 'password': 'a-secure-test-password'
    })
    assert result.status_code == 200
    return {'X-CSRF-TOKEN': client.get_cookie('csrf_access_token').value}


def add_customer():
    customer = Customer(
        company_name='Example Co', contact_person='Accounts', address='Road',
        phone='123', mobile='456', email='accounts@example.test',
    )
    db.session.add(customer)
    db.session.commit()
    return customer.id


def test_archive_restore_and_default_list_filter_preserve_customer(app, client):
    headers = login_as(app, client, 'editor')
    with app.app_context():
        customer_id = add_customer()

    archived = client.patch(f'/api/customers/{customer_id}/archive', headers=headers)
    assert archived.status_code == 200
    assert archived.json['is_archived'] is True
    assert client.get('/api/customers').json == []
    assert len(client.get('/api/customers?include_archived=true').json) == 1
    assert client.get(f'/api/customers/{customer_id}').json['id'] == customer_id

    restored = client.patch(f'/api/customers/{customer_id}/restore', headers=headers)
    assert restored.status_code == 200
    assert restored.json['is_archived'] is False
    assert len(client.get('/api/customers').json) == 1


def test_regular_user_cannot_archive_customer(app, client):
    headers = login_as(app, client, 'user')
    with app.app_context():
        customer_id = add_customer()
    assert client.patch(f'/api/customers/{customer_id}/archive', headers=headers).status_code == 403
