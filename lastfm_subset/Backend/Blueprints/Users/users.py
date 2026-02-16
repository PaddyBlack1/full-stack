from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
from  Blueprints.auth.auth import jwt_required, admin_required


import bcrypt
import globals

users_bp = Blueprint("users_bp", __name__)
users = globals.users

@users_bp.route("/api/v1.0/users", methods=["POST"])
def add_user():
    favourites = request.form.getlist("favourites") or []

    if "password" not in request.form:
        return make_response(jsonify({"error": "Password required"}), 400)

    password = request.form["password"].encode("utf-8")
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    new_user = {
        "username": request.form["username"],
        "email": request.form["email"],
        "password": hashed_password,
        "favourites": favourites,
        "admin": request.form.get("admin", "False").lower() == "true"
    }

    user_id = users.insert_one(new_user).inserted_id
    return jsonify({"_id": str(user_id)}), 201

@users_bp.route("/api/v1.0/users", methods=["GET"])
@jwt_required
@admin_required
def get_all_users():
    data_to_return = []
    for user in users.find():
        user["_id"] = str(user["_id"])
        del user["password"]  
        data_to_return.append(user)
    return jsonify(data_to_return)

@users_bp.route("/api/v1.0/users/<user_id>", methods=["GET"])
@jwt_required
@admin_required
def get_user(user_id):
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return make_response(jsonify({"error": "User not found"}), 404)
    user["_id"] = str(user["_id"])
    del user["password"]
    return jsonify(user)

@users_bp.route("/api/v1.0/users/<user_id>", methods=["PUT"])
@jwt_required
@admin_required
def update_user(user_id):
    favourites = request.form.getlist("favourites") or []

    password = request.form.get("password")
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()) if password else None

    updated_user = {
        "username": request.form.get("username"),
        "email": request.form.get("email"),
        "favourites": favourites if favourites else None,
        "password": hashed_password,
        "admin": request.form.get("admin")
    }

    updated_user = {k: v for k, v in updated_user.items() if v is not None}
    result = users.update_one({"_id": ObjectId(user_id)}, {"$set": updated_user})

    if result.matched_count == 0:
        return make_response(jsonify({"error": "User not found"}), 404)
    return jsonify({"message": "User updated"})

@users_bp.route("/api/v1.0/users/<user_id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_user(user_id):
    result = users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        return make_response(jsonify({"error": "User not found"}), 404)
    return make_response(jsonify({}), 204)
