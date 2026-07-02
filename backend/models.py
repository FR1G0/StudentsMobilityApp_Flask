from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint, DDL, event
db = SQLAlchemy()

# NOTE: : each model has predefined functions
# User.query.all()
# User.query.get(id)
# User.query.filter_by(name='Joe').first()
# User.query.filter(User.age > 18).all()


#  user model
class Institution(db.Model):
    __tablename__ = 'institutions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'country': self.country,
            'city': self.city
        }


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    id_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        db.CheckConstraint("role = 'student' OR role = 'referent' OR role = 'staff'", name='allowed_user_roles'),
        db.UniqueConstraint('id', 'id_institution'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'id_institution': self.id_institution
        }


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(32), nullable=False, default='created')
    date_submitted = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    date_arrived = db.Column(db.Date, nullable=True)
    date_departure = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, default='')
    referent_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    sending_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    host_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['user_id', 'sending_institution'], ['users.id', 'users.id_institution']),
        ForeignKeyConstraint(['referent_id', 'sending_institution'], ['users.id', 'users.id_institution']),
        ForeignKeyConstraint(
            ['sending_institution', 'host_institution'],
            ['partner_institution.id_institution', 'partner_institution.id_partner_institution'],
            onupdate='CASCADE'
        ),
        db.CheckConstraint('host_institution <> sending_institution', name='different_host_sending'),
        db.CheckConstraint(
            'date_arrived IS NULL OR date_departure IS NULL OR date_departure >= date_arrived',
            name='valid_mobility_dates'
        ),
        db.CheckConstraint("semester IN ('first', 'second', 'full')", name='valid_semester'),
        db.CheckConstraint(
            "status IN ('created', 'learning_agreement_pending', 'pre_departure_completed', 'mobility_ongoing', 'exam_recognition', 'closed')",
            name='valid_status'
        ),
    )

    # trigger: referent must be a referent, student must be a student, and an application cannot start already past the initial statuses
    application_data_check = DDL("""
CREATE OR REPLACE FUNCTION check_application_data() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.referent_id IS NOT NULL AND NOT EXISTS(
        SELECT 1
        FROM users
        WHERE id = NEW.referent_id
        AND role='referent'
    ) THEN
        RAISE EXCEPTION 'application referent must have role=referent';
    END IF;

    IF NOT EXISTS(
        SELECT 1
        FROM users
        WHERE id=NEW.user_id
        AND role='student'
    ) THEN
        RAISE EXCEPTION 'application student must have role=student';
    END IF;

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
""")
    event.listen(db.metadata, "after_create", application_data_check)

    # trigger: enforces the allowed status transitions of an application
    application_status_workflow = DDL("""
CREATE OR REPLACE FUNCTION check_application_status_workflow() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status='created' AND OLD.status NOT IN ('learning_agreement_pending', 'created') THEN
        RAISE EXCEPTION 'cannot move to created without an approved learning agreement';
    END IF;

    -- learning_agreement_pending -> pre_departure_completed
    IF NEW.status='pre_departure_completed' AND  OLD.status='created' THEN
        IF NOT EXISTS ( SELECT 1
                FROM uploaded_documents
                WHERE application_id=NEW.id
                AND document_type='learning_agreement'
                AND status='approved'
            ) THEN
            RAISE EXCEPTION 'cannot move to pre_departure_completed without an approved learning agreement';
        END IF;

        IF EXISTS (SELECT 1
            FROM mapped_exams
            WHERE application_id=NEW.id
            AND status<>'approved'
            ) THEN
            RAISE EXCEPTION 'cannot move to pre_departure_completed: all mapped exams must be approved';
        END IF;
    ELSEIF NEW.status='pre_departure_completed' AND OLD.status<>'learning_agreement_pending' THEN
        RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
    END IF;

    -- pre_departure_completed -> mobility_ongoing
    IF NEW.status='mobility_ongoing' AND OLD.status<>'pre_departure_completed' THEN
        RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
    END IF;

    -- mobility_ongoing -> exam_recognition
    IF NEW.status='exam_recognition' AND OLD.status='mobility_ongoing' THEN
        UPDATE mapped_exams
        SET status='pending'
        WHERE application_id=NEW.id;
    ELSEIF NEW.status='exam_recognition' AND OLD.status<>'mobility_ongoing' THEN
        RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
    END IF;

    IF NEW.status='closed' AND OLD.status='exam_recognition' THEN
        IF NOT EXISTS (SELECT 1
            FROM uploaded_documents
            WHERE application_id=NEW.id
            AND document_type='transcript'
            AND status='approved'
            ) THEN
            RAISE EXCEPTION 'approved transcript of records required';
        END IF;

        IF EXISTS(SELECT 1
                FROM mapped_exams
                WHERE application_id=NEW.id
                AND grade IS NULL
                OR grade=-1
                OR status <> 'approved'
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
""")
    event.listen(db.metadata, "after_create", application_status_workflow)

    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'semester': self.semester,
            'status': self.status,
            'date_submitted': self.date_submitted.isoformat() if self.date_submitted else None,
            'date_arrived': self.date_arrived.isoformat() if self.date_arrived else None,
            'date_departure': self.date_departure.isoformat() if self.date_departure else None,
            'notes': self.notes,
            'referent_id': self.referent_id,
            'sending_institution': self.sending_institution,
            'host_institution': self.host_institution,
            'user_id': self.user_id,
        }


