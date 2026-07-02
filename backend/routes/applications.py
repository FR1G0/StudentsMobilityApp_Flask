import os
from datetime import datetime, date, timezone

from flask import Blueprint, jsonify, request, g, current_app, send_file

from auth import (
    ROLE_OVERSEAS,
    ROLE_REFERENT,
    ROLE_STUDENT,
    can_view_application,
    custom_jwt_required,
    require_roles,
)
from models import db, Application, User, Institution, UploadedDocument, MappedExam

applications_blueprint = Blueprint("applications", __name__)


UPLOADS_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "uploads",
    "applications",
)


def _application_upload_dir(application_id):
    return os.path.join(UPLOADS_BASE_DIR, str(application_id))


# OK: [GET] /applications
# returns the list of applications visible to the current user based on role
@applications_blueprint.route("/applications", methods=["GET"])
@custom_jwt_required()
def list_applications():
    # Multitenancy: filter results based on user role to ensure data isolation.
    # Students see own data; Staff/Referents see data scoped to their institution.
    user = g.current_user
    role = g.current_user_role
    if role == ROLE_STUDENT:
        applications = Application.query.filter_by(user_id=user.id).all()
    elif role == ROLE_REFERENT:
        applications = Application.query.filter_by(referent_id=user.id).all()
    elif role == ROLE_OVERSEAS:
        applications = Application.query.filter_by(
            sending_institution=user.id_institution
        ).all()
    else:
        return jsonify({"error": "role not authorized"}), 403

    result = []
    for app in applications:
        result.append(app.to_dict())
    return jsonify(result), 200


