-- on INSERT of a document, the associated application must be notified, changed status and check if business rules apply correctly
CREATE OR REPLACE FUNCTION update_application_on_upload()  RETURNS TRIGGER AS $$ 
DECLARE
	app_status VARCHAR(32);
BEGIN
	SELECT status 
		INTO app_status
		FROM applications
		WHERE id = NEW.application_id;

	IF NEW.document_type = 'learning_agreement' THEN
		-- check if the status of associated applicaiton is valid
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

CREATE TRIGGER applicaiton_update_on_upload
BEFORE INSERT ON uploaded_documents
FOR EACH ROW
	EXECUTE FUNCTION update_application_on_upload()

-- on INSERT/UPDATE of a mapped_exams row, verifies that
--   1) host_exam_id    belongs to the application's host_institution
--   2) sending_exam_id belongs to the application's sending_institution
CREATE OR REPLACE FUNCTION check_mapped_exam_institutions() RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

CREATE TRIGGER mapped_exam_institutions_check
BEFORE INSERT OR UPDATE ON mapped_exams
FOR EACH ROW
	EXECUTE FUNCTION check_mapped_exam_institutions();


-- on INSERT/UPDATE of an application, verifies that the referent (if not null, which it can be) has role='referent' and is enrolled in the application's sending_institution.
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

	-- check if student cannot create a application that is already past all the LA & exams validation process
	IF TG_OP='INSERT' AND NEW.status NOT IN('created','learning_agreement_pending') THEN
		RAISE EXCEPTION 'application status cannot start with %', NEW.status;
	END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER application_data_check
BEFORE INSERT OR UPDATE ON applications
FOR EACH ROW
	EXECUTE FUNCTION check_application_data();


-- student puts application into ongoing or exam_recognition
CREATE OR REPLACE FUNCTION check_application_status_workflow() RETURNS TRIGGER AS $$
BEGIN
	IF NEW.status='created' AND OLD.status NOT IN ('learning_agreement_pending', 'created') THEN
		RAISE EXCEPTION 'cannot move to created without an approved learning agreement';
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
	ELSEIF NEW.status='pre_departure_completed' AND OLD.status<>'created' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;

	-- pre_departure_completed -> mobility_ongoing
	IF NEW.status='mobility_ongoing' AND OLD.status<>'pre_departure_completed' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;
	
	-- mobility_ongoing -> exam_recognition
	IF NEW.status='exam_recognition' AND OLD.status='mobility_ongoing' THEN
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
$$ LANGUAGE plpgsql;

CREATE TRIGGER applicaiton_status_workflow 
BEFORE UPDATE ON applications
FOR EACH ROW
	WHEN (NEW.status<>OLD.status)
	EXECUTE FUNCTION  check_application_status_workflow();

-- when the status of a mapped_exam changes to 'approved' or 'rejected', automatically stamps decision_date with the current timestamp.
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

CREATE TRIGGER mapped_exam_update_status_check
BEFORE UPDATE ON mapped_exams
FOR EACH ROW
WHEN (OLD.status <> NEW.status)
	EXECUTE FUNCTION check_update_status_mapped_exams();


-- when the status of an uploaded_document changes to 'approved' or 'rejected', automatically stamps decision_date with the current timestamp.
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

CREATE TRIGGER document_status_update_check
BEFORE UPDATE ON uploaded_documents
FOR EACH ROW
WHEN (OLD.status <> NEW.status)
	EXECUTE FUNCTION check_document_status_update();


-- after an INSERT on partner_institution, automatically inserts the reciprocal row (B -> A) if it does not already exist, so that partnership is always symmetrical in the data.
CREATE OR REPLACE FUNCTION mirror_partner_institution() RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

CREATE TRIGGER partner_institution_symmetry
AFTER INSERT ON partner_institution
FOR EACH ROW
	EXECUTE FUNCTION mirror_partner_institution();


-- when the status of a la_modification changes to 'approved' or 'rejected', automatically stamps decision_date with the current timestamp.
CREATE OR REPLACE FUNCTION set_modification_decision_date() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('approved', 'rejected') THEN
        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER la_modification_decision_date
BEFORE UPDATE ON la_modifications
FOR EACH ROW
WHEN (OLD.status <> NEW.status)
	EXECUTE FUNCTION set_modification_decision_date();
