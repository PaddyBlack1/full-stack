from pymongo import MongoClient
import json, os

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.musicdb
tracks = db.tracks

def create_database():
    base_path = r"C:\Users\pb005\Desktop\fullstack\lastfm_subset"
    count = 0

    for root, _, files in os.walk(base_path):
        for file in files:
            if not file.endswith(".json"):
                continue
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    print("Skipping invalid JSON:", file_path)
                    continue

            track_doc = {
                "artist": data.get("artist"),
                "title": data.get("title"),
                "track_id": data.get("track_id"),
                "tags": [t[0] for t in data.get("tags", [])[:5]],
                "timestamp": data.get("timestamp")
            }

            tracks.insert_one(track_doc)
            count += 1
            if count % 100 == 0:
                print(count, "tracks inserted")

    print("Import complete. Total tracks:", count)

create_database()