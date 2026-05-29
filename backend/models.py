from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'firstname': self.firstname,
            'lastname': self.lastname
        }
