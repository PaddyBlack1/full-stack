from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
import globals
import requests 
from spotify_utils import get_spotify_token
from Blueprints.auth.auth import jwt_required, admin_required

tracks_bp = Blueprint("tracks_bp", __name__)

tracks = globals.tracks
reviews = globals.reviews

@tracks_bp.route("/api/v1.0/tracks", methods=["GET"])
def show_all_tracks():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for track in tracks.find().skip(page_start).limit(page_size):
        track['_id'] = str(track['_id'])
        track_reviews = []
        for review in reviews.find({"track_id": track['track_id']}):
            review['_id'] = str(review['_id'])
            track_reviews.append(review)
        track['reviews'] = track_reviews
        data_to_return.append(track)

    total_count = tracks.count_documents({})
    total_pages = (total_count + page_size - 1) // page_size if page_size else 1

    return make_response(jsonify({
        "items": data_to_return,
        "page": page_num,
        "page_size": page_size,
        "total": total_count,
        "total_pages": total_pages
    }), 200)

@tracks_bp.route("/api/v1.0/tracks/<string:id>", methods=["GET"])
def show_one_track(id):
    track = tracks.find_one({'track_id': id})
    if track is not None:
        track['_id'] = str(track['_id'])
        track_reviews = []
        for review in reviews.find({"track_id": id}):
            review['_id'] = str(review['_id'])
            track_reviews.append(review)
        track['reviews'] = track_reviews
        return make_response(jsonify(track), 200)
    else:
        return make_response(jsonify({"error": "Track not found"}), 404)

@tracks_bp.route("/api/v1.0/tracks", methods=["POST"])
@jwt_required
@admin_required
def add_track():
    if "artist" in request.form and \
       "title" in request.form and \
       "track_id" in request.form:
        new_track = {
            "artist": request.form["artist"],
            "title": request.form["title"],
            "track_id": request.form["track_id"],
            "tags": [],
            "reviews": []
        }
        new_track_id = tracks.insert_one(new_track)
        new_track_link = "http://localhost:5000/api/v1.0/tracks/" + str(new_track_id.inserted_id)
        return make_response(jsonify({"url": new_track_link}), 201)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 400)
    
@tracks_bp.route("/api/v1.0/tracks/<string:id>", methods=["PUT"])
@jwt_required
@admin_required
def edit_track(id):
    if "artist" in request.form and "title" in request.form and "track_id" in request.form:
        result = tracks.update_one(
            {"track_id": id},
            {"$set": {
                "artist": request.form["artist"],
                "title": request.form["title"],
                "track_id": request.form["track_id"]
            }}
        )
        if result.matched_count == 0:
            return make_response(jsonify({"error": "Track not found"}), 404)
        return make_response(jsonify({"message": "Track updated"}), 200)
    return make_response(jsonify({"error": "Missing form data"}), 400)


@tracks_bp.route("/api/v1.0/tracks/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_track(id):
    result = tracks.delete_one({"track_id": id})
    if result.deleted_count == 1:
        return make_response(jsonify({}), 204)
    else:
        return make_response(jsonify({"error": "Track not found"}), 404)
    
@tracks_bp.route("/api/v1.0/tracks/<track_id>/average", methods=["GET"])
def get_average_rating(track_id):
    reviews_cursor = reviews.find({"track_id": track_id}, {"rating": 1, "_id": 0})
    ratings = [float(r["rating"]) for r in reviews_cursor if "rating" in r]
    
    if not ratings:
        return make_response(jsonify({"track_id": track_id, "average_rating": None, "count": 0}), 200)
    
    avg_rating = round(sum(ratings) / len(ratings), 2)
    return make_response(jsonify({
        "track_id": track_id,
        "average_rating": avg_rating,
        "count": len(ratings)
    }), 200)

@tracks_bp.route("/api/v1.0/tracks/top", methods=["GET"])
def top_tracks():
    limit = 10
    try:
        limit = int(request.args.get("limit", 10))
    except Exception:
        limit = 10

    top_cursor = tracks.find().sort("average_rating", -1).limit(limit)
    results = []
    for t in top_cursor:
        t["_id"] = str(t["_id"])
        results.append(t)

    return make_response(jsonify(results), 200)

@tracks_bp.route("/api/v1.0/tracks/search", methods=["GET"])
def search_tracks():
    q = request.args.get("q")
    results = tracks.find({
        "$or": [
            {"artist": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},   
            {"title": {"$regex": q, "$options": "i"}}
        ]
    }, {"_id": 0})   

    return make_response(jsonify(list(results)), 200)

@tracks_bp.route("/api/v1.0/spotify/search", methods=["GET"])
def spotify_search():
    q = request.args.get("q", "")
    token = get_spotify_token()
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": q, "type": "track", "limit": 10},
    )

    if r.status_code != 200:
        return make_response(jsonify(r.json()), r.status_code)

    data = r.json()
    items = data.get("tracks", {}).get("items", [])
    return make_response(jsonify(items), 200)



