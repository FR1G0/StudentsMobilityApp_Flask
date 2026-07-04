import datetime
import jwt
from flask import Blueprint, jsonify, request, current_app, g
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db
from auth import ROLE_OVERSEAS, custom_jwt_required, require_roles, _get_jwt_secret
from routes.api import extract_db_error

users_blueprint = Blueprint("users", __name__)

# returns true if user_id belongs to the id_institution, false otherwise
def user_in_institution(user,param_id_institution):
    try:
        # if user is null, return false, if param_id is missing, the second return handles it correctly
        if not user:
            return False;
        return user.id_institution == param_id_institution
    except Exception as e:
        return False;


# OK: [POST] /login
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


# OK: [GET] /user
# returns the list of all the users inside the same institution as the staff
@users_blueprint.route("/user", methods=["GET"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def all_users():
    try:
        staff_user = g.current_user
        users = User.query.filter_by(id_institution=staff_user.id_institution)
        result = []
        for user in users:
            result.append(user.to_dict())
        return jsonify(result), 200
    except Exception as e:
        msg = extract_db_error(e)
        return jsonify({"error": msg}), 500


# OK: [GET] /user/:id
# returns the information of the row users using the users' id
@users_blueprint.route("/user/<int:id>", methods=["GET"])
@custom_jwt_required()
def get_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({"error": "user not found"}), 404
        if not user_in_institution(g.current_user, user.id_institution):
            return jsonify({"error": "access restricted"}), 404

        result = {
            "id": user.id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "role": user.role,
            "id_institution": user.id_institution,
        }
        return jsonify(result), 200
    except Exception as e:
        msg = extract_db_error(e)
        return jsonify({"error": msg}), 500


# OK: [POST] /user/insert
# inserts a new user row into the database using the json body data
@users_blueprint.route("/user/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def insert_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        if not user_in_institution(g.current_user, data.get("id_institution")):
            return jsonify({"status": "failed", "error": "restricted access to this user"}), 403

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
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500


# OK: [POST] /user/update
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
        if user.role == 'staff':
            return jsonify({"status": "failed", "error": "unauthorized access, higher privilege required for modifying staff rows"}), 403

        if not user_in_institution(g.current_user, user.id_institution):
            return jsonify({"status": "failed", "error": "restricted access to this user"}), 403

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
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500


# OK: [POST] /user/delete/:id
# deletes the user row identified by :id
@users_blueprint.route("/user/delete/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def delete_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({"status": "failed", "error": "user not found"}), 404

        if user.role == 'staff':
            return jsonify({"status": "failed", "error": "you can't delete staff members, higher authority required"}), 403

        if not user_in_institution(g.current_user, user.id_institution):
            return jsonify({"status": "failed", "error": "restricted access to this user"}), 403

        db.session.delete(user)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500

#   -------  USER INFO SECTION  -------

# OK: [GET] /user/info/role
# returns the list of allowed user roles
@users_blueprint.route("/user/info/role", methods=["GET"])
def get_user_roles():
    roles = ["student", "referent", "staff"]
    return jsonify(roles), 200
