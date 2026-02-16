from bson import ObjectId
import random
import globals  

tracks = globals.tracks
reviews = globals.reviews


usernames = ["paddyb", "api_user", "golf_guy", "tester1", "musicfan", "devuser"]
texts = [
    "Brilliant track, love the sound!",
    "Pretty average but okay overall.",
    "Didnt really enjoy this one.",
    "Absolute banger!",
    "Nice beat, good for study sessions.",
    "Underrated song with solid rhythm."
]

track_list = list(tracks.find().limit(100))

count = 0
for t in track_list:
    track_id = t["track_id"]
    num_reviews = random.randint(1, 3)  
    for _ in range(num_reviews):
        review_doc = {
            "_id": ObjectId(),
            "username": random.choice(usernames),
            "text": random.choice(texts),
            "rating": random.randint(1, 5),
            "track_id": track_id
        }
        reviews.insert_one(review_doc)
        count += 1

print(f"✅ Inserted {count} reviews for {len(track_list)} tracks.")
