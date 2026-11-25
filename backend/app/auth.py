"""Shared authentication and role authorization decorators."""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from .models import User


def role_required(required_roles):
    allowed_roles = frozenset(required_roles)

    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = User.query.get(get_jwt_identity())
            if not user or not user.is_active or user.role not in allowed_roles:
                return jsonify({'message': 'Access denied'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_current_role(*roles):
    user = User.query.get(get_jwt_identity())
    return bool(user and user.is_active and user.role in roles)
