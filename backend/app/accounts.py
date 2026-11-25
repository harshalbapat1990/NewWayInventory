"""Session, password and user administration endpoints."""
from datetime import datetime
import hmac

from flask import current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, decode_token, get_jwt,
    get_jwt_identity, jwt_required, set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies,
)
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .audit import record_audit_event
from .models import RevokedToken, User
from .validation import json_object


def register_account_routes(app, role_required, limiter):
    @app.route('/api/register', methods=['POST'])
    def register():
        return jsonify({"message": "Public registration is disabled"}), 404

    @app.route('/api/login', methods=['POST'])
    @limiter.limit('10 per 15 minutes')
    def login():
        data = json_object()
        if data is None:
            return jsonify({'message': 'Credentials must be provided as an object'}), 400
        username, password = str(data.get('username', ''))[:80], data.get('password', '')
        if not isinstance(password, str) or len(password) > 256:
            return jsonify({"message": "Invalid credentials"}), 401
        user = User.query.filter_by(username=username).first()
        if user and user.is_active and password and check_password_hash(user.password, password):
            if user.password.startswith('pbkdf2:'):
                user.password = generate_password_hash(password, method='scrypt')
                db.session.commit()
            token_claims = {"auth_version": user.auth_version}
            access = create_access_token(identity=str(user.id), additional_claims=token_claims)
            refresh = create_refresh_token(identity=str(user.id), additional_claims=token_claims)
            response = jsonify(user={"id": user.id, "username": user.username, "first_name": user.first_name, "last_name": user.last_name, "role": user.role})
            set_access_cookies(response, access)
            set_refresh_cookies(response, refresh)
            return response, 200
        return jsonify({"message": "Invalid credentials"}), 401

    # Add this new refresh token endpoint
    @app.route('/api/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        claims = get_jwt()
        user = User.query.get(get_jwt_identity())
        if not user:
            return jsonify({"message": "Unauthorized"}), 401
        db.session.add(RevokedToken(jti=claims['jti'], expires_at=datetime.fromtimestamp(claims['exp'])))
        token_claims = {"auth_version": user.auth_version}
        access = create_access_token(identity=str(user.id), additional_claims=token_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=token_claims)
        response = jsonify({"message": "Session refreshed"})
        set_access_cookies(response, access)
        set_refresh_cookies(response, refresh_token)
        db.session.commit()
        return response, 200

    @app.route('/api/users', methods=['GET', 'POST'])
    @role_required(['admin'])
    def manage_users():
        if request.method == 'GET':
            return jsonify([{"id": u.id, "username": u.username, "first_name": u.first_name, "last_name": u.last_name, "role": u.role, "is_active": u.is_active} for u in User.query.order_by(User.username).all()])
        data = json_object()
        if data is None:
            return jsonify({'message': 'User data must be an object'}), 400
        required = ('username', 'password', 'first_name', 'last_name', 'role')
        if any(not isinstance(data.get(k), str) or not data[k].strip() for k in required):
            return jsonify({"message": "All user fields are required"}), 400
        if (len(data['username'].strip()) > 80 or len(data['first_name'].strip()) > 50
                or len(data['last_name'].strip()) > 50):
            return jsonify({"message": "Username and name fields exceed their maximum lengths"}), 400
        if not 12 <= len(data['password']) <= 256 or data['role'] not in ('admin', 'editor', 'accountant', 'user'):
            return jsonify({"message": "Password must be at least 12 characters and role must be valid"}), 400
        if User.query.filter_by(username=data['username'].strip()).first():
            return jsonify({"message": "Username is already in use"}), 409
        user = User(username=data['username'].strip(), password=generate_password_hash(data['password'], method='scrypt'), first_name=data['first_name'].strip(), last_name=data['last_name'].strip(), role=data['role'], is_active=True)
        db.session.add(user)
        db.session.flush()
        record_audit_event('user.created', 'user', user.id)
        db.session.commit()
        return jsonify({"id": user.id, "username": user.username, "first_name": user.first_name, "last_name": user.last_name, "role": user.role, "is_active": user.is_active}), 201

    @app.route('/api/users/<int:user_id>', methods=['PATCH', 'DELETE'])
    @role_required(['admin'])
    def update_user(user_id):
        user = User.query.get_or_404(user_id)
        if request.method == 'DELETE':
            if user.id == int(get_jwt_identity()):
                return jsonify({"message": "You cannot deactivate your own account"}), 400
            if user.is_active:
                user.auth_version += 1
            user.is_active = False
        else:
            data = json_object()
            if data is None:
                return jsonify({'message': 'User data must be an object'}), 400
            new_role = data.get('role', user.role)
            new_active = data.get('is_active', user.is_active)
            if 'role' in data and (not isinstance(new_role, str) or new_role not in ('admin', 'editor', 'accountant', 'user')):
                return jsonify({"message": "Invalid role"}), 400
            if not isinstance(new_active, bool):
                return jsonify({"message": "is_active must be boolean"}), 400
            if user.role == 'admin' and user.is_active and (new_role != 'admin' or not new_active):
                active_admins = User.query.filter_by(role='admin', is_active=True).count()
                if active_admins <= 1:
                    return jsonify({"message": "At least one active administrator must remain"}), 409
            if 'role' in data:
                user.role = data['role']
            if 'is_active' in data:
                if user.is_active and not data['is_active']:
                    user.auth_version += 1
                user.is_active = data['is_active']
            if 'password' in data:
                if not isinstance(data['password'], str) or not 12 <= len(data['password']) <= 256:
                    return jsonify({"message": "Password must be 12 to 256 characters"}), 400
                user.password = generate_password_hash(data['password'], method='scrypt')
                user.auth_version += 1
        record_audit_event('user.updated', 'user', user.id)
        db.session.commit()
        return jsonify({"message": "User updated"}), 200

    @app.route('/api/logout', methods=['POST'])
    def logout():
        csrf_header = request.headers.get('X-CSRF-TOKEN', '')
        csrf_cookies = (request.cookies.get('csrf_access_token', ''), request.cookies.get('csrf_refresh_token', ''))
        has_session = any(request.cookies.get(name) for name in (app.config['JWT_ACCESS_COOKIE_NAME'], app.config['JWT_REFRESH_COOKIE_NAME']))
        if has_session and not any(value and hmac.compare_digest(value, csrf_header) for value in csrf_cookies):
            return jsonify({"message": "CSRF validation failed"}), 403
        for cookie_name in (app.config['JWT_ACCESS_COOKIE_NAME'], app.config['JWT_REFRESH_COOKIE_NAME']):
            token = request.cookies.get(cookie_name)
            if token:
                try:
                    payload = decode_token(token, allow_expired=True)
                    if not RevokedToken.query.filter_by(jti=payload['jti']).first():
                        db.session.add(RevokedToken(jti=payload['jti'], expires_at=datetime.fromtimestamp(payload['exp'])))
                except Exception:
                    pass
        db.session.commit()
        response = jsonify({"message": "Logged out"})
        unset_jwt_cookies(response)
        return response

    @app.route('/api/user-details', methods=['GET'])
    @jwt_required()
    def get_user_details():
        user_record = User.query.get(get_jwt_identity())
        if not user_record:
            return jsonify({"message": "User not found"}), 404
        return jsonify({
            "id": user_record.id,
            "username": user_record.username,
            "first_name": user_record.first_name,
            "last_name": user_record.last_name,
            "role": user_record.role
        }), 200
    
    @app.route('/api/reset-password', methods=['POST'])
    @jwt_required()
    def reset_password():
        data = json_object()
        if data is None:
            return jsonify({'message': 'Password data must be an object'}), 400
        user_record = User.query.get(get_jwt_identity())
        if not user_record:
            return jsonify({"message": "User not found"}), 404

        new_password = data.get('new_password')
        current_password = data.get('current_password')
        if not isinstance(current_password, str) or len(current_password) > 256 or not check_password_hash(user_record.password, current_password):
            return jsonify({"message": "Current password is incorrect"}), 400
        if not isinstance(new_password, str) or not 12 <= len(new_password) <= 256:
            return jsonify({"message": "Password must be 12 to 256 characters long"}), 400

        user_record.password = generate_password_hash(new_password, method='scrypt')
        user_record.auth_version += 1
        record_audit_event('user.password_changed', 'user', user_record.id)
        db.session.commit()
        response = jsonify({"message": "Password changed. Please sign in again."})
        unset_jwt_cookies(response)
        return response, 200

