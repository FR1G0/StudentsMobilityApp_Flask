from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# NOTE: db INIT
db = SQLAlchemy()

class Giocatore(db.Model):
    __tablename__ = 'giocatori'

    idg = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50))
    nazione = db.Column(db.String(50))
    annonascita = db.Column(db.String(4))

    def to_dict(self):
        return {
            'id': self.idg,
            'nome' : self.nome,
            'nazione': self.nazione,
            'annonascita': self.annonascita
        }

