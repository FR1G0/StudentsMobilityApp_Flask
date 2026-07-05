"""add triggers

All trigger functions and triggers of the overseas database, consolidated from
the previous migration history (last touched by a3adacd6d090). Bodies are the
canonical versions extracted from the reference database at squash time.

Installed after the seed revision, mirroring pg_dump's restore order: the
historical seed rows must not be re-validated by the INSERT triggers
(closed applications, already-symmetric partner rows).

Revision ID: b7f3d2a91c04
Revises: c8e4f5b62d15
Create Date: 2026-07-04

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b7f3d2a91c04'
down_revision = 'c8e4f5b62d15'
branch_labels = None
depends_on = None


TRIGGER_FUNCTIONS = r"""
CREATE OR REPLACE FUNCTION public.check_application_data()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;
CREATE OR REPLACE FUNCTION public.check_application_status_workflow()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
	-- the status learning_agreement_pending must only be updated when status is created or la_pending
	if NEW.status='learning_agreement_pending' AND OLD.status NOT IN ('learning_agreement_pending', 'created') THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;


	-- the status must go to 'created' only if the previous status was la_pending or created
	IF NEW.status='created' AND OLD.status NOT IN ('learning_agreement_pending', 'created') THEN
		RAISE EXCEPTION 'cannot move to created without an approved learning agreement';
	END IF;
	
	-- the status 'created' must be blocked from going anywhere else
	IF OLD.status='closed' AND NEW.status<>'closed' THEN
		RAISE EXCEPTION 'status is closed, no actions are possible';
	END IF;

	-- learning_agreement_pending -> pre_departure_completed
	IF NEW.status='pre_departure_completed' AND OLD.status='created' THEN
		-- check if associated learning agreement exists and has been approved
		IF NOT EXISTS ( SELECT 1 
				FROM uploaded_documents
				WHERE application_id=NEW.id 
				AND document_type='learning_agreement'
				AND status='approved'
			) THEN
			RAISE EXCEPTION 'cannot move to pre_departure_completed without an approved learning agreement';
		END IF;

		-- check if mapped exams exists and are all approved (search for at least 1 that has not been approved)
		IF EXISTS (SELECT 1
			FROM mapped_exams
			WHERE application_id=NEW.id
			AND status<>'approved'
			) THEN
			RAISE EXCEPTION 'cannot move to pre_departure_completed: all mapped exams must be approved';
		END IF;

		-- check if there is another application in the same time period
		IF EXISTS (SELECT 1
			FROM applications
			WHERE user_id = NEW.user_id
			AND id <> NEW.id
			AND status NOT IN ('learning_agreement_pending','created')
			AND (date_arrived, date_departure) OVERLAPS (NEW.date_arrived, NEW.date_departure)
			) THEN
			RAISE EXCEPTION 'this application overlaps with another applicaiton in the same time period';
		END IF;
	ELSEIF NEW.status='pre_departure_completed' AND OLD.status<>'created' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;

	-- pre_departure_completed -> mobility_ongoing
	IF NEW.status='mobility_ongoing' AND OLD.status='pre_departure_completed' THEN
		-- when going to mobility_ongoing user can only update the date_arrived field
		IF NEW.date_departure IS DISTINCT FROM OLD.date_departure THEN
			RAISE EXCEPTION 'you can only update the arrival date, not the departure date';
		END IF;

		-- user can update the new date_arrived check if new updated date is overlapping
		IF EXISTS (SELECT 1
			FROM applications
			WHERE user_id = NEW.user_id
			AND id <> NEW.id
			AND status NOT IN ('learning_agreement_pending','created')
			AND (date_arrived, date_departure) OVERLAPS (NEW.date_arrived, NEW.date_departure)
			) THEN
			RAISE EXCEPTION 'this application overlaps with another applicaiton in the same time period';
		END IF;
	ELSEIF NEW.status='mobility_ongoing' AND OLD.status<>'pre_departure_completed' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;
	
	-- mobility_ongoing -> exam_recognition
	IF NEW.status='exam_recognition' AND OLD.status='mobility_ongoing' THEN
		-- when going to exam_recognition user can only update the date_departure field
		IF NEW.date_arrived IS DISTINCT FROM OLD.date_arrived THEN
			RAISE EXCEPTION 'you can only update the departure date, not the arrival date';
		END IF;
		IF EXISTS (SELECT 1
			FROM la_modifications
			WHERE application_id=NEW.id
			AND status='pending'
			) THEN
			RAISE EXCEPTION 'cannot change application status to exam_recognition when there are pending modifications';
		END IF;
		-- user can update the new date_departure check if new updated date is overlapping
		IF EXISTS (SELECT 1
			FROM applications
			WHERE user_id = NEW.user_id
			AND id <> NEW.id
			AND status NOT IN ('learning_agreement_pending','created')
			AND (date_arrived, date_departure) OVERLAPS (NEW.date_arrived, NEW.date_departure)
			) THEN
			RAISE EXCEPTION 'this application overlaps with another applicaiton in the same time period';
		END IF;

		-- update the mapped exams to 'pending' because a grade is expected
		UPDATE mapped_exams 
		SET status='pending' 
		WHERE application_id=NEW.id;
	ELSEIF NEW.status='exam_recognition' AND OLD.status<>'mobility_ongoing' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;

	IF NEW.status='closed' AND OLD.status='exam_recognition' THEN
		-- check uploaded transcript of records, if it exists and has been approved
		IF NOT EXISTS (SELECT 1
			FROM uploaded_documents
			WHERE application_id=NEW.id
			AND document_type='transcript'
			AND status='approved'
			) THEN
			RAISE EXCEPTION 'approved transcript of records required';
		END IF;

		-- check if all mapped_exams are graded (if exists at least 1 that has no grade)
		IF EXISTS(SELECT 1
				FROM mapped_exams
				WHERE application_id=NEW.id AND 
				(grade IS NULL OR grade=-1 OR status <> 'approved')
			) THEN
			RAISE EXCEPTION 'all exams must be approved and require a grade';
		END IF;
	ELSEIF NEW.status='closed' AND OLD.status<>'exam_recognition' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;

	RETURN NEW;
