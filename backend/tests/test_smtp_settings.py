import base64
import os

os.environ['APP_ENV'] = 'development'

import pytest
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import AppSetting, User


@pytest.fixture
def app(tmp_path):
    key = base64.urlsafe_b64encode(b'01234567890123456789012345678901').decode()
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(tmp_path / 'smtp.sqlite').as_posix()}",
        'SECRET_KEY': 'test-secret-key-with-more-than-32-characters',
        'JWT_SECRET_KEY': 'test-jwt-key-with-more-than-32-characters',
        'SMTP_CREDENTIAL_ENCRYPTION_KEY': key,
        'JWT_COOKIE_SECURE': False,
        'TRUST_PROXY': False,
        'RATELIMIT_STORAGE_URI': 'memory://',
        'MAIL_SERVER': 'smtp.example.test',
        'MAIL_PORT': 465,
        'MAIL_USE_SSL': True,
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def authenticate(app, client, role):
    with app.app_context():
        user = User(username=f'{role}-user', password=generate_password_hash('a-secure-test-password', method='scrypt'), first_name='Test', last_name='User', role=role, is_active=True)
        db.session.add(user)
        db.session.commit()
    response = client.post('/api/login', json={'username': f'{role}-user', 'password': 'a-secure-test-password'})
    assert response.status_code == 200
    return {'X-CSRF-TOKEN': client.get_cookie('csrf_access_token').value}


def test_accountant_can_replace_smtp_password_without_getting_it(app, client, monkeypatch):
    import app.smtp_settings as smtp_settings

    class SMTP:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def login(self, username, password):
            assert username == 'billing@example.test'
            assert password == 'never-return-this'

    monkeypatch.setattr(smtp_settings.smtplib, 'SMTP_SSL', SMTP)
    headers = authenticate(app, client, 'accountant')
    saved = client.put('/api/settings/smtp', json={'username': 'billing@example.test', 'password': 'never-return-this'}, headers=headers)
    assert saved.status_code == 200
    assert 'password' not in saved.json
    status = client.get('/api/settings/smtp')
    assert status.json == {'configured': True, 'username': 'billing@example.test', 'source': 'saved'}
    with app.app_context():
        stored = AppSetting.query.get('smtp_credentials').value
        assert 'never-return-this' not in stored


def test_non_finance_user_cannot_view_or_update_smtp(app, client):
    headers = authenticate(app, client, 'user')
    assert client.get('/api/settings/smtp').status_code == 403
    assert client.put('/api/settings/smtp', json={'username': 'x', 'password': 'y'}, headers=headers).status_code == 403


def test_failed_smtp_check_does_not_replace_saved_credential(app, client, monkeypatch):
    import app.smtp_settings as smtp_settings

    class SMTP:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def login(self, username, password):
            if password == 'bad-password':
                raise smtp_settings.smtplib.SMTPAuthenticationError(535, b'authentication failed')

    monkeypatch.setattr(smtp_settings.smtplib, 'SMTP_SSL', SMTP)
    headers = authenticate(app, client, 'admin')
    first = client.put('/api/settings/smtp', json={'username': 'billing@example.test', 'password': 'old-good-password'}, headers=headers)
    assert first.status_code == 200
    rejected = client.put('/api/settings/smtp', json={'username': 'attacker@example.test', 'password': 'bad-password'}, headers=headers)
    assert rejected.status_code == 400
    status = client.get('/api/settings/smtp')
    assert status.json['username'] == 'billing@example.test'
    with app.app_context():
        assert 'attacker@example.test' not in AppSetting.query.get('smtp_credentials').value
