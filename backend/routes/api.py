from flask import Blueprint, jsonify, request
from sqlalchemy import text

from models import db
from auth import custom_jwt_required

api_blueprint = Blueprint("api", __name__, url_prefix="/api")


def _rows_to_dicts(result):
    return [dict(row) for row in result.mappings().all()]

# checks the exception and returns the message acordingly
def extract_db_error(e):
    orig = getattr(e, "orig", None)

    if orig is None or not getattr(orig, "diag", None):
        return str(e)

    return orig.diag.message_primary or str(orig)

@api_blueprint.route("/health", methods=["GET"])
def health():
    result = db.session.execute(
        text(
            """
            SELECT
                current_database() AS database_name,
                version() AS database_version,
                (SELECT COUNT(*) FROM public.users) AS users_count,
                (SELECT COUNT(*) FROM public.institutions) AS institutions_count,
                (SELECT COUNT(*) FROM public.applications) AS applications_count,
                (SELECT COUNT(*) FROM public.exams) AS exams_count
            """
        )
    ).mappings().one()

    return jsonify(
        {
            "status": "ok",
            "database_name": result["database_name"],
            "database_version": result["database_version"],
            "counts": {
                "users": result["users_count"],
                "institutions": result["institutions_count"],
                "applications": result["applications_count"],
                "exams": result["exams_count"],
            },
        }
    ), 200


@api_blueprint.route("/summary", methods=["GET"])
@custom_jwt_required()
def summary():
    counts = db.session.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM public.users) AS users_count,
                (SELECT COUNT(*) FROM public.institutions) AS institutions_count,
                (SELECT COUNT(*) FROM public.applications) AS applications_count,
                (SELECT COUNT(*) FROM public.exams) AS exams_count
            """
        )
    ).mappings().one()

    recent_applications = _rows_to_dicts(
        db.session.execute(
            text(
                """
                SELECT
                    a.id,
                    a.year,
                    a.semester,
                    a.status,
                    a.date_submitted,
                    a.sending_institution,
                    a.host_institution,
                    a.user_id,
                    CONCAT(u.firstname, ' ', u.lastname) AS student_name,
                    si.name AS sending_institution_name,
                    hi.name AS host_institution_name
                FROM public.applications a
                JOIN public.users u ON u.id = a.user_id
                JOIN public.institutions si ON si.id = a.sending_institution
                JOIN public.institutions hi ON hi.id = a.host_institution
                ORDER BY a.date_submitted DESC, a.id DESC
                LIMIT 5
                """
            )
        )
    )
    for row in recent_applications:
        if row.get("date_submitted") is not None:
            row["date_submitted"] = row["date_submitted"].isoformat()

    top_institutions = _rows_to_dicts(
        db.session.execute(
            text(
                """
                SELECT
                    i.id,
                    i.name,
                    i.country,
                    i.city,
                    COUNT(pi.id) AS partner_count
                FROM public.institutions i
                LEFT JOIN public.partner_institution pi ON pi.id_institution = i.id
                GROUP BY i.id, i.name, i.country, i.city
                ORDER BY partner_count DESC, i.name ASC
                LIMIT 5
                """
            )
        )
    )

    return jsonify(
        {
            "counts": {
                "users": counts["users_count"],
                "institutions": counts["institutions_count"],
                "applications": counts["applications_count"],
                "exams": counts["exams_count"],
            },
            "recent_applications": recent_applications,
            "top_institutions": top_institutions,
        }
    ), 200


@api_blueprint.route("/exams", methods=["GET"])
@custom_jwt_required()
def exams():
    exams = _rows_to_dicts(
        db.session.execute(
            text(
                """
                SELECT
                    e.code,
                    e.name,
                    e.credits,
                    e.id_institution,
                    i.name AS institution_name,
                    i.country AS institution_country
                FROM public.exams e
                JOIN public.institutions i ON i.id = e.id_institution
                ORDER BY i.name ASC, e.name ASC
                """
            )
        )
    )
    return jsonify(exams), 200
