import os
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger, swag_from

load_dotenv()

app = Flask(__name__)
CORS(app)
Swagger(app)

# ✅ DB Config
# app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ✅ User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

with app.app_context():
    db.create_all()

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\\.[^@]+", email)

# ✅ Register API
@app.route("/api/register", methods=["POST"])
@swag_from({
    'summary': 'Register new user',
    'description': 'Takes username, email, and password and creates a new user account.',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'example': 'johnwick'},
                'email': {'type': 'string', 'example': 'john@continental.com'},
                'password': {'type': 'string', 'example': 'supersecure123'}
            },
            'required': ['username', 'email', 'password']
        }
    }],
    'responses': {
        200: {'description': 'User registered successfully'},
        400: {'description': 'Missing or invalid fields'},
        409: {'description': 'Username or email already exists'}
    }
})
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists"}), 409

    hashed_pw = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 200

# ✅ Login API
@app.route("/api/login", methods=["POST"])
@swag_from({
    'summary': 'User login',
    'description': 'Login using username and password. Returns a success message.',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'example': 'johnwick'},
                'password': {'type': 'string', 'example': 'supersecure123'}
            },
            'required': ['username', 'password']
        }
    }],
    'responses': {
        200: {'description': 'Login successful'},
        400: {'description': 'Missing fields'},
        401: {'description': 'Invalid credentials'}
    }
})
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful"}), 200

# ✅ Home route
@app.route("/api/home", methods=["GET"])
@swag_from({
    'summary': 'Welcome route',
    'description': 'Basic route to check if server is alive.',
    'responses': {
        200: {'description': 'Welcome message'}
    }
})
def home():
    return jsonify({"message": "Welcome to the Home Page!"})

if __name__ == "__main__":
    app.run(debug=True)
