import os
from functools import wraps
import jwt
from flask import request, jsonify, g
from models import User

ROLE_STUDENT = "student"
ROLE_REFERENT = "referent"
ROLE_OVERSEAS = "staff"


def normalize_role(role):
    if not role:
        return None
    return role.strip().lower().replace(" ", "_")


def _get_jwt_secret():
    return os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")


# Decodes JWT and injects User object into Flask 'g' for role-based access control.
def custom_jwt_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "missing bearer token"}), 401

            token = auth_header.split(" ", 1)[1].strip()
            secret = _get_jwt_secret()
            if not secret:
                return jsonify({"error": "JWT secret not configured"}), 500

            try:
                payload = jwt.decode(token, secret, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "invalid token"}), 401

            user_id = payload.get("sub")
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                return jsonify({"error": "token user id invalid"}), 401

            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "user not found"}), 401

            # save data in the object 'g' in flask for the current request
            g.current_user = user
            g.current_user_id = user.id
            g.current_user_role = normalize_role(user.role)
            g.jwt_payload = payload

            return f(*args, **kwargs)

        return decorated_function

    return decorator
