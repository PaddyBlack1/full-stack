from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.musicdb

tracks = db.tracks
reviews = db.reviews
users = db.users
blacklist = db.blacklist

