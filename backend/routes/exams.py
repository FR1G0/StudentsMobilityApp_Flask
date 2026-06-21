from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from auth import (
    ROLE_OVERSEAS,
    ROLE_REFERENT,
    custom_jwt_required,
    require_roles,
)
from models import db, Exam, MappedExam

exams_blueprint = Blueprint("exams", __name__)


# NOTE: [GET] /exam/list/:id_institution
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
        return jsonify({"error": str(e)}), 500


# NOTE: [GET] /exam/:id
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
        return jsonify({"error": str(e)}), 500


# NOTE: [POST] /exam/insert
# inserts a new exam row using the json body data
@exams_blueprint.route("/exam/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def insert_exam():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

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
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /exam/delete/:id
# deletes the exam row identified by :id
@exams_blueprint.route("/exam/delete/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def delete_exam(id):
    try:
        exam = Exam.query.get(id)
        if not exam:
            return jsonify({"status": "failed", "error": "exam not found"}), 404
        db.session.delete(exam)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /exam/mapping/insert/:application_id
# inserts a new mapped_exams row linking a host exam and a sending exam for an application
@exams_blueprint.route("/exam/mapping/insert/<int:application_id>", methods=["POST"])
@custom_jwt_required()
def insert_mapped_exam(application_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        new_mapping = MappedExam(
            application_id=application_id,
            host_exam_id=data.get("host_exam_id"),
            sending_exam_id=data.get("sending_exam_id"),
            notes=data.get("notes", ""),
        )
        if "previous_id" in data:
            new_mapping.previous_id = data["previous_id"]

        db.session.add(new_mapping)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /exam/mapping/delete/:id
# deletes the mapped_exams row identified by :id
@exams_blueprint.route("/exam/mapping/delete/<int:id>", methods=["POST"])
@custom_jwt_required()
def delete_mapped_exam(id):
    try:
        mapping = MappedExam.query.get(id)
        if not mapping:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404
        db.session.delete(mapping)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /exam/mapping/update/:id
# updates the status of the mapped_exam row of given id (e.g. approved/rejected) and decision info
@exams_blueprint.route("/exam/mapping/update/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_REFERENT, ROLE_OVERSEAS)
def update_mapped_exam_status(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        mapping = MappedExam.query.get(id)
        if not mapping:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404

        if "status" in data:
            mapping.status = data["status"]
        if "notes" in data:
            mapping.notes = data["notes"]
        mapping.decision_date = datetime.now(timezone.utc)

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /exam/mapping/passed/:id
# registers grade and date_passed on the mapped_exam row of given id
@exams_blueprint.route("/exam/mapping/passed/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_REFERENT, ROLE_OVERSEAS)
def set_mapped_exam_passed(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        mapping = MappedExam.query.get(id)
        if not mapping:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404

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
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [GET] /exam/mapped/info/status
# returns the list of allowed status values for mapped exams
@exams_blueprint.route("/exam/mapped/info/status", methods=["GET"])
def get_mapped_exam_status_values():
    statuses = ["pending", "approved", "rejected"]
    return jsonify(statuses), 200
