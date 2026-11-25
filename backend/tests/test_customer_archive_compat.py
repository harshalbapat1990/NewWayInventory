import sqlite3

import pytest
from flask_jwt_extended import create_access_token

from app import create_app, db
from app.config import Config
from app.models import Customer


@pytest.fixture
def app(tmp_path, monkeypatch):
    database = tmp_path / 'archive-test.sqlite'
    monkeypatch.setattr(Config, 'SQLALCHEMY_DATABASE_URI', f'sqlite:///{database.as_posix()}')
    app = create_app()
    app.config.update(TESTING=True)
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def bearer_headers(app, role):
    with app.app_context():
        token = create_access_token(identity='test-user', additional_claims={'role': role})
    return {'Authorization': f'Bearer {token}'}


@pytest.mark.parametrize('role', ['user', 'editor', 'admin', 'accountant'])
def test_each_operational_role_can_list_active_and_archived_customers(app, role):
    with app.app_context():
        db.session.add_all([
            Customer(company_name='Active Co', contact_person='A', address='Road', phone='1', mobile='2', email='a@example.test'),
            Customer(company_name='Archived Co', contact_person='B', address='Road', phone='3', mobile='4', email='b@example.test', is_archived=True),
        ])
        db.session.commit()

    response = app.test_client().get(
        '/api/customers?include_archived=true', headers=bearer_headers(app, role)
    )
    assert response.status_code == 200
    assert {customer['company_name'] for customer in response.json} == {'Active Co', 'Archived Co'}


def test_accountant_can_read_customers_but_cannot_create_them(app):
    response = app.test_client().post(
        '/api/customers', json={}, headers=bearer_headers(app, 'accountant')
    )
    assert response.status_code == 403


def test_startup_migrates_existing_customer_rows_without_changing_ids(tmp_path, monkeypatch):
    database = tmp_path / 'legacy.sqlite'
    connection = sqlite3.connect(database)
    connection.execute('''
        CREATE TABLE customer (
            id INTEGER PRIMARY KEY, company_name VARCHAR(100) NOT NULL UNIQUE,
            contact_person VARCHAR(100) NOT NULL, address VARCHAR(200) NOT NULL,
            phone VARCHAR(20) NOT NULL, mobile VARCHAR(20) NOT NULL,
            email VARCHAR(500) NOT NULL, gstin VARCHAR(15),
            state VARCHAR(50), code VARCHAR(10)
        )
    ''')
    connection.execute(
        "INSERT INTO customer (id, company_name, contact_person, address, phone, mobile, email) VALUES (42, 'Legacy Co', 'Legacy', 'Road', '1', '2', 'legacy@example.test')"
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(Config, 'SQLALCHEMY_DATABASE_URI', f'sqlite:///{database.as_posix()}')

    app = create_app()
    with app.app_context():
        legacy = db.session.get(Customer, 42)
        assert legacy is not None
        assert legacy.company_name == 'Legacy Co'
        assert legacy.is_archived is False
        db.session.remove()
        db.engine.dispose()
