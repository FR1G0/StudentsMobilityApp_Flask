import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# import db initialized
from models import db

# import routes
from routes.users import users_blueprint
from routes.applications import applications_blueprint

# load env variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app) # allow traffic from angular

# database config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False;

db.init_app(app)

# register external ruotes
app.register_blueprint(users_blueprint)
app.register_blueprint(applications_blueprint)

@app.route("/")
def index():
    "Health check"
    return jsonify({"status":"ok", "message": "API is running"})

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