# TEST: [POST] /application/insert
# creates a new application row (student only) and prepares its uploads directory
@applications_blueprint.route("/application/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def insert_application():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        new_app = Application(
            year=data.get("year"),
            semester=data.get("semester"),
            status=data.get("status", "created"),
            notes=data.get("notes", ""),
            referent_id=data.get("referent_id"),
            sending_institution=data.get("sending_institution"),
            host_institution=data.get("host_institution"),
            user_id=g.current_user_id,
        )
        db.session.add(new_app)
        db.session.commit()

        upload_dir = _application_upload_dir(new_app.id)
        os.makedirs(upload_dir, exist_ok=True)

        return jsonify({"status": "success", "id": new_app.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# OK: [POST] /application/update/:id
# updates the editable fields of an application (student, own application only).
# status is intentionally excluded: it has its own workflow route.
@applications_blueprint.route("/application/update/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def post_update_application(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        application = Application.query.get(id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404

        # a student may only edit their own application
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify({"status": "failed", "error": "cannot modify this application"}), 403

        # only these fields may be changed here; reject anything else
        allowed_fields = {
            "year",
            "semester",
            "notes",
            "referent_id",
            "sending_institution",
            "host_institution",
            "date_arrived",
            "date_departure",
        }
        unknown_fields = set(data.keys()) - allowed_fields
        if unknown_fields:
            return jsonify({"status": "failed", "error": "unknown fields: " + ", ".join(sorted(unknown_fields))}), 400

        integer_fields = {"year", "referent_id", "sending_institution", "host_institution"}
        date_fields = {"date_arrived", "date_departure"}

        for field in data:
            value = data[field]
            if field in integer_fields:
                if not isinstance(value, int):
                    return jsonify({"status": "failed", "error": field + " must be an integer"}), 400
                setattr(application, field, value)
            elif field in date_fields:
                if value is None:
                    setattr(application, field, None)
                else:
                    try:
                        parsed_date = datetime.fromisoformat(value).date()
                    except (ValueError, TypeError):
                        return jsonify({"status": "failed", "error": field + " must be an ISO-8601 date"}), 400
                    setattr(application, field, parsed_date)
            else:
                setattr(application, field, value)

        try:
            db.session.commit()
        except Exception as e:
            # DB triggers/constraints enforce workflow rules; surface them as a 400
            db.session.rollback()
            return jsonify({"status": "failed", "error": str(e)}), 400

        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500

# NOTE: [POST] /application/status/update/:id
# updates the application status, following a very specific workflow 
@applications_blueprint.route("/application/status/update/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT, ROLE_REFERENT, ROLE_OVERSEAS)
def update_status_application(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        # this route only moves the status, so it must always be present
        if "status" not in data:
            return jsonify({"status": "failed", "error": "missing status"}), 400

        application = Application.query.get(id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404

        role = g.current_user_role
        if not can_view_application(application, g.current_user, role):
            return jsonify( {"status": "failed", "error": "cannot modify this application"}), 403

        if role == ROLE_STUDENT:
            if data["status"] not in ("mobility_ongoing", "exam_recognition"):
                return jsonify({"status": "failed", "error": "student cannot set this status"}), 403

        # check referent
        if role == ROLE_REFERENT:
            referent_allowed_fields = {"status", "notes"}
            if set(data.keys()) - referent_allowed_fields:
                return jsonify({"status": "failed", "error": "referent can only change status"}), 403
            if data["status"] not in ("created", "learning_agreement_pending"):
                return jsonify({"status": "failed", "error": "referent cannot set this status"}), 403

        # check staff
        if role == ROLE_OVERSEAS:
            overseas_allowed_fields = {"status"}
            if set(data.keys()) - overseas_allowed_fields:
                return jsonify({"status": "failed", "error": "staff can only change status"}), 403
            if data["status"] not in ("pre_departure_completed", "closed"):
                return jsonify({"status": "failed", "error": "staff cannot set this status"}), 403

        application.status = data["status"]
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# OK: [POST] /application/delete/:id
# deletes the application row identified by :id (student and staff only), both student and staff can delete applications
@applications_blueprint.route("/application/delete/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT, ROLE_OVERSEAS)
def delete_application(id):
    try:
        application = Application.query.get(id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404

        # students delete only their own; staff only apps hosted by their institution
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify( {"status": "failed", "error": "cannot delete this application"}), 403

        db.session.delete(application)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500

#   -------  APPLICATION INFORMATION SECTION  -------

# OK: [GET] /application/info/semester
# returns the list of allowed semester values
# for frontend
@applications_blueprint.route("/application/info/semester", methods=["GET"])
def get_application_semesters():
    semesters = ["first", "second", "full"]
    return jsonify(semesters), 200


# OK: [GET] /application/info/status
# returns the list of allowed application status values, for frontend
@applications_blueprint.route("/application/info/status", methods=["GET"])
def get_application_statuses():
    statuses = [
        "created",
        "learning_agreement_pending",
        "pre_departure_completed",
        "mobility_ongoing",
        "exam_recognition",
        "closed",
    ]
    return jsonify(statuses), 200


# OK: [GET] /application/info/academic_years, for frontend
# returns the list of academic years starting from the current year for 5 years
@applications_blueprint.route("/application/info/academic_years", methods=["GET"])
def get_application_academic_years():
    current_year = date.today().year
    years = []
    i = 0
    while i < 5:
        years.append(current_year + i)
        i = i + 1
    return jsonify(years), 200

#   -------  DOCUMENT SECTION  -------

# TEST: [POST] /application/documents/:id
# returns the list of all uploaded documents associated to the given application
@applications_blueprint.route("/application/documents/<int:id>", methods=["POST"])
@custom_jwt_required()
def list_application_documents(id):
    try:
        application = Application.query.get(id)
        if not application:
            return jsonify({"error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify({"error": "not authorized for this application"}), 403

        documents = UploadedDocument.query.filter_by(application_id=id).all()
        result = []
        for doc in documents:
            result.append(
                {
                    "id": doc.id,
                    "document_type": doc.document_type,
                    "file_path": doc.file_path,
                    "date_updated": doc.date_updated.isoformat()
                    if doc.date_updated
                    else None,
                    "status": doc.status,
                    "decision_date": doc.decision_date.isoformat()
                    if doc.decision_date
                    else None,
                    "notes": doc.notes,
                    "user_id": doc.user_id,
                    "application_id": doc.application_id,
                }
            )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# OK: [POST] /application/document/insert
# inserts a new uploaded_document **row only** using the json body data
@applications_blueprint.route("/application/document/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def insert_application_document():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        application = Application.query.get(data.get("application_id"))
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify( {"status": "failed", "error": "cannot upload to this application"}), 403

        new_doc = UploadedDocument(
            document_type=data.get("document_type"),
            file_path=data.get("file_path"),
            user_id=data.get("user_id", g.current_user_id),
            application_id=data.get("application_id"),
            notes=data.get("notes", ""),
        )
        db.session.add(new_doc)
        db.session.commit()
        return jsonify({"status": "success", "id": new_doc.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# OK: [POST] /application/document/upload
# uploads a file from form-data ("myfile") into uploads/applications/:application_id/
@applications_blueprint.route("/application/document/upload", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def upload_application_document():
    try:
        application_id = request.form.get("application_id")
        if not application_id:
            return jsonify({"status": "failed", "error": "missing application_id"}), 400

        application = Application.query.get(application_id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify({"status": "failed", "error": "cannot upload to this application"}), 403

        uploaded_file = request.files.get("myfile")
        if not uploaded_file or uploaded_file.filename == "":
            return jsonify({"status": "failed", "error": "missing file"}), 400

        upload_dir = _application_upload_dir(application_id)
        os.makedirs(upload_dir, exist_ok=True)

        filename = os.path.basename(uploaded_file.filename)
        destination = os.path.join(upload_dir, filename)
        uploaded_file.save(destination)

        return jsonify({"status": "success", "file_path": destination}), 200
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500


# OK: [POST] /application/document/:id/delete
# deletes the uploaded file from disk and removes the related document row
@applications_blueprint.route("/application/document/<int:id>/delete", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def delete_application_document(id):
    try:
        doc = UploadedDocument.query.get(id)
        if not doc:
            return jsonify({"status": "failed", "error": "document not found"}), 404

        application = Application.query.get(doc.application_id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify(
                {"status": "failed", "error": "cannot delete this document"}
            ), 403

        file_path = doc.file_path
        application_id = doc.application_id

        if file_path and os.path.isfile(file_path):
            os.remove(file_path)
        else:
            # if file_path is just the filename, try the application uploads dir
            candidate = os.path.join(
                _application_upload_dir(application_id),
                os.path.basename(file_path or ""),
            )
            if os.path.isfile(candidate):
                os.remove(candidate)

        db.session.delete(doc)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# OK: [GET] /application/document/:id/download
# sends the uploaded file back so the frontend can download it, allows anyone that has access to that application to download/view the documents
@applications_blueprint.route("/application/document/<int:id>/download", methods=["GET"])
@custom_jwt_required()
def download_application_document(id):
    doc = UploadedDocument.query.get(id)
    if not doc:
        return jsonify({"error": "document not found"}), 404

    application = Application.query.get(doc.application_id)
    if not application:
        return jsonify({"error": "application not found"}), 404
    if not can_view_application(application, g.current_user, g.current_user_role):
        return jsonify({"error": "not authorized for this document"}), 403

    file_path = doc.file_path
    if not file_path or not os.path.isfile(file_path):
        # if file_path is just the filename, try the application uploads dir
        candidate = os.path.join(
            _application_upload_dir(doc.application_id),
            os.path.basename(file_path or ""),
        )
        if os.path.isfile(candidate):
            file_path = candidate
        else:
            return jsonify({"error": "file not found"}), 404

    return send_file(
        file_path, as_attachment=True, download_name=os.path.basename(file_path)
    )


# OK: (DUPLICATE of line 457) [POST] /application/document/:id/decision
# referent approves or rejects an uploaded document (learning agreement / transcript),
# recording a motivation; decision_date is stamped by a DB trigger
@applications_blueprint.route("/application/document/<int:id>/decision", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_REFERENT, ROLE_OVERSEAS)
def decide_application_document(id):
    try:
        data = request.get_json()
        if not data or "status" not in data:
            return jsonify({"status": "failed", "error": "missing status"}), 400

        new_status = data["status"]
        if new_status not in ("approved", "rejected"):
            return jsonify({"status": "failed", "error": "document status must be approved or rejected"}), 400

        doc = UploadedDocument.query.get(id)
        if not doc:
            return jsonify({"status": "failed", "error": "document not found"}), 404

        application = Application.query.get(doc.application_id)
        if not application:
            return jsonify({"status": "failed", "error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify( {"status": "failed", "error": "restricted access for this application"}), 403

        notes = data.get("notes", "")
        # a rejection must carry a motivation
        if new_status == "rejected" and not (notes and notes.strip()):
            return jsonify({"status": "failed", "error": "rejection requires a motivation"}), 400

        doc.status = new_status
        doc.notes = notes
        # decision_date is set by the set_document_decision_date trigger
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 400


# OK: [GET] /application/exams_mapping/:application_id
# returns the list of mapped_exams rows associated to the given application, anyone with access to the application can view the associated exam mappings.
@applications_blueprint.route("/application/exams_mapping/<int:application_id>", methods=["GET"])
@custom_jwt_required()
def list_application_exam_mappings(application_id):
    try:
        application = Application.query.get(application_id)
        if not application:
            return jsonify({"error": "application not found"}), 404
        if not can_view_application(application, g.current_user, g.current_user_role):
            return jsonify({"error": "not authorized for this application"}), 403

        mappings = MappedExam.query.filter_by(application_id=application_id).all()
        result = []
        for mapping in mappings:
            result.append(
                {
                    "id": mapping.id,
                    "application_id": mapping.application_id,
                    "date_passed": mapping.date_passed.isoformat()
                    if mapping.date_passed
                    else None,
                    "grade": mapping.grade,
                    "status": mapping.status,
                    "decision_date": mapping.decision_date.isoformat()
                    if mapping.decision_date
                    else None,
                    "notes": mapping.notes,
                    "previous_id": mapping.previous_id,
                    "host_exam_id": mapping.host_exam_id,
                    "sending_exam_id": mapping.sending_exam_id,
                }
            )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#   -------  DOCUMENT INFORMATION SECTION  -------

# OK: [GET] /application/document/info/type
# returns the list of allowed document types, for frontend
@applications_blueprint.route("/application/document/info/type", methods=["GET"])
def get_document_types():
    types = ["learning_agreement", "transcript"]
    return jsonify(types), 200


# OK: [GET] /application/document/info/status
# returns the list of allowed document status values
@applications_blueprint.route("/application/document/info/status", methods=["GET"])
def get_document_statuses():
    statuses = ["pending", "approved", "rejected"]
    return jsonify(statuses), 200
