from flask import Blueprint, jsonify, request, g

from ..auth import (
    ROLE_OVERSEAS,
    ROLE_REFERENT,
    ROLE_STUDENT,
    custom_jwt_required,
)
from models import db, Application

applications_blueprint = Blueprint("applications", __name__)


@applications_blueprint.route("/applications", methods=["GET"])
@custom_jwt_required()
def list_applications():
    user = g.current_user
    role = g.current_user_role
    if role == ROLE_STUDENT:
        applications = Application.query.filter_by(user_id=user.id).all()
    elif role == ROLE_REFERENT:
        applications = Application.query.filter_by(referent_id=user.id).all()
    elif role == ROLE_OVERSEAS:
        applications = Application.query.filter_by(
            host_institution=user.id_institution
        ).all()
    else:
        return jsonify({"error": "role not authorized"}), 403

    return jsonify([app.to_dict() for app in applications]), 200


@applications_blueprint.route("/applications/<int:application_id>", methods=["PATCH"])
@custom_jwt_required()
def update_application(application_id):
    user = g.current_user

    application = Application.query.get(application_id)
    if not application:
        return jsonify({"error": "application not found"}), 404

    role = g.current_user_role
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
    # checks that no unexistent fields get passed
    if unknown_fields:
        return jsonify(
            {"error": f"unknown fields: {', '.join(sorted(unknown_fields))}"}
        ), 400

    for field, value in payload.items():
        if field in {"year", "sending_institution", "host_institution", "referent_id"}:
            if not isinstance(value, int):
                return jsonify({"error": f"{field} must be an integer"}), 400
            setattr(application, field, value)
            continue
        setattr(application, field, value)

    db.session.commit()
    return jsonify(application.to_dict()), 200
