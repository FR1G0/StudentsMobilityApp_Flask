from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint
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


class PartnerInstitution(db.Model):
    __tablename__ = 'partner_institution'

    id = db.Column(db.Integer, primary_key=True)
    id_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    id_partner_institution = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        db.CheckConstraint('id_institution <> id_partner_institution', name='self_partner'),
        db.UniqueConstraint('id_institution', 'id_partner_institution'),
    )


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
