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
    email  = db.Column(db.String(255))
    password_hash  = db.Column(db.String(255))
    role = db.Column(db.String(50))
    firstname = db.Column(db.String(255))
    lastname = db.Column(db.String(255))
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
    sending_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    host_institution = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'semester': self.semester,
            'status': self.status,
            'sending_institution': self.sending_institution,
            'host_institution': self.host_institution,
            'user_id': self.user_id,
            'referent_id': self.referent_id
        }
