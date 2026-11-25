"""Helpers for recording security relevant state changes."""
from flask_jwt_extended import get_jwt_identity

from . import db
from .models import AuditLog


def record_audit_event(action, entity_type, entity_id):
    identity = get_jwt_identity()
    try:
        actor_id = int(identity) if identity is not None else None
    except (TypeError, ValueError):
        actor_id = None
    db.session.add(AuditLog(
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
    ))
