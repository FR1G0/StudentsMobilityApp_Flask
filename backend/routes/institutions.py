from flask import Blueprint, jsonify, request, g
from sqlalchemy import text

from auth import (
    ROLE_OVERSEAS,
    custom_jwt_required,
    require_roles,
)
from models import db, Institution, PartnerInstitution
from routes.users import user_in_institution

institutions_blueprint = Blueprint("institutions", __name__)


# OK: [GET] /institutions
# returns the list of all institutions, accessible to everyone
@institutions_blueprint.route("/institutions", methods=["GET"])
def list_institutions():
    try:
        institutions = Institution.query.all()
        result = []
        for inst in institutions:
            result.append(inst.to_dict())
        return jsonify(result), 200
    except Exception as e:
        msg = extract_db_error(e)
        return jsonify({"error": msg}), 500


# WARN: (how to restrict this kind of access) [POST] /institution/insert
# inserts a new institution row (staff only)
@institutions_blueprint.route("/institution/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def insert_institution():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        new_inst = Institution(
            name=data.get("name"),
            country=data.get("country"),
            city=data.get("city"),
        )
        db.session.add(new_inst)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500

# OK: [POST] /institution/info/:id
# returns information associated to the application
@institutions_blueprint.route("/institution/info/<int:id>", methods=["GET"])
def get_institition_information(id):
    try:
        inst = Institution.query.get(id)
        if not inst:
            return jsonify({"status": "failed", "error": "institution not found"}), 404

        return jsonify(inst.to_dict())
    except Exception as e:
        msg = extract_db_error(e)
        return jsonify({"status": "failed", "error": msg}), 500



