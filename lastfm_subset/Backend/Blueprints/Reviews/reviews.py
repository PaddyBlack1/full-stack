from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
import globals
from Blueprints.auth.auth import jwt_required, admin_required

reviews_bp = Blueprint("reviews_bp", __name__)

tracks = globals.tracks
reviews = globals.reviews

@reviews_bp.route("/api/v1.0/tracks/<string:id>/reviews", methods=["POST"])
def add_new_review(id):
    new_review = {
        "_id": ObjectId(),
        "username": request.form["username"],
        "text": request.form["text"],
        "rating": int(request.form["rating"]),
        "track_id": id
    }

    result = reviews.insert_one(new_review)

    if result.inserted_id:
        new_review_link = (
            f"http://localhost:5000/api/v1.0/tracks/{id}/reviews/{result.inserted_id}"
        )
        return make_response(jsonify({"url": new_review_link}), 201)
    return make_response(jsonify({"error": "Failed to add review"}), 500)


@reviews_bp.route("/api/v1.0/tracks/<string:id>/reviews", methods=["GET"])
def fetch_all_reviews(id):
    track = tracks.find_one({"track_id": id}, {"_id": 0, "track_id": 1})
    if not track:
        return make_response(jsonify({"error": "Track not found"}), 404)

    data_to_return = []
    for review in reviews.find({"track_id": id}):
        review["_id"] = str(review["_id"])
        data_to_return.append(review)

    return make_response(jsonify(data_to_return), 200)

@reviews_bp.route("/api/v1.0/tracks/<string:track_id>/reviews/<string:review_id>", methods=["GET"])
def fetch_one_review(track_id, review_id):
    try:
        review_obj_id = ObjectId(review_id)
    except Exception:
        return make_response(jsonify({"error": "Invalid review ID format"}), 400)

    review = reviews.find_one(
        {"_id": review_obj_id, "track_id": track_id},
        {"_id": 1, "username": 1, "text": 1, "rating": 1, "track_id": 1}
    )

    if not review:
        return make_response(jsonify({"error": "Track or review not found"}), 404)

    review["_id"] = str(review["_id"])
    return make_response(jsonify(review), 200)

@reviews_bp.route("/api/v1.0/tracks/<string:track_id>/reviews/<string:review_id>", methods=["PUT"])
def edit_review(track_id, review_id):
    try:
        review_obj_id = ObjectId(review_id)
    except Exception:
        return make_response(jsonify({"error": "Invalid review ID format"}), 400)

    if not all(k in request.form for k in ("username", "text", "rating")):
        return make_response(jsonify({"error": "Missing form data"}), 400)

    result = reviews.update_one(
        {"_id": review_obj_id, "track_id": track_id},
        {"$set": {
            "username": request.form["username"],
            "text": request.form["text"],
            "rating": int(request.form["rating"])
        }}
    )

    if result.matched_count == 0:
        return make_response(jsonify({"error": "Track or review not found"}), 404)

    edit_review_url = f"http://localhost:5000/api/v1.0/tracks/{track_id}/reviews/{review_id}"
    return make_response(jsonify({"url": edit_review_url}), 200)


@reviews_bp.route("/api/v1.0/tracks/<string:track_id>/reviews/<string:review_id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_review(track_id, review_id):
    try:
        review_obj_id = ObjectId(review_id)
    except Exception:
        return make_response(jsonify({"error": "Invalid review ID format"}), 400)

    result = reviews.delete_one({"_id": review_obj_id, "track_id": track_id})

    if result.deleted_count == 0:
        return make_response(jsonify({"error": "Track or review not found"}), 404)

    return make_response(jsonify({}), 204)

@reviews_bp.route("/api/v1.0/reviews/top", methods=["GET"])
def top_tracks_from_reviews():
    pipeline = [
        {"$group": {
            "_id": "$track_id",
            "average_rating": {"$avg": {"$toDouble": "$rating"}},
            "review_count": {"$sum": 1}
        }},
        {"$sort": {"average_rating": -1}},
        {"$limit": 10}
    ]
    results = list(reviews.aggregate(pipeline))

    for r in results:
        r["track_id"] = r.pop("_id")
        r["average_rating"] = round(r["average_rating"], 2)

    return make_response(jsonify(results), 200)

@reviews_bp.route("/api/v1.0/users/<string:username>/reviews", methods=["GET"])
def user_reviews(username):
    data = list(reviews.find({"username": username}))
    return make_response(jsonify(data), 200)