class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    id_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('code', 'id_institution'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'credits': self.credits,
            'id_institution': self.id_institution,
        }


class MappedExam(db.Model):
    __tablename__ = 'mapped_exams'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    date_passed = db.Column(db.Date, nullable=True)
    grade = db.Column(db.Integer, default=-1)
    status = db.Column(db.String(32), nullable=False, default='pending')
    decision_date = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, default='')
    previous_id = db.Column(db.Integer, nullable=False, default=-1)
    host_exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    sending_exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        db.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='valid_status'),
        db.CheckConstraint("grade = -1 OR (grade > 17 AND grade <= 30)", name='valid_grade'),
        db.CheckConstraint(
            '(grade = -1 AND date_passed IS NULL) OR (grade <> -1 AND date_passed IS NOT NULL)',
            name='valid_grade_date'
        ),
        db.UniqueConstraint('application_id', 'sending_exam_id'),
        db.UniqueConstraint('application_id', 'host_exam_id'),
    )

    # trigger: host/sending exams must belong to the application's institutions
    mapped_exam_institutions_check = DDL("""
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

    IF host_exam_inst <> app_host_inst THEN
        RAISE EXCEPTION 'host_exam_id institution does not match application host_institution';
    END IF;

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
""")
    event.listen(db.metadata, "after_create", mapped_exam_institutions_check)

    # trigger: stamp decision_date when a mapped exam is approved/rejected
    mapped_exam_update_status_check = DDL("""
CREATE OR REPLACE FUNCTION check_update_status_mapped_exams() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    IF NEW.status IN ('approved', 'rejected') THEN
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
""")
    event.listen(db.metadata, "after_create", mapped_exam_update_status_check)


class UploadedDocument(db.Model):
    __tablename__ = 'uploaded_documents'

    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    status = db.Column(db.String(32), nullable=False, default='pending')
    decision_date = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, default='')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        db.CheckConstraint("document_type IN ('learning_agreement', 'transcript')", name='valid_type'),
        db.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='valid_status'),
    )

    # trigger: on INSERT of a document, validate/advance the associated application
    applicaiton_update_on_upload = DDL("""
CREATE OR REPLACE FUNCTION update_application_on_upload() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    SELECT status
        INTO app_status
        FROM applications
        WHERE id = NEW.application_id;

    IF NEW.document_type = 'learning_agreement' THEN
        IF app_status NOT IN ('created','learning_agreement_pending') THEN
            RAISE EXCEPTION 'new learning agreement document cannot be changed while the application is in % status', app_status;
        END IF;

        IF app_status = 'created' THEN
            UPDATE applications SET status='learning_agreement_pending' WHERE id=NEW.application_id;
        END IF;
    ELSE
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
    EXECUTE FUNCTION update_application_on_upload();
""")
    event.listen(db.metadata, "after_create", applicaiton_update_on_upload)

    # trigger: stamp decision_date when a document is approved/rejected
    document_status_update_check = DDL("""
CREATE OR REPLACE FUNCTION check_document_status_update() RETURNS TRIGGER AS $$
DECLARE
    app_status VARCHAR(32);
BEGIN
    SELECT status INTO app_status
    FROM applications
    WHERE id = NEW.application_id;

    IF NEW.status IN ('approved', 'rejected') THEN
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
""")
    event.listen(db.metadata, "after_create", document_status_update_check)


class PartnerInstitution(db.Model):
    __tablename__ = 'partner_institution'

    id = db.Column(db.Integer, primary_key=True)
    id_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    id_partner_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        db.CheckConstraint('id_institution <> id_partner_institution', name='self_partner'),
        db.UniqueConstraint('id_institution', 'id_partner_institution'),
    )

    # trigger: keep the partnership symmetrical by mirroring the reciprocal row
    partner_institution_symmetry = DDL("""
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
""")
    event.listen(db.metadata, "after_create", partner_institution_symmetry)


class LAModification(db.Model):
    __tablename__ = 'la_modifications'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='pending')
    decision_date = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, default='')
    document_id = db.Column(db.Integer, db.ForeignKey('uploaded_documents.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)

    __table_args__ = (
        db.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='valid_modification_status'),
    )

    # trigger: stamp decision_date when a modification is approved/rejected
    la_modification_decision_date = DDL("""
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
""")
    event.listen(db.metadata, "after_create", la_modification_decision_date)

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'description': self.description,
            'status': self.status,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
            'notes': self.notes,
            'document_id': self.document_id,
        }


class LAModificationExam(db.Model):
    # typed snapshot of the mapped_exams set as it was BEFORE the modification
    __tablename__ = 'la_modification_exams'

    id = db.Column(db.Integer, primary_key=True)
    modification_id = db.Column(db.Integer, db.ForeignKey('la_modifications.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    host_exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    sending_exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    grade = db.Column(db.Integer, default=-1)
    date_passed = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(32), nullable=False, default='pending')
    notes = db.Column(db.Text, default='')
    decision_date = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('modification_id', 'sending_exam_id'),
        db.UniqueConstraint('modification_id', 'host_exam_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'modification_id': self.modification_id,
            'host_exam_id': self.host_exam_id,
            'sending_exam_id': self.sending_exam_id,
            'grade': self.grade,
            'date_passed': self.date_passed.isoformat() if self.date_passed else None,
            'status': self.status,
            'notes': self.notes,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
        }
