from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g
from sqlalchemy import text

from auth import (
    ROLE_OVERSEAS,
    ROLE_REFERENT,
    ROLE_STUDENT,
    can_view_application,
    custom_jwt_required,
    require_roles,
)
from models import db, Exam, MappedExam, Application, UploadedDocument
from routes.users import user_in_institution
from routes.api import extract_db_error

exams_blueprint = Blueprint("exams", __name__)


# OK: [GET] /exam/list/:id_institution
# returns the list of exam rows that belong to the given institution
@exams_blueprint.route("/exam/list/<int:id_inst>", methods=["GET"])
@custom_jwt_required()
def list_exams_by_institution(id_inst):
    try:
        exams = Exam.query.filter_by(id_institution=id_inst).all()
        result = []
        for exam in exams:
            result.append(exam.to_dict())
        return jsonify(result), 200
    except Exception as e:
        msg = extract_db_error(e)
        return jsonify({"error": msg}), 500


# OK: [GET] /exam/:id
# returns the information of the exam row with the given id
@exams_blueprint.route("/exam/<int:id>", methods=["GET"])
@custom_jwt_required()
def get_exam(id):
    try:
        exam = Exam.query.get(id)
        if not exam:
            return jsonify({"error": "exam not found"}), 404
        return jsonify(exam.to_dict()), 200
    except Exception as e:
        msg = extract_db_error(e)
        return jsonify({"error": msg}), 500


# OK: [POST] /exam/insert
# inserts a new exam row using the json body data
@exams_blueprint.route("/exam/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def insert_exam():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        # validate user access
        if not user_in_institution(g.current_user, data.get("id_institution")):
            return jsonify({"status": "failed", "error": "access restricted"}), 403

        new_exam = Exam(
            code=data.get("code"),
            name=data.get("name"),
            credits=data.get("credits"),
            id_institution=data.get("id_institution"),
        )
        db.session.add(new_exam)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500


# OK: [POST] /exam/delete/:id
# deletes the exam row identified by :id
@exams_blueprint.route("/exam/delete/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def delete_exam(id):
    try:
        exam = Exam.query.get(id)
        if not exam:
            return jsonify({"status": "failed", "error": "exam not found"}), 404

        # validate user access
        if not user_in_institution(g.current_user, exam.id_institution):
            return jsonify({"status": "failed", "error": "access restricted"}), 403

        db.session.delete(exam)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500

#   -------  EXAM MAPPING SECTION  -------

# TEST: [POST] /exam/mapping/insert/:application_id
# inserts a new mapped_exams row linking a host exam and a sending exam for an application
@exams_blueprint.route("/exam/mapping/insert/<int:application_id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def insert_mapped_exam(application_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        application = Application.query.get(application_id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify({"status": "failed", "error": "cannot add a mapping to this application"}), 403

        new_mapping = MappedExam(
            application_id=application_id,
            host_exam_id=data.get("host_exam_id"),
            sending_exam_id=data.get("sending_exam_id"),
            notes=data.get("notes", ""),
        )

        db.session.add(new_mapping)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500


# OK: [POST] /exam/mapping/delete/:id
# deletes the mapped_exams row identified by :id
@exams_blueprint.route("/exam/mapping/delete/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def delete_mapped_exam(id):
    try:
        mapping = MappedExam.query.get(id)
        if not mapping:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404

        application = Application.query.get(mapping.application_id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify( {"status": "failed", "error": "cannot remove a mapping to this application"}), 403
        # TODO : should we also check if such operation is allowed? as in if the application is in "ongoing" the mapped exam shouldn't be changed, but my concerns are related to the fact that maybe LamodifcationExam is in charge of such operation

        db.session.delete(mapping)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500


# NOTE: [POST] /exam/mapping/:id/decision
@exams_blueprint.route("/exam/mapping/<int:id>/decision", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_REFERENT)
def update_mapped_exam_status(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        mapping = MappedExam.query.get(id)
        if not mapping:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404

        application = Application.query.get(mapping.application_id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify( {"status": "failed", "error": "cannot decide on this exam"}), 403

        if "status" in data:
            mapping.status = data["status"]
        if "notes" in data:
            mapping.notes = data["notes"]
        mapping.decision_date = datetime.now(timezone.utc)

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500




# OK: [POST] /exam/mapping/passed/:id
# registers grade and date_passed on the mapped_exam row of given id
@exams_blueprint.route("/exam/mapping/passed/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def set_mapped_exam_passed(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        mapping = MappedExam.query.get(id)
        if not mapping:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404

        application = Application.query.get(mapping.application_id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify({"status": "failed", "error": "cannot modify this application"}), 403

        # an approved exam is locked: its grade/date cannot be changed anymore
        if mapping.status == "approved":
            return jsonify({"status": "failed", "error": "approved exam cannot be modified"}), 403

        # grade/date can be entered only after the Transcript of Records is uploaded
        transcript_exists = UploadedDocument.query.filter_by(
            application_id=application.id, document_type="transcript"
        ).first()
        if not transcript_exists:
            return jsonify({"status": "failed", "error": "transcript of records not uploaded yet, please upload the transcript of records"}), 400

        if "grade" in data:
            mapping.grade = data["grade"]
        if "date_passed" in data:
            date_value = data["date_passed"]
            if date_value is None:
                mapping.date_passed = None
            else:
                mapping.date_passed = datetime.fromisoformat(date_value).date()

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500


# OK: [GET] /exam/mapped/info/status
# returns the list of allowed status values for mapped exams
@exams_blueprint.route("/exam/mapped/info/status", methods=["GET"])
def get_mapped_exam_status_values():
    statuses = ["pending", "approved", "rejected"]
    return jsonify(statuses), 200
