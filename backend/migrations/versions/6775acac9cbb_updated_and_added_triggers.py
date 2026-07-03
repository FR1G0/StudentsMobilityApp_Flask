"""updated_and_added_triggers

Revision ID: 6775acac9cbb
Revises: b9d9d1de9be5
Create Date: 2026-07-03 17:54:16.554456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6775acac9cbb'
down_revision = 'b9d9d1de9be5'
branch_labels = None
depends_on = None


def upgrade():
    # --- modified functions (existing triggers keep pointing at them) ---

    # a learning agreement may now also be (re)uploaded while the application is
    # 'mobility_ongoing' (added 'mobility_ongoing' to the allowed status list)
    op.execute("""
CREATE OR REPLACE FUNCTION update_application_on_upload() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    SELECT status
        INTO app_status
        FROM applications
        WHERE id = NEW.application_id;

    IF NEW.document_type = 'learning_agreement' THEN
        -- check if the status of associated application is valid
        IF app_status NOT IN ('created','learning_agreement_pending','mobility_ongoing') THEN
            RAISE EXCEPTION 'new learning agreement document cannot be changed while the application is in % status', app_status;
        END IF;

        IF app_status = 'created' THEN
            UPDATE applications SET status='learning_agreement_pending' WHERE id=NEW.application_id;
        END IF;
    ELSE
        -- if it's not a LA, it must be a transcript of records (because of check constraint), check if the status of associated application is valid
        IF app_status <> 'exam_recognition' THEN
            RAISE EXCEPTION 'new transcript of records document cannot be changed while the application is in % status', app_status;
        END IF;
    END IF;

    RETURN NEW;
END
$$ LANGUAGE plpgsql;
""")

    # stamps decision_date also when a mapped exam is moved back to 'pending'
    # (added 'pending' to the handled status list)
    op.execute("""