END;
$function$
;
CREATE OR REPLACE FUNCTION public.check_document_status_update()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
	app_status VARCHAR(32);
BEGIN
	SELECT status INTO app_status
	FROM applications
	WHERE id = NEW.application_id;

	-- prevent status change when application is not in adequate status 
	IF NEW.document_type='learning_agreement' THEN
		IF app_status NOT IN ('created','learning_agreement_pending','mobility_ongoing') THEN
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
$function$
;
CREATE OR REPLACE FUNCTION public.check_exam_mapping_insert()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;
CREATE OR REPLACE FUNCTION public.check_grade_changes()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;
CREATE OR REPLACE FUNCTION public.check_mapped_exam_institutions()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    app_host_inst       INT;
    app_sending_inst    INT;
    host_exam_inst      INT;
    sending_exam_inst   INT;
BEGIN
    SELECT host_institution, sending_institution
        INTO app_host_inst, app_sending_inst
        FROM applications
        WHERE id = NEW.application_id;

    SELECT id_institution INTO host_exam_inst
        FROM exams WHERE id = NEW.host_exam_id;

    SELECT id_institution INTO sending_exam_inst
        FROM exams WHERE id = NEW.sending_exam_id;

	-- this can be possible through an independent insert
    IF host_exam_inst <> app_host_inst THEN
        RAISE EXCEPTION 'host_exam_id institution does not match application host_institution';
    END IF;

	-- this can be possible through an independent insert
    IF sending_exam_inst <> app_sending_inst THEN
        RAISE EXCEPTION 'sending_exam_id institution does not match application sending_institution';
    END IF;

    RETURN NEW;
END;
$function$
;
CREATE OR REPLACE FUNCTION public.check_update_mapping()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;
CREATE OR REPLACE FUNCTION public.check_update_status_mapped_exams()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;
CREATE OR REPLACE FUNCTION public.mirror_partner_institution()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM partner_institution
        WHERE id_institution = NEW.id_partner_institution
          AND id_partner_institution = NEW.id_institution
    ) THEN
        INSERT INTO partner_institution (id_institution, id_partner_institution)
            VALUES (NEW.id_partner_institution, NEW.id_institution);
    END IF;

    RETURN NEW;
END;
$function$
;
CREATE OR REPLACE FUNCTION public.set_modification_decision_date()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.status IN ('approved', 'rejected') THEN
        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$function$
