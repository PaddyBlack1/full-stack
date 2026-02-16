from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, make_response
from Blueprints.Tracks.tracks import tracks_bp
from Blueprints.Reviews.reviews import reviews_bp
from Blueprints.Users.users import users_bp
from Blueprints.auth.auth import auth_bp


app = Flask(__name__)


app.register_blueprint(tracks_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(debug=True)