CREATE OR REPLACE FUNCTION check_update_status_mapped_exams() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    IF NEW.status IN ('approved', 'pending' ,'rejected') THEN
        -- prevent status change when application is not in adequate status
        SELECT status INTO app_status
        FROM applications
        WHERE id = NEW.application_id;
        IF app_status NOT IN ('created','learning_agreement_pending','mobility_ongoing','exam_recognition') THEN
            RAISE EXCEPTION 'cannot change exam status when associated application is in % status', app_status;
        END IF;

        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

    # the document-status validation now runs for every status change (the outer
    # 'approved'/'rejected' guard was removed; the trigger already fires only WHEN
    # OLD.status <> NEW.status) and decision_date is always stamped
    op.execute("""
CREATE OR REPLACE FUNCTION check_document_status_update() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    SELECT status INTO app_status
    FROM applications
    WHERE id = NEW.application_id;

    -- prevent status change when application is not in adequate status
    IF NEW.document_type='learning_agreement' THEN
        IF app_status NOT IN ('created','learning_agreement_pending') THEN
            RAISE EXCEPTION 'cannot change document when associated application is in % status', app_status;
        END IF;
    END IF;
    IF NEW.document_type='transcript' THEN
        IF app_status <> 'exam_recognition' THEN
            RAISE EXCEPTION 'cannot change document status when associated application is in % status', app_status;
        END IF;
    END IF;

    NEW.decision_date := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

    # --- new functions + triggers ---

    # validates a grade / date_passed update on a mapped exam: the mapping must not
    # be already approved, the application must be in 'exam_recognition' and the
    # passed date must fall within the mobility period; resets the status to pending
    op.execute("""
CREATE OR REPLACE FUNCTION check_grade_changes() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
    start_mobility_date DATE;
    end_mobility_date DATE;
BEGIN
    -- if exam mapping was already approved, it must not be changed
    IF OLD.status='approved' THEN
        RAISE EXCEPTION 'cannot update grade information when exam status is approved';
    END IF;

    -- check if exam grade changes are valid in the associated application
    SELECT status, date_arrived, date_departure
    INTO app_status, start_mobility_date, end_mobility_date
    FROM applications
    WHERE id=NEW.application_id;

    -- changes cannot be made if the application is not in exam_recognition status
    IF app_status <> 'exam_recognition' THEN
        RAISE EXCEPTION 'cannot update exam grade when associated application is in %', app_status;
    END IF;

    -- check if the passed date is within the mobility period
    IF NEW.date_passed IS NOT NULL
       AND (start_mobility_date IS NULL OR end_mobility_date IS NULL
            OR NEW.date_passed NOT BETWEEN start_mobility_date AND end_mobility_date) THEN
        RAISE EXCEPTION 'exam passed date must be between the arrival and departure date';
    END IF;

    NEW.status = 'pending';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER exam_grade_changes_check
BEFORE UPDATE ON mapped_exams
FOR EACH ROW
    WHEN (NEW.grade IS DISTINCT FROM OLD.grade
        OR NEW.date_passed IS DISTINCT FROM OLD.date_passed)
    EXECUTE FUNCTION check_grade_changes();
""")

    # validates a change of the mapped exam pair (sending/host exam): only allowed
    # while the application is created / la_pending / mobility_ongoing; resets the
    # status to pending
    op.execute("""
CREATE OR REPLACE FUNCTION check_update_mapping() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    SELECT status INTO app_status
    FROM applications
    WHERE id=NEW.application_id;

    -- cannot change mapping if not allowed in the current app status
    IF app_status NOT IN ('learning_agreement_pending','created','mobility_ongoing') THEN
        RAISE EXCEPTION 'invalid, cannot change exam mapping when associated application is in % status',app_status;
    END IF;

    NEW.status='pending';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER exam_mapping_update_check
BEFORE UPDATE ON mapped_exams
FOR EACH ROW
    WHEN (NEW.sending_exam_id<>OLD.sending_exam_id
    OR NEW.host_exam_id<>OLD.host_exam_id)
    EXECUTE FUNCTION check_update_mapping();
""")


def downgrade():
    # --- drop the newly added triggers + functions ---
    op.execute("DROP TRIGGER IF EXISTS exam_mapping_update_check ON mapped_exams;")
    op.execute("DROP FUNCTION IF EXISTS check_update_mapping();")

    op.execute("DROP TRIGGER IF EXISTS exam_grade_changes_check ON mapped_exams;")
    op.execute("DROP FUNCTION IF EXISTS check_grade_changes();")

    # --- restore the modified functions to their previous definitions ---

    op.execute("""
CREATE OR REPLACE FUNCTION update_application_on_upload() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    SELECT status
        INTO app_status
        FROM applications
        WHERE id = NEW.application_id;

    IF NEW.document_type = 'learning_agreement' THEN
        -- check if the status of associated application is valid
        IF app_status NOT IN ('created','learning_agreement_pending') THEN
            RAISE EXCEPTION 'new learning agreement document cannot be changed while the application is in % status', app_status;
        END IF;

        IF app_status = 'created' THEN
            UPDATE applications SET status='learning_agreement_pending' WHERE id=NEW.application_id;
        END IF;
    ELSE
        -- if it's not a LA, it must be a transcript of records (because of check constraint), check if the status of associated application is valid
        IF app_status <> 'exam_recognition' THEN
            RAISE EXCEPTION 'new transcript of records document cannot be changed while the application is in % status', app_status;
        END IF;
    END IF;

    RETURN NEW;
END
$$ LANGUAGE plpgsql;
""")

    op.execute("""
CREATE OR REPLACE FUNCTION check_update_status_mapped_exams() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    IF NEW.status IN ('approved', 'rejected') THEN
        -- prevent status change when application is not in adequate status
        SELECT status INTO app_status
        FROM applications
        WHERE id = NEW.application_id;
        IF app_status NOT IN ('created','learning_agreement_pending','mobility_ongoing','exam_recognition') THEN
            RAISE EXCEPTION 'cannot change exam status when associated application is in % status', app_status;
        END IF;

        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

    op.execute("""
CREATE OR REPLACE FUNCTION check_document_status_update() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    SELECT status INTO app_status
    FROM applications
    WHERE id = NEW.application_id;

    IF NEW.status IN ('approved', 'rejected') THEN
        -- prevent status change when application is not in adequate status
        IF NEW.document_type='learning_agreement' THEN
            IF app_status NOT IN ('created','learning_agreement_pending') THEN
                RAISE EXCEPTION 'cannot change document when associated application is in % status', app_status;
            END IF;
        END IF;
        IF NEW.document_type='transcript' THEN
            IF app_status <> 'exam_recognition' THEN
                RAISE EXCEPTION 'cannot change document status when associated application is in % status', app_status;
            END IF;
        END IF;

        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")
