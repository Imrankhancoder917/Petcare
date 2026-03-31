from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt
import re
from models.db import get_connection

auth_bp = Blueprint("auth", __name__)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "user").strip().lower()

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if not _valid_email(email):
        return jsonify({"error": "invalid email address"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400
    if role not in ("user", "volunteer", "admin"):
        role = "user"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({"error": "email already registered"}), 409
            hashed = _hash_password(password)
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, hashed, role),
            )
            new_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    token = create_access_token(identity=str(new_id), additional_claims={"role": role, "name": name})
    return jsonify({"message": "user created", "token": token, "role": role, "name": name}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, role, password FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
    finally:
        conn.close()

    if not user or not _check_password(password, user["password"]):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(
        identity=str(user["id"]),
        additional_claims={"role": user["role"], "name": user["name"]},
    )
    return jsonify({"token": token, "role": user["role"], "name": user["name"]}), 200
