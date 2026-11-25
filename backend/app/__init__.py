# filepath: backend/app/__init__.py
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config  # Import the Config class

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
from .migrations import create_views, run_migrations, _apply_money_migration, _backfill_invoice_item_challans


def create_app(test_config=None):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if app.config['TRUST_PROXY'] and not app.config.get('SMTP_CREDENTIAL_ENCRYPTION_KEY'):
        raise RuntimeError('SMTP_CREDENTIAL_ENCRYPTION_KEY must be configured for production')
    if app.config['TRUST_PROXY']:
        from cryptography.fernet import Fernet
        try:
            Fernet(app.config['SMTP_CREDENTIAL_ENCRYPTION_KEY'].encode('ascii'))
        except (ValueError, UnicodeError):
            raise RuntimeError('SMTP_CREDENTIAL_ENCRYPTION_KEY must be a valid Fernet key')
    if app.config['TRUST_PROXY'] and not app.config['RATELIMIT_STORAGE_URI'].startswith('redis://') and not app.config['RATELIMIT_STORAGE_URI'].startswith('rediss://'):
        raise RuntimeError('Production RATELIMIT_STORAGE_URI must use a shared Redis store')
    if app.config['TRUST_PROXY'] and any(not origin.startswith('https://') for origin in app.config['CORS_ORIGINS']):
        raise RuntimeError('Production CORS_ORIGINS entries must use HTTPS')

    # Disable SMTP debug output
    import logging
    logging.getLogger('mail.log').setLevel(logging.ERROR)

    app.config['MAIL_DEBUG'] = False

    if app.config['TRUST_PROXY']:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    mail.init_app(app)
    limiter.init_app(app, storage_uri=app.config['RATELIMIT_STORAGE_URI'])

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}}, supports_credentials=True)
    migrate.init_app(app, db)

    with app.app_context():
        from . import routes
        routes.register_routes(app)
        from .models import User, Item, Customer, PlateSize, WastePlate, Job, Plate, UsedPlate, RevokedToken
        run_migrations(db)
        User.disable_known_default_credentials()
        create_views()

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'"
        if app.config['JWT_COOKIE_SECURE']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception('Unhandled application error')
        return jsonify({"message": "Internal server error"}), 500

    @app.cli.command('create-admin')
    def create_admin():
        """Interactively create or reset an administrator account."""
        import getpass
        username = input('Admin username: ').strip()
        password = getpass.getpass('New password (12+ characters): ')
        if not 12 <= len(password) <= 256:
            raise SystemExit('Password must be between 12 and 256 characters.')
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, first_name='Admin', last_name='User', role='admin')
            db.session.add(user)
        user.password = __import__('werkzeug.security', fromlist=['generate_password_hash']).generate_password_hash(password, method='scrypt')
        user.role, user.is_active = 'admin', True
        user.auth_version = (user.auth_version or 0) + 1
        db.session.commit()
        print('Administrator account is ready.')

    return app