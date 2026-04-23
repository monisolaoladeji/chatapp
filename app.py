from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_socketio import SocketIO

import json
import os
import uuid
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "messages.txt")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_IMAGE_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "gif", "webp"})
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
socketio = SocketIO(app)


def allowed_image(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def save_message_image(file_storage):
    if not file_storage or not getattr(file_storage, "filename", None):
        return None

    raw_name = file_storage.filename
    if not allowed_image(raw_name):
        return None

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = raw_name.rsplit(".", 1)[1].lower()
    stored = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, stored)

    file_storage.save(path)
    return stored


def load_messages():
    if not os.path.exists(FILE_PATH):
        return []

    messages = []
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                messages.append(json.loads(line))
            except:
                pass
    return messages


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "")
    message = request.form.get("message", "")
    image = request.files.get("image")

    image_name = save_message_image(image)

    if not message.strip() and not image_name:
        return redirect(url_for("home"))

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "username": name,
        "message": message,
        "image": image_name
    }

    with open(FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return redirect(url_for("home"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/api/messages")
def api_messages():
    return jsonify(load_messages())


@socketio.on("send_message")
def handle_message(data):
    username = data.get("username", "Anonymous")
    message = data.get("message", "")

    if not message.strip():
        return

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "username": username,
        "message": message
    }

    with open(FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    socketio.emit("receive_message", record)


if __name__ == "__main__":
    socketio.run(app, debug=True)
