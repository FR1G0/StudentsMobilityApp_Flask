import datetime
import jwt
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text

from models import User, db
from auth import custom_jwt_required, _get_jwt_secret

users_blueprint = Blueprint("users", __name__)


@users_blueprint.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "missing credentials"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    # NOTE: In real app, use password hashing (e.g., bcrypt)
    # Here checking against plain password_hash for simplicity
    if not user or user.password_hash != data["password"]:
        return jsonify({"error": "invalid credentials"}), 401

    secret = _get_jwt_secret()
    if not secret:
        return jsonify({"error": "JWT secret not configured"}), 500

    payload = {
        "sub": user.id,
        "role": user.role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return jsonify({"token": token, "user": user.to_dict()}), 200


@users_blueprint.route("/user", methods=["GET"])
@custom_jwt_required()
def all_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@users_blueprint.route("/user/<int:id>", methods=["GET"])
@custom_jwt_required()
def get_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({"error": "user not found"}), 404
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@users_blueprint.route("/user/name:<string:name>", methods=["GET"])
@custom_jwt_required()
def get_user_by_name(name):
    try:
        result = (
            db.session.execute(
                text("SELECT * FROM users WHERE LOWER(firstname) = :name"),
                {"name": name.lower()},
            )
            .mappings()
            .all()
        )
        if not result:
            return jsonify({"error": "user not found"}), 404

        return (
            jsonify(
                [
                    {
                        "id": row["id"],
                        "email": row["email"],
                        "role": row["role"],
                        "firstname": row["firstname"],
                        "lastname": row["lastname"],
                    }
                    for row in result
                ]
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@users_blueprint.route("/user/<string:name>/<string:surname>", methods=["GET"])
@custom_jwt_required()
def get_user_by_email(name, surname):
    try:
        user = User.query.filter(
            (User.firstname == name.lower()) & (User.lastname == surname.lower())
        ).first()
        if not user:
            return jsonify({"error": "user not found"}), 404
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
