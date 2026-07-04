"""trigger_update1

Revision ID: a3adacd6d090
Revises: 645eee6cee91
Create Date: 2026-07-04 14:06:56.835991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3adacd6d090'
down_revision = '645eee6cee91'
branch_labels = None
depends_on = None


def upgrade():
    # check_update_status_mapped_exams() now validates the mapped exam status up
    # front (the SELECT and the adequate-status check run for every status change,
    # not only 'approved'/'pending'/'rejected'), and while the application is in
    # 'exam_recognition' it refuses to approve/reject an exam that has no grade or
    # passing date. the trigger is unchanged (still WHEN OLD.status <> NEW.status).
    op.execute("""
CREATE OR REPLACE FUNCTION check_update_status_mapped_exams() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    -- prevent status change when application is not in adequate status
    SELECT status INTO app_status
    FROM applications
    WHERE id = NEW.application_id;
    IF app_status NOT IN ('created','learning_agreement_pending','mobility_ongoing','exam_recognition') THEN
        RAISE EXCEPTION 'cannot change exam status when associated application is in % status', app_status;
    END IF;

    IF app_status = 'exam_recognition' THEN
        IF NEW.status <> 'pending'
           AND (NEW.grade = -1 OR NEW.date_passed IS NULL) THEN
            RAISE EXCEPTION 'cannot approve or reject exam without a grade';
        END IF;
    END IF;

    NEW.decision_date := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")


def downgrade():
    # restore the previous definition (revision 6775acac9cbb)
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
