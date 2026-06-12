import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
from sqlalchemy import text

# import db initialized
from models import db

# import routes
from routes.users import users_blueprint
from routes.applications import applications_blueprint
from routes.api import api_blueprint
from routes.exams import exams_blueprint
from routes.institutions import institutions_blueprint

# load env variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app) # allow traffic from angular

# database config
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False;

db.init_app(app)
migrate = Migrate(app, db)

# register external ruotes
app.register_blueprint(users_blueprint, url_prefix="/api")
app.register_blueprint(applications_blueprint, url_prefix="/api")
app.register_blueprint(exams_blueprint, url_prefix="/api")
app.register_blueprint(institutions_blueprint, url_prefix="/api")
app.register_blueprint(api_blueprint)

@app.route("/")
def index():
    "Health check"
    result = db.session.execute(
        text("SELECT current_database() AS database_name")
    ).mappings().one()
    return jsonify(
        {
            "status": "ok",
            "message": "API is running",
            "database_name": result["database_name"],
        }
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
