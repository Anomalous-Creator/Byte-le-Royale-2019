import os
import datetime
from flask import Flask, request, redirect, url_for, g, Response
from flask_cors import CORS
from flask_pymongo import PyMongo
from functools import wraps
from bson import json_util
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

ADMIN_USERNAME = "BL_ROYALE_ADMIN"
ADMIN_PASSWORD = "bl_royale_admin_123"

UPLOAD_FOLDER = os.path.abspath('uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app)
mongo = PyMongo(app)



class RunState:
    none = 0
    running = 1
    queued = 2
    finished = 3
    failed = 4


# Auth
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    if username == ADMIN_USERNAME:
        return password == ADMIN_PASSWORD
    else:
        user = mongo.db.users.find_one({"username": username})

        if user:
            return check_password_hash(user.password_hash, password)
    return False


def check_admin(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# API Routes
@app.route("/announcements", methods=["GET"])
def get_announcements():
    announcements = [a for a in mongo.db.announcements.find()]

    return Response(
        json_util.dumps({"announcements": announcements}),
        mimetype="application/json"
    )


@app.route("/announcements", methods=["POST"])
@requires_admin
def add_announcement():
    data = request.json

    if "message" not in data:
        raise Exception("Key 'message' not present in payload.")

    if "title" not in data:
        raise Exception("Key 'title' not present in payload.")

    mongo.db.announcements.insert_one({
        "title": data["title"],
        "message": data["message"],
        "posted_date": str(datetime.datetime.now())
    })
    return "success"


@app.route("/announcements", methods=["DELETE"])
@requires_admin
def clear_announcements():
    all = request.args.get("all", False)

    if all:
        mongo.db.announcements.delete_many({})

    else:
        # Delete only one
        # TODO update to allow deleting one
        pass

    return "Success"



@app.route("/register", methods=["POST"])
def register_team():
    data = request.json

    if not mongo.db.config.find_one({"registration_open": True}):
        raise Exception("Registration is closed.")

    if "team_name" not in data:
        raise Exception("Team name is required.")

    if "password" not in data:
        raise Exception("Password is required.")

    team_name = data["team_name"]
    password = data["password"]

    if len("".join(team_name.split())):
        raise Exception("Team name cannot be empty or white space.")

    if len("".join(password.split())) < len(password):
        raise Exception("White space characters not allowed in passwords.")

    if len(password) < 6:
        raise Exception("Password must be at least 6 characters.")

    team_name = team_name.strip()

    if mongo.db.users.find_one({"username": team_name}):
        raise Exception(f"Team with name '{team_name}' already exists.")

    mongo.db.users.insert_one({
        "team_name": team_name,
        "password_hash": generate_password_hash(password),
        "submissions": []
    })

    return "success"


@app.route("/submissions", methods=["POST"])
@requires_auth
def upload_file():
    data = request.json
    user = get_user()

    team_name = user.username
    filename = "".join(x for x in team_name if x.isalnum()) + ".py"
    file_data = data["file_data"]

    # add submission to db
    submissions = user["submissions"]
    no_subs = len(submissions)
    time = datetime.datetime.now()
    submissions.append({
        "submission_no": no_subs,
        "name": f"Submission #{no_subs} ({time})",
        "file_name": filename,
        "upload_date": time,
        "stats": {}
    })

    mongo.db.users.update_one({"username": team_name}, {"$set": {
        "submissions": submissions
    }})


    # save file to disk
    with open(os.path.join(UPLOAD_FOLDER, filename), "w") as f:
        f.write(file_data)

    return True


@app.route("/submissions", methods=["GET"])
@requires_admin
def get_submissions():
    team_data = []
    for team in mongo.db.users.find():
        most_recent_submission = next(sorted(team["submissions"], key=lambda e:e["submission_no"], reverse=True))

        with open(os.path.join(UPLOAD_FOLDER, team["file_name"]), "r") as f:
            client_data = f.read()

        team_data.append({
            "team_name": team["username"],
            "client_data": client_data,
            "submission_info": most_recent_submission["submission_no"],
        })

    return Response(
        json_util.dumps({"teams_": team_data}),
        mimetype="application/json"
    )



@app.route("/report", methods=["POST"])
@requires_admin
def upload_game_info():
    """Used by the runner to upload the client logs, results, update leaderboards"""
    json = request.json




# ######### Helpers

def get_user():
    auth = request.authorization
    if not auth:
        return None

    user = mongo.db.users.find_one({"username": auth.username})

    return user


if __name__ == "__main__":
    app.run()
