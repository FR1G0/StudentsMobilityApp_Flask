from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint, jsonify, request
from models import db, Giocatore

db = SQLAlchemy()

giocatori_bp = Blueprint('giocatori',__name__)

@giocatori_bp.route('/giocatori', methods=['GET'])
def all_giocatori():
    try:
        giocatori = Giocatore.query.all()
        all_g = [g.to_dict() for g in giocatori]
        return jsonify(all_g),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@giocatori_bp.route('/giocatori/<int:idg>', methods=["GET"])
def get_giocatore(idg):
    try:
        giocatore = Giocatore.query.get(idg)
        if not giocatore:
            return jsonify({}),500
        return jsonify(giocatore.to_dict()),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

