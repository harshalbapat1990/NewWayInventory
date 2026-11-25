"""SMTP credential resolution and accountant/admin settings endpoints."""
import json
import smtplib
import ssl

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app, jsonify, request

from . import db
from .audit import record_audit_event
from .models import AppSetting
from .validation import json_object


def _cipher():
    key = current_app.config.get('SMTP_CREDENTIAL_ENCRYPTION_KEY')
    if not key:
        raise RuntimeError('SMTP credential encryption is not configured')
    return Fernet(key.encode('ascii'))


def smtp_credentials():
    """Return username, password and whether they came from encrypted settings."""
    saved = AppSetting.query.get('smtp_credentials')
    if saved:
        try:
            values = json.loads(_cipher().decrypt(saved.value.encode()).decode())
            return values['username'], values['password'], True
        except (InvalidToken, ValueError, KeyError, TypeError, RuntimeError, UnicodeError):
            # A corrupt saved value must never silently fall back to environment secrets.
            raise RuntimeError('Saved SMTP credentials are unavailable')
    return current_app.config.get('MAIL_USERNAME'), current_app.config.get('MAIL_PASSWORD'), False


def register_smtp_settings_routes(app, role_required, limiter):
    @app.route('/api/settings/smtp', methods=['GET'])
    @role_required(['admin', 'accountant'])
    def get_smtp_settings():
        try:
            username, password, saved = smtp_credentials()
        except RuntimeError:
            return jsonify({'message': 'SMTP settings are unavailable'}), 503
        return jsonify({
            'configured': bool(username and password),
            'username': username or '',
            'source': 'saved' if saved else ('environment' if username and password else 'unset'),
        })

    @app.route('/api/settings/smtp', methods=['PUT'])
    @limiter.limit('5 per hour')
    @role_required(['admin', 'accountant'])
    def update_smtp_settings():
        data = json_object()
        if data is None:
            return jsonify({'message': 'SMTP settings must be an object'}), 400
        username, password = data.get('username'), data.get('password')
        if (not isinstance(username, str) or not username.strip() or len(username) > 254
                or not isinstance(password, str) or not password or len(password) > 512):
            return jsonify({'message': 'Enter a valid SMTP username and password'}), 400
        try:
            cipher = _cipher()
            host, port = current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']
            context = ssl.create_default_context()
            if current_app.config.get('MAIL_USE_SSL'):
                with smtplib.SMTP_SSL(host, port, timeout=10, context=context) as client:
                    client.login(username.strip(), password)
            else:
                with smtplib.SMTP(host, port, timeout=10) as client:
                    client.ehlo()
                    if current_app.config.get('MAIL_USE_TLS'):
                        client.starttls(context=context)
                        client.ehlo()
                    client.login(username.strip(), password)
            encrypted = cipher.encrypt(json.dumps({
                'username': username.strip(), 'password': password
            }).encode()).decode()
        except (RuntimeError, ValueError, OSError, smtplib.SMTPException):
            return jsonify({'message': 'Could not verify SMTP settings; existing settings were kept'}), 400

        setting = AppSetting.query.get('smtp_credentials')
        if setting is None:
            setting = AppSetting(key='smtp_credentials', value=encrypted)
            db.session.add(setting)
        else:
            setting.value = encrypted
        record_audit_event('smtp.credentials_replaced', 'smtp_settings', 'global')
        db.session.commit()
        current_app.config.update(
            MAIL_USERNAME=username.strip(),
            MAIL_PASSWORD=password,
            MAIL_DEFAULT_SENDER=current_app.config.get('MAIL_DEFAULT_SENDER') or username.strip(),
            MAIL_SUPPRESS_SEND=False,
        )
        return jsonify({'configured': True, 'username': username.strip()})
