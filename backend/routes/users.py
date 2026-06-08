from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint, blueprints, jsonify, request
from models import db, User
from ..auth import custom_jwt_required

# define blueprinty
users_blueprint = Blueprint("users", __name__)


# fetch all users
@users_blueprint.route("/user", methods=["GET"])
@custom_jwt_required()
def all_users():
    try:
        users = User.query.all()
        all_u = []
        for u in users:
            all_u.append(u.to_dict())
        return jsonify(all_u), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# fetch user by id
@users_blueprint.route("/user/<int:id>", methods=["GET"])
@custom_jwt_required()
def get_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({}), 500
        return user.to_dict(), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# fetch user by firstname
@users_blueprint.route("/user/name:<string:name>", methods=["GET"])
@custom_jwt_required()
def get_user_by_name(name):
    try:
        name = name.lower()
        # WARN: raw sql query
        result = db.session.execute(
            db.text("SELECT * FROM users WHERE LOWER(firstname) = :name"),
            {"name": name},
        )
        data = result.fetchall()
        users = []
        if not data:
            return jsonify({}), 500
        # raw data assembling
        for u in data:
            users.append(
                {
                    "id": u.id,
                    "email": u.email,
                    "role": u.role,
                    "firstname": u.firstname,
                    "lastname": u.lastname,
                }
            )
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# fetch user by firstname and lastname
@users_blueprint.route("/user/<string:name>/<string:surname>", methods=["GET"])
@custom_jwt_required()
def get_user_by_email(name, surname):
    try:
        name = name.lower()
        surname = surname.lower()
        user = User.query.filter(
            (User.firstname == name) & (User.lastname == surname)
        ).first()
        if not user:
            return jsonify({}), 500
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
