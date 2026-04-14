import os
from datetime import timedelta

from flask_jwt_extended import JWTManager
from flask_cors import CORS
from api.v1_0 import api_v1_0

from flask import Flask, jsonify

app = Flask(__name__)

app.config.from_envvar('CONFIGURATION_FILE')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

jwt = JWTManager(app)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"msg": "Token has expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"msg": "Token is invalid"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"msg": "Token is missing"}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({"msg": "Token has been revoked"}), 401

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(api_v1_0)


@app.route('/')
def hello_world():
    secret_key = app.config['SECRET_KEY']
    return f'Hello, World! The secret key is: {secret_key}'

from flask import send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    print("DIMINTA FILE:", filename)
    print("PATH:", os.path.join(UPLOAD_FOLDER, filename))
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    print(f"SECRET_KEY from os.getenv: {os.getenv('SECRET_KEY')}")
    app.run(host="0.0.0.0", port=5001, use_reloader=False)
    # app.run(debug=True, port=5001)
