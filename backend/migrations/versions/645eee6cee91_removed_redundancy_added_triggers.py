"""removed_redundancy_added_triggers

Revision ID: 645eee6cee91
Revises: 6775acac9cbb
Create Date: 2026-07-03 22:15:30.318638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '645eee6cee91'
down_revision = '6775acac9cbb'
branch_labels = None
depends_on = None


def upgrade():
    # --- modified function (the existing trigger keeps pointing at it) ---

    # check_application_data now also freezes the institutions and the referent of
    # an application once it has moved past the initial statuses. Before, a plain
    # UPDATE that kept the status unchanged (e.g. while 'mobility_ongoing') skipped
    # the status-workflow trigger and let a student swap host_institution, which
    # left the existing mapped_exams pointing at exams of the wrong institution.
    op.execute("""
CREATE OR REPLACE FUNCTION check_application_data() RETURNS TRIGGER AS $$
BEGIN
    -- valid referent, institution is checked by existing constraint
    IF NEW.referent_id IS NOT NULL AND NOT EXISTS(
        SELECT 1
        FROM users
        WHERE id = NEW.referent_id
        AND role='referent'
    ) THEN
        RAISE EXCEPTION 'application referent must have role=referent';
    END IF;

    -- valid student, institution is checked by existing constraint
    IF NOT EXISTS(
        SELECT 1
        FROM users
        WHERE id=NEW.user_id
        AND role='student'
    ) THEN
        RAISE EXCEPTION 'application student must have role=student';
    END IF;

    IF NEW.status IN ('mobility_ongoing','pre_departure_completed','exam_recognition','closed') THEN
        -- restrict institution changes
        IF (NEW.sending_institution <> OLD.sending_institution OR NEW.host_institution <> OLD.host_institution) THEN
            RAISE EXCEPTION 'cannot change institutions while application is in % status', NEW.status;
        END IF;
        -- restrict referent changes
        IF (NEW.referent_id IS DISTINCT FROM OLD.referent_id) THEN
            RAISE EXCEPTION 'cannot change referent while application is in % status', NEW.status;
        END IF;
    END IF;

    -- check if student cannot create a application that is already past all the LA & exams validation process
    IF TG_OP='INSERT' AND NEW.status NOT IN('created','learning_agreement_pending') THEN
        RAISE EXCEPTION 'application status cannot start with %', NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

    # --- new function + trigger ---

    # check_exam_mapping_insert guards INSERT and DELETE of mapped_exams: exams may
    # only be added or removed while the application is created / la_pending /
    # mobility_ongoing. This closes the gap where a student could add mappings to a
    # closed application, or delete an approved/blocking mapping to game the closing
    # checks (the previous check_update_mapping only fired on UPDATE of the exam pair).
    op.execute("""
CREATE OR REPLACE FUNCTION check_exam_mapping_insert() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    IF TG_OP='INSERT' THEN
        SELECT status INTO app_status
        FROM applications
        WHERE id=NEW.application_id;
    ELSE
        SELECT status INTO app_status
        FROM applications
        WHERE id=OLD.application_id;
    END IF;

    IF app_status NOT IN ('learning_agreement_pending','created','mobility_ongoing') THEN
        RAISE EXCEPTION 'cannot add or remove exams when associated application is in %', app_status;
    END IF;

    IF TG_OP='INSERT' THEN
        RETURN NEW;
    ELSE
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER exam_mapping_insert_check
BEFORE INSERT OR DELETE ON mapped_exams
FOR EACH ROW
    EXECUTE FUNCTION check_exam_mapping_insert();
""")


def downgrade():
    # --- drop the newly added trigger + function ---
    op.execute("DROP TRIGGER IF EXISTS exam_mapping_insert_check ON mapped_exams;")
    op.execute("DROP FUNCTION IF EXISTS check_exam_mapping_insert();")

    # --- restore check_application_data to its previous definition (no
    #     institution / referent freeze) ---
    op.execute("""
CREATE OR REPLACE FUNCTION check_application_data() RETURNS TRIGGER AS $$
BEGIN
    -- valid referent, institution is checked by existing constraint
    IF NEW.referent_id IS NOT NULL AND NOT EXISTS(
        SELECT 1
        FROM users
        WHERE id = NEW.referent_id
        AND role='referent'
    ) THEN
        RAISE EXCEPTION 'application referent must have role=referent';
    END IF;

    -- valid student, institution is checked by existing constraint
    IF NOT EXISTS(
        SELECT 1
        FROM users
        WHERE id=NEW.user_id
        AND role='student'
    ) THEN
        RAISE EXCEPTION 'application student must have role=student';
    END IF;

    -- check that a application cannot be created already past the initial statuses
    IF TG_OP='INSERT' AND NEW.status NOT IN('created','learning_agreement_pending') THEN
        RAISE EXCEPTION 'application status cannot start with %', NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")
