from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
import datetime, bcrypt
from functools import wraps
import globals
import os
from jwt import JWT
from jwt.jwk import OctetJWK

auth_bp = Blueprint("auth_bp", __name__)
users = globals.users
blacklist = globals.blacklist
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
jwt_handler = JWT()
jwt_key = OctetJWK(SECRET_KEY.encode("utf-8"))


def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("x-access-token")
        if not token:
            return make_response(jsonify({"message": "Token missing"}), 401)
        try:
            data = jwt_handler.decode(token, jwt_key, do_time_check=True)
        except Exception:
            return make_response(jsonify({"message": "Token invalid"}), 401)

        if blacklist.find_one({"token": token}):
            return make_response(jsonify({"message": "Token cancelled"}), 401)
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("x-access-token")
        try:
            data = jwt_handler.decode(token, jwt_key, do_time_check=True)
        except Exception:
            return make_response(jsonify({"message": "Token invalid"}), 401)
        if data.get("admin"):
            return func(*args, **kwargs)
        return make_response(jsonify({"message": "Admin access required"}), 401)
    return wrapper

@auth_bp.route("/api/v1.0/login", methods=["GET"])
def login():
    auth = request.authorization
    body = request.get_json(silent=True) or {}

    username = (auth.username if auth else None) or body.get("username")
    password = (auth.password if auth else None) or body.get("password")

    if not username or not password:
        return make_response(jsonify({"message": "Authentication required"}), 401)

    user = users.find_one({"username": username})
    if not user:
        return make_response(jsonify({"message": "Username or Password Incorrect"}), 401)

    stored_pw = user.get("password")
    if isinstance(stored_pw, str):
        stored_pw = stored_pw.encode("utf-8")
    try:
        password_ok = bcrypt.checkpw(password.encode("utf-8"), stored_pw)
    except Exception:
        return make_response(jsonify({"message": "Bad password"}), 401)

    if password_ok:
        exp_ts = int((datetime.datetime.utcnow() + datetime.timedelta(minutes=30)).timestamp())
        token = jwt_handler.encode({
            "user": username,
            "admin": user.get("admin", False),
            # python-jwt expects timestamp, not datetime object
            "exp": exp_ts
        }, jwt_key, alg="HS256")
        return jsonify({"token": token})
    return make_response(jsonify({"message": "Bad password"}), 401)

@auth_bp.route("/api/v1.0/logout", methods=["GET"])
@jwt_required
def logout():
    token = request.headers.get("x-access-token")
    blacklist.insert_one({"token": token})
    return jsonify({"message": "Logout successful"})

@auth_bp.route("/api/v1.0/secure", methods=["GET"])
@jwt_required
def secure():
    return jsonify({"message": "You are logged in"})

@auth_bp.route("/api/v1.0/admin", methods=["DELETE"])
@jwt_required
@admin_required
def admin_only():
    return jsonify({"message": "Admin access granted"})