;
CREATE OR REPLACE FUNCTION public.update_application_on_upload()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;
"""

TRIGGERS = r"""
CREATE TRIGGER applicaiton_status_workflow BEFORE UPDATE ON public.applications FOR EACH ROW WHEN (((new.status)::text <> (old.status)::text)) EXECUTE FUNCTION check_application_status_workflow();
CREATE TRIGGER applicaiton_update_on_upload BEFORE INSERT ON public.uploaded_documents FOR EACH ROW EXECUTE FUNCTION update_application_on_upload();
CREATE TRIGGER application_data_check BEFORE INSERT OR UPDATE ON public.applications FOR EACH ROW EXECUTE FUNCTION check_application_data();
CREATE TRIGGER document_status_update_check BEFORE UPDATE ON public.uploaded_documents FOR EACH ROW WHEN (((old.status)::text <> (new.status)::text)) EXECUTE FUNCTION check_document_status_update();
CREATE TRIGGER exam_grade_changes_check BEFORE UPDATE ON public.mapped_exams FOR EACH ROW WHEN (((new.grade IS DISTINCT FROM old.grade) OR (new.date_passed IS DISTINCT FROM old.date_passed))) EXECUTE FUNCTION check_grade_changes();
CREATE TRIGGER exam_mapping_insert_check BEFORE INSERT OR DELETE ON public.mapped_exams FOR EACH ROW EXECUTE FUNCTION check_exam_mapping_insert();
CREATE TRIGGER exam_mapping_update_check BEFORE UPDATE ON public.mapped_exams FOR EACH ROW WHEN (((new.sending_exam_id <> old.sending_exam_id) OR (new.host_exam_id <> old.host_exam_id))) EXECUTE FUNCTION check_update_mapping();
CREATE TRIGGER la_modification_decision_date BEFORE UPDATE ON public.la_modifications FOR EACH ROW WHEN (((old.status)::text <> (new.status)::text)) EXECUTE FUNCTION set_modification_decision_date();
CREATE TRIGGER mapped_exam_institutions_check BEFORE INSERT OR UPDATE ON public.mapped_exams FOR EACH ROW EXECUTE FUNCTION check_mapped_exam_institutions();
CREATE TRIGGER mapped_exam_update_status_check BEFORE UPDATE ON public.mapped_exams FOR EACH ROW WHEN (((old.status)::text <> (new.status)::text)) EXECUTE FUNCTION check_update_status_mapped_exams();
CREATE TRIGGER partner_institution_symmetry AFTER INSERT ON public.partner_institution FOR EACH ROW EXECUTE FUNCTION mirror_partner_institution();
"""


def upgrade():
    op.execute(TRIGGER_FUNCTIONS)
    op.execute(TRIGGERS)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS applicaiton_status_workflow ON public.applications;")
    op.execute("DROP TRIGGER IF EXISTS applicaiton_update_on_upload ON public.uploaded_documents;")
    op.execute("DROP TRIGGER IF EXISTS application_data_check ON public.applications;")
    op.execute("DROP TRIGGER IF EXISTS document_status_update_check ON public.uploaded_documents;")
    op.execute("DROP TRIGGER IF EXISTS exam_grade_changes_check ON public.mapped_exams;")
    op.execute("DROP TRIGGER IF EXISTS exam_mapping_insert_check ON public.mapped_exams;")
    op.execute("DROP TRIGGER IF EXISTS exam_mapping_update_check ON public.mapped_exams;")
    op.execute("DROP TRIGGER IF EXISTS la_modification_decision_date ON public.la_modifications;")
    op.execute("DROP TRIGGER IF EXISTS mapped_exam_institutions_check ON public.mapped_exams;")
    op.execute("DROP TRIGGER IF EXISTS mapped_exam_update_status_check ON public.mapped_exams;")
    op.execute("DROP TRIGGER IF EXISTS partner_institution_symmetry ON public.partner_institution;")
    op.execute("DROP FUNCTION IF EXISTS public.check_application_data();")
    op.execute("DROP FUNCTION IF EXISTS public.check_application_status_workflow();")
    op.execute("DROP FUNCTION IF EXISTS public.check_document_status_update();")
    op.execute("DROP FUNCTION IF EXISTS public.check_exam_mapping_insert();")
    op.execute("DROP FUNCTION IF EXISTS public.check_grade_changes();")
    op.execute("DROP FUNCTION IF EXISTS public.check_mapped_exam_institutions();")
    op.execute("DROP FUNCTION IF EXISTS public.check_update_mapping();")
    op.execute("DROP FUNCTION IF EXISTS public.check_update_status_mapped_exams();")
    op.execute("DROP FUNCTION IF EXISTS public.mirror_partner_institution();")
    op.execute("DROP FUNCTION IF EXISTS public.set_modification_decision_date();")
    op.execute("DROP FUNCTION IF EXISTS public.update_application_on_upload();")
