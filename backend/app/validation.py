"""Small request validation helpers shared by API domains."""
from flask import request


def json_object():
    """Return the JSON object body or None for missing/non-object JSON."""
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def bounded_text(value, maximum, *, required=False):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        return None
    return value
