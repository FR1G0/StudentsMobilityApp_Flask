from flask import Blueprint, jsonify, request, g

from auth import (
    ROLE_STUDENT,
    ROLE_REFERENT,
    can_view_application,
    custom_jwt_required,
    require_roles,
)
from models import (
    db,
    Application,
    MappedExam,
    LAModification,
    LAModificationExam,
    UploadedDocument,
)

modifications_blueprint = Blueprint("modifications", __name__)


# NOTE: [POST] /application/:application_id/modification
# student proposes a Learning Agreement modification during mobility: the current
# exam mapping is snapshotted into la_modification_exams and replaced by the proposed
# one, all inside a single transaction. The updated LA must already be uploaded.
@modifications_blueprint.route("/application/<int:application_id>/modification", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_STUDENT)
def create_modification(application_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "missing body"}), 400

        application = Application.query.get(application_id)
        if not application:
            return jsonify({"error": "application not found"}), 404
        if application.user_id != g.current_user_id:
            return jsonify({"error": "not your application"}), 403
        if application.status != "mobility_ongoing":
            return jsonify({"error": "modifications allowed only during mobility"}), 400

        # only one open proposal at a time
        if LAModification.query.filter_by(application_id=application_id, status="pending").first():
            return jsonify({"error": "a pending modification already exists"}), 409

        description = (data.get("description") or "").strip()
        document_id = data.get("document_id")
        new_mapping = data.get("mapping")
        if not description or not document_id or not new_mapping:
            return jsonify({"error": "description, document_id and mapping required"}), 400

        # the updated LA must belong to this application and be a learning_agreement
        doc = UploadedDocument.query.get(document_id)
        if (not doc or doc.application_id != application_id
                or doc.document_type != "learning_agreement"):
            return jsonify({"error": "document_id must be a learning_agreement of this application"}), 400

        # ---- single transaction: create proposal, snapshot current, swap mapping ----
        mod = LAModification(
            application_id=application_id,
            description=description,
            document_id=document_id,
            status="pending",
        )
        db.session.add(mod)
        db.session.flush()  # need mod.id for the snapshot rows

        # snapshot the CURRENT mapping into the child table
        for r in MappedExam.query.filter_by(application_id=application_id).all():
            db.session.add(LAModificationExam(
                modification_id=mod.id,
                host_exam_id=r.host_exam_id,
                sending_exam_id=r.sending_exam_id,
                grade=r.grade,
                date_passed=r.date_passed,
                status=r.status,
                notes=r.notes,
                decision_date=r.decision_date,
            ))

        # replace the live mapping (delete before insert: unique constraints)
        MappedExam.query.filter_by(application_id=application_id).delete()
        db.session.flush()
        for m in new_mapping:
            db.session.add(MappedExam(
                application_id=application_id,
                host_exam_id=m["host_exam_id"],
                sending_exam_id=m["sending_exam_id"],
                notes=m.get("notes", ""),
            ))

        db.session.commit()
        return jsonify({"status": "success", "id": mod.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# NOTE: [GET] /application/:application_id/modifications
# returns the modification proposals of an application, each with its snapshot
@modifications_blueprint.route("/application/<int:application_id>/modifications", methods=["GET"])
@custom_jwt_required()
def list_modifications(application_id):
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"error": "application not found"}), 404
    if not can_view_application(application, g.current_user, g.current_user_role):
        return jsonify({"error": "not authorized"}), 403

    result = []
    for mod in LAModification.query.filter_by(application_id=application_id).all():
        item = mod.to_dict()
        item["snapshot"] = [
            s.to_dict()
            for s in LAModificationExam.query.filter_by(modification_id=mod.id).all()
        ]
        result.append(item)
    return jsonify(result), 200


# NOTE: [POST] /modification/:id/decision
# the application's referent approves or rejects a modification. On reject the
# previous mapping is restored from the snapshot, atomically. decision_date is
# stamped by a DB trigger.
@modifications_blueprint.route("/modification/<int:id>/decision", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_REFERENT)
def decide_modification(id):
    try:
        data = request.get_json()
        if not data or "status" not in data:
            return jsonify({"error": "missing status"}), 400

        new_status = data["status"]
        if new_status not in ("approved", "rejected"):
            return jsonify({"error": "status must be approved or rejected"}), 400

        mod = LAModification.query.get(id)
        if not mod:
            return jsonify({"error": "modification not found"}), 404
        if mod.status != "pending":
            return jsonify({"error": "modification already decided"}), 409

        application = Application.query.get(mod.application_id)
        if application.referent_id != g.current_user_id:
            return jsonify({"error": "not the referent of this application"}), 403

        notes = data.get("notes", "")
        if new_status == "rejected" and not notes.strip():
            return jsonify({"error": "rejection requires a motivation"}), 400

        if new_status == "rejected":
            # ---- restore the previous mapping from the snapshot, atomically ----
            MappedExam.query.filter_by(application_id=mod.application_id).delete()
            db.session.flush()
            for s in LAModificationExam.query.filter_by(modification_id=mod.id).all():
                db.session.add(MappedExam(
                    application_id=mod.application_id,
                    host_exam_id=s.host_exam_id,
                    sending_exam_id=s.sending_exam_id,
                    grade=s.grade,
                    date_passed=s.date_passed,
                    status=s.status,
                    notes=s.notes,
                    decision_date=s.decision_date,
                ))

        mod.status = new_status
        mod.notes = notes
        # decision_date is set by the set_modification_decision_date trigger
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
