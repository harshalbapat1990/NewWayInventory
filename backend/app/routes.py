from flask import request, jsonify, render_template_string, send_from_directory
from sqlalchemy import text
from . import db, jwt, limiter, mail
from .models import User, RevokedToken
import os
import sys
from .smtp_settings import register_smtp_settings_routes, smtp_credentials
from .auth import role_required, require_current_role
from .customers import register_customer_routes
from .plate_sizes import register_plate_size_routes
from .invoices import register_invoice_routes
from .challans import register_challan_routes
from .inventory import register_inventory_routes
from .accounts import register_account_routes
from .archives import register_archive_routes
from .printing import register_print_routes


@jwt.token_in_blocklist_loader
def token_is_revoked(jwt_header, jwt_payload):
    if RevokedToken.query.filter_by(jti=jwt_payload.get('jti')).first():
        return True
    user = User.query.get(jwt_payload.get('sub'))
    return user is None or not user.is_active or jwt_payload.get('auth_version') != user.auth_version

def reserve_document_sequences(name, period, count, existing_max_sql):
    """Reserve a non-overlapping sequence range under a SQLite write lock."""
    count = max(1, min(int(count), 500))
    connection = db.engine.connect()
    try:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        row = connection.execute(
            text('SELECT value FROM document_sequence WHERE name=:name AND period=:period'),
            {'name': name, 'period': period}
        ).first()
        existing_max = connection.execute(text(existing_max_sql), {'period': period}).scalar() or 0
        if row is None:
            current = existing_max
            connection.execute(text('INSERT INTO document_sequence (name, period, value) VALUES (:name, :period, :value)'), {
                'name': name, 'period': period, 'value': current
            })
        else:
            current = max(row[0], existing_max)
        start = int(current) + 1
        connection.execute(text('UPDATE document_sequence SET value=:value WHERE name=:name AND period=:period'), {
            'value': start + count - 1, 'name': name, 'period': period
        })
        connection.commit()
        return list(range(start, start + count))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def register_routes(app):
    register_smtp_settings_routes(app, role_required, limiter)
    register_customer_routes(app, role_required, require_current_role)
    register_plate_size_routes(app, role_required)
    register_invoice_routes(app, role_required, require_current_role, reserve_document_sequences, limiter, mail, smtp_credentials)
    register_challan_routes(app, role_required, require_current_role, reserve_document_sequences)
    register_inventory_routes(app, role_required, require_current_role)
    register_account_routes(app, role_required, limiter)
    register_archive_routes(app, role_required)
    register_print_routes(app, role_required)

    @app.route('/api/')
    def home():
        return render_template_string("<h1>Welcome to the Inventory Management App</h1>")

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # Dynamically locate the dist folder relative to the executable
        if getattr(sys, 'frozen', False):  # Check if running as a PyInstaller executable
            dist_folder = os.path.join(sys._MEIPASS, 'dist')
        else:
            dist_folder = os.path.join(os.path.dirname(__file__), '..', 'dist')

        # print(f"Dist folder path: {dist_folder}")  # Debugging: Print the dist folder path
        if path != "" and os.path.exists(os.path.join(dist_folder, path)):
            return send_from_directory(dist_folder, path)
        else:
            return send_from_directory(dist_folder, 'index.html')