# OK: [POST] /institution/update/:id
# updates an existing institution row (staff only)
@institutions_blueprint.route("/institution/update/<int:id>", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def update_institution(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400

        inst = Institution.query.get(id)
        if not inst:
            return jsonify({"status": "failed", "error": "institution not found"}), 404
        

        if not user_in_institution(g.current_user,id):
            return jsonify({"error": " access restricted"}), 403

        if "name" in data:
            inst.name = data["name"]
        if "country" in data:
            inst.country = data["country"]
        if "city" in data:
            inst.city = data["city"]

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# OK: [GET] /institution/:id_institution/partners
# returns the list of partner institution mappings linked to the given institution
@institutions_blueprint.route("/institution/<int:id_institution>/partners", methods=["GET"])
@custom_jwt_required()
def get_institution_partners(id_institution):
    try:
        rows = db.session.execute(
            text(
                """
                SELECT pi.id AS partner_row_id,
                       pi.id_partner_institution,
                       i.name AS partner_name,
                       i.country AS partner_country,
                       i.city AS partner_city
                FROM partner_institution pi
                JOIN institutions i ON i.id = pi.id_partner_institution
                WHERE pi.id_institution = :id_institution
                """
            ),
            {"id_institution": id_institution},
        ).mappings().all()

        result = []
        for row in rows:
            result.append({
                "partner_row_id": row["partner_row_id"],
                "id_partner_institution": row["id_partner_institution"],
                "name": row["partner_name"],
                "country": row["partner_country"],
                "city": row["partner_city"],
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# OK: [GET] /institution/:id/referents
# returns the list of referents (users with role=referent) associated to the institution
@institutions_blueprint.route("/institution/<int:id>/referents", methods=["GET"])
@custom_jwt_required()
def get_institution_referents(id):
    try:
        rows = db.session.execute(
            text(
                """
                SELECT u.id, u.email, u.firstname, u.lastname, u.role, u.id_institution
                FROM users u
                JOIN institutions i ON i.id = u.id_institution
                WHERE i.id = :id AND u.role = 'referent'
                """
            ),
            {"id": id},
        ).mappings().all()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "email": row["email"],
                "firstname": row["firstname"],
                "lastname": row["lastname"],
                "role": row["role"],
                "id_institution": row["id_institution"],
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# OK: [GET] /institution/:id/students
# returns the list of students associated to the institution
@institutions_blueprint.route("/institution/<int:id>/students", methods=["GET"])
@custom_jwt_required()
def get_institution_students(id):
    try:
        rows = db.session.execute(
            text(
                """
                SELECT u.id, u.email, u.firstname, u.lastname, u.role, u.id_institution
                FROM users u
                JOIN institutions i ON i.id = u.id_institution
                WHERE i.id = :id AND u.role = 'student'
                """
            ),
            {"id": id},
        ).mappings().all()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "email": row["email"],
                "firstname": row["firstname"],
                "lastname": row["lastname"],
                "role": row["role"],
                "id_institution": row["id_institution"],
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# OK: [GET] /institution/:id/staff
# returns the list of staff members associated to the institution
@institutions_blueprint.route("/institution/<int:id>/staff", methods=["GET"])
@custom_jwt_required()
def get_institution_staff(id):
    try:
        rows = db.session.execute(
            text(
                """
                SELECT u.id, u.email, u.firstname, u.lastname, u.role, u.id_institution
                FROM users u
                JOIN institutions i ON i.id = u.id_institution
                WHERE i.id = :id AND u.role = 'staff'
                """
            ),
            {"id": id},
        ).mappings().all()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "email": row["email"],
                "firstname": row["firstname"],
                "lastname": row["lastname"],
                "role": row["role"],
                "id_institution": row["id_institution"],
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# OK: [GET] /institution/:id/exams
# returns the list of exams associated to the institution
@institutions_blueprint.route("/institution/<int:id>/exams", methods=["GET"])
@custom_jwt_required()
def get_institution_exams(id):
    try:
        rows = db.session.execute(
            text(
                """
                SELECT e.id, e.code, e.name, e.credits, e.id_institution
                FROM exams e
                JOIN institutions i ON i.id = e.id_institution
                WHERE i.id = :id
                """
            ),
            {"id": id},
        ).mappings().all()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "code": row["code"],
                "name": row["name"],
                "credits": row["credits"],
                "id_institution": row["id_institution"],
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# OK: [POST] /institution/partner/insert
# inserts a new partner_institution row to link two institutions
@institutions_blueprint.route("/institution/partner/insert", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def insert_partner_institution():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400
        
        if not user_in_institution(g.current_user, data.get("id_institution")):
            return jsonify({"error": "staff member not authorized to add partnership"}), 403

        new_partner = PartnerInstitution(
            id_institution=data.get("id_institution"),
            id_partner_institution=data.get("id_partner_institution"),
        )
        db.session.add(new_partner)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# OK: [POST] /institution/partner/:id/delete
# deletes a partner_institution mapping using the row id
@institutions_blueprint.route("/institution/partner/<int:id>/delete", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def delete_partner_institution(id):
    try:
        partner = PartnerInstitution.query.get(id)
        if not partner:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404

        if not user_in_institution(g.current_user, partner.id_institution):
            return jsonify({"error": "staff member not authorized to remove partnership"}), 403

        db.session.delete(partner)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500


# NOTE: [POST] /institution/partner/:id/update
# updates an existing partner_institution mapping using the row id
# WARN: a bit weird to update a partnership, but NOT logically wrong, let's keep it.
@institutions_blueprint.route("/institution/partner/<int:id>/update", methods=["POST"])
@custom_jwt_required()
@require_roles(ROLE_OVERSEAS)
def update_partner_institution(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "missing body"}), 400


        partner = PartnerInstitution.query.get(id)
        if not partner:
            return jsonify({"status": "failed", "error": "mapping not found"}), 404

        if not user_in_institution(g.current_user, partner.id_institution):
            return jsonify({"error": "staff member not authorized to update partnership"}), 403

        if "id_institution" in data:
            partner.id_institution = data["id_institution"]
        if "id_partner_institution" in data:
            partner.id_partner_institution = data["id_partner_institution"]

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500
