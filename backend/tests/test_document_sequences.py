import os
from concurrent.futures import ThreadPoolExecutor

os.environ['APP_ENV'] = 'development'

import pytest
from app import create_app
from app.routes import reserve_document_sequences


@pytest.fixture
def app(tmp_path):
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(tmp_path / 'sequences.sqlite').as_posix()}",
        'SECRET_KEY': 'test-secret-key-with-more-than-32-characters',
        'JWT_SECRET_KEY': 'test-jwt-key-with-more-than-32-characters',
        'JWT_COOKIE_SECURE': False,
        'TRUST_PROXY': False,
        'RATELIMIT_STORAGE_URI': 'memory://',
    })
    yield application
    with application.app_context():
        from app import db
        db.session.remove()
        db.engine.dispose()


def test_concurrent_reservations_never_overlap(app):
    def reserve_one(_):
        with app.app_context():
            return reserve_document_sequences(
                'invoice', '2627', 1,
                'SELECT COALESCE(MAX(invoice_sequence), 0) FROM invoice WHERE financial_year=:period'
            )[0]

    with ThreadPoolExecutor(max_workers=12) as executor:
        numbers = list(executor.map(reserve_one, range(30)))

    assert sorted(numbers) == list(range(1, 31))


def test_block_reservation_advances_following_single_number(app):
    with app.app_context():
        reserved = reserve_document_sequences(
            'invoice', '2627', 4,
            'SELECT COALESCE(MAX(invoice_sequence), 0) FROM invoice WHERE financial_year=:period'
        )
        following = reserve_document_sequences(
            'invoice', '2627', 1,
            'SELECT COALESCE(MAX(invoice_sequence), 0) FROM invoice WHERE financial_year=:period'
        )
    assert reserved == [1, 2, 3, 4]
    assert following == [5]
