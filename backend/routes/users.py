import datetime
import jwt
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db
from auth import ROLE_OVERSEAS, custom_jwt_required, require_roles, _get_jwt_secret

users_blueprint = Blueprint("users", __name__)


# NOTE: [POST] /login
# authenticates a user and returns a JWT token along with the user info
@users_blueprint.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "missing credentials"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    # password_hash stores a werkzeug hash (pbkdf2). Constant-time verify.
    if not user or not check_password_hash(user.password_hash, data["password"]):
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


# NOTE: [GET] /user
# returns the list of all the users inside the database
@users_blueprint.route("/user", methods=["GET"])
@custom_jwt_required()
def all_users():
    try:
        users = User.query.all()
        result = []
        for user in users:
            result.append(user.to_dict())
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# NOTE: [GET] /user/:id
# returns the information of the row users using the users' id
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


# NOTE: [GET] /user/name:<name>
# returns the list of users whose firstname matches the given name
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

        users = []
        for row in result:
            users.append({
                "id": row["id"],
                "email": row["email"],
                "role": row["role"],
                "firstname": row["firstname"],
                "lastname": row["lastname"],
            })
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# NOTE: [GET] /user/:name/:surname
# returns a single user matching firstname and lastname
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


# NOTE: [POST] /user/insert
# inserts a new user row into the database using the json body data
@users_blueprint.route("/user/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def insert_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        # accept "password" (preferred) or legacy "password_hash" as the raw secret
        raw_password = data.get("password") or data.get("password_hash")
        if not raw_password:
            return jsonify({"status": "failed", "error": "missing password"}), 400

        new_user = User(
            email=data.get("email"),
            password_hash=generate_password_hash(raw_password, method="pbkdf2:sha256"),
            role=data.get("role"),
            firstname=data.get("firstname"),
            lastname=data.get("lastname"),
            id_institution=data.get("id_institution"),
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /user/update
# updates an existing user row using the json body data (must contain "id")
@users_blueprint.route("/user/update", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def update_user():
    try:
        data = request.get_json()
        if not data or not data.get("id"):
            return jsonify({"status": "failed", "error": "missing id"}), 400

        user = User.query.get(data["id"])
        if not user:
            return jsonify({"status": "failed", "error": "user not found"}), 404

        if "email" in data:
            user.email = data["email"]
        if "password" in data:
            user.password_hash = generate_password_hash(data["password"], method="pbkdf2:sha256")
        elif "password_hash" in data:
            user.password_hash = generate_password_hash(data["password_hash"], method="pbkdf2:sha256")
        if "firstname" in data:
            user.firstname = data["firstname"]
        if "lastname" in data:
            user.lastname = data["lastname"]
        if "id_institution" in data:
            user.id_institution = data["id_institution"]

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /user/delete/:id
# deletes the user row identified by :id
# WARNING: must be protected
@users_blueprint.route("/user/delete/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def delete_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({"status": "failed", "error": "user not found"}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [GET] /user/info/role
# returns the list of allowed user roles
@users_blueprint.route("/user/info/role", methods=["GET"])
def get_user_roles():
    roles = ["student", "referent", "staff"]
    return jsonify(roles), 200
