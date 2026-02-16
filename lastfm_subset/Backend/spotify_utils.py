# Backend/spotify_utils.py
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Always load .env that lives in the Backend folder
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

def get_spotify_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        # Optional debug print
        print("DEBUG spotify_utils: CLIENT_ID:", client_id, "SECRET set:", bool(client_secret))
        raise RuntimeError("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set in environment")

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"]
