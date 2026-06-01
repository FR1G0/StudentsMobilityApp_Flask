from flask import Blueprint, jsonify, request
from models import db, User, Application

applications_blueprint = Blueprint("applications", __name__)

ROLE_STUDENT = "student"
ROLE_REFERENT = "referent"
ROLE_OVERSEAS = "overseas_staff"


def normalize_role(role):
    if not role:
        return None
    return role.strip().lower().replace(" ", "_")


@applications_blueprint.route("/applications", methods=["GET"])
def list_applications():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    role = normalize_role(user.role)
    if role == ROLE_STUDENT:
        applications = Application.query.filter_by(user_id=user.id).all()
    elif role == ROLE_REFERENT:
        applications = Application.query.filter_by(referent_id=user.id).all()
    elif role == ROLE_OVERSEAS:
        applications = Application.query.filter_by(host_institution=user.id_institution).all()
    else:
        return jsonify({"error": "role not authorized"}), 403

    return jsonify([app.to_dict() for app in applications]), 200


@applications_blueprint.route("/applications/<int:application_id>", methods=["PATCH"])
def update_application(application_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    application = Application.query.get(application_id)
    if not application:
        return jsonify({"error": "application not found"}), 404

    role = normalize_role(user.role)
    if role == ROLE_OVERSEAS:
        return jsonify({"error": "overseas staff cannot modify applications"}), 403
    if role == ROLE_STUDENT and application.user_id != user.id:
        return jsonify({"error": "student cannot modify this application"}), 403
    if role == ROLE_REFERENT and application.referent_id != user.id:
        return jsonify({"error": "referent cannot modify this application"}), 403
    if role not in {ROLE_STUDENT, ROLE_REFERENT}:
        return jsonify({"error": "role not authorized"}), 403

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "request body is required"}), 400

    allowed_fields = {
        "year",
        "semester",
        "status",
        "sending_institution",
        "host_institution",
        "referent_id",
    }
    unknown_fields = set(payload.keys()) - allowed_fields
    if unknown_fields:
        return jsonify({"error": f"unknown fields: {', '.join(sorted(unknown_fields))}"}), 400

    for field, value in payload.items():
        if field in {"year", "sending_institution", "host_institution", "referent_id"}:
            if not isinstance(value, int):
                return jsonify({"error": f"{field} must be an integer"}), 400
            setattr(application, field, value)
            continue
        setattr(application, field, value)

    db.session.commit()
    return jsonify(application.to_dict()), 200
