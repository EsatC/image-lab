"""
ImageLab — Authentication Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # --- Validation ---
    errors = []
    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters.")
    if not email or "@" not in email:
        errors.append("A valid email is required.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if errors:
        return jsonify({"errors": errors}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"errors": ["Username already taken."]}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"errors": ["Email already registered."]}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"user": user.to_dict(), "access_token": token}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"errors": ["Invalid credentials."]}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"user": user.to_dict(), "access_token": token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return current user info."""
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if user is None:
        return jsonify({"errors": ["User not found."]}), 404
    return jsonify({"user": user.to_dict()}), 200
