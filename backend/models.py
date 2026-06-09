from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# NOTE: : each model has predefined functions
# User.query.all()        
# User.query.get(id)     
# User.query.filter_by(name='Joe').first()
# User.query.filter(User.age > 18).all()


#  user model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email  = db.Column(db.String(255), unique=True, nullable=False)
    password_hash  = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    id_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'id_institution': self.id_institution
        }


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


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    date_submitted = db.Column(db.DateTime, nullable=False)
    sending_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    host_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'semester': self.semester,
            'status': self.status,
            'date_submitted': self.date_submitted.isoformat() if self.date_submitted else None,
            'sending_institution': self.sending_institution,
            'host_institution': self.host_institution,
            'user_id': self.user_id,
        }


class Exam(db.Model):
    __tablename__ = 'exams'

    code = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    id_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    credits = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'code': self.code,
            'name': self.name,
            'id_institution': self.id_institution,
            'credits': self.credits,
        }


class MappedExam(db.Model):
    __tablename__ = 'mapped_exams'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    exam_code = db.Column(db.String(20), db.ForeignKey('exams.code'), nullable=False)
    mapped_exam_code = db.Column(db.String(20), db.ForeignKey('exams.code'), nullable=False)


class UploadedDocument(db.Model):
    __tablename__ = 'uploaded_documents'

    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)


class PartnerInstitution(db.Model):
    __tablename__ = 'partner_institution'

    id = db.Column(db.Integer, primary_key=True)
    id_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    id_partner_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
