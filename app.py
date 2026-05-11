from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId

import os
import uuid
import base64
from datetime import datetime

# ---------------- SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

load_dotenv()

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://monisola:portfolio2026@cluster0.eaer1cp.mongodb.net/?appName=Cluster0"
)
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "chatapp_db")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
messages_collection = mongo_db["messages"]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-this-in-production")
socketio = SocketIO(app, cors_allowed_origins="*")

CORS(app)

# ---------------- DATABASE ----------------
def init_db():
    messages_collection.create_index([("ts", ASCENDING)])
    messages_collection.create_index([("username", ASCENDING)])

init_db()

# ---------------- LOAD MESSAGES ----------------
def load_messages(with_index=False):
    docs = list(messages_collection.find({}).sort("_id", 1))
    messages = []

    for i, doc in enumerate(docs):
        msg = {
            "id": str(doc["_id"]),
            "ts": doc.get("ts", ""),
            "username": doc.get("username", ""),
            "message": doc.get("message", ""),
            "image": doc.get("image"),
        }
        if with_index:
            msg["line_index"] = i
        messages.append(msg)
    return messages

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/all_messages")
def all_messages():
    msgs = load_messages(with_index=True)
    formatted = []
    for m in msgs:
        formatted.append({
            "name": m["username"],
            "body": m["message"],
            "image_url": f"/uploads/{m['image']}" if m["image"] else None,
            "time_display": m["ts"],
            "line_index": m["line_index"],
            "id": m["id"]
        })
    return render_template("all_messages.html", messages=formatted)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/api/messages")
def api_messages():
    msgs = load_messages(with_index=True)
    formatted = []
    for m in msgs:
        formatted.append({
            "name": m["username"],
            "body": m["message"],
            "image_url": f"/uploads/{m['image']}" if m["image"] else None,
            "time_display": m["ts"],
            "line_index": m["line_index"],
            "id": m["id"]
        })
    return jsonify(formatted)

# ---------------- DELETE ROUTES ----------------
@app.route("/delete/<int:line_index>")
def delete_message(line_index):
    msgs = load_messages()
    if 0 <= line_index < len(msgs):
        msg_id = msgs[line_index]["id"]
        messages_collection.delete_one({"_id": ObjectId(msg_id)})
    return redirect(url_for("all_messages"))

@app.route("/delete_all")
def delete_all_messages():
    messages_collection.delete_many({})
    return redirect(url_for("all_messages"))

# ---------------- SOCKET ----------------
@socketio.on("send_message")
def handle_message(data):
    username = data.get("username", "Anonymous")
    message = data.get("message", "")
    image_data = data.get("image")

    if not message.strip() and not image_data:
        return

    ts = datetime.now().strftime("%I:%M %p")

    image_filename = None

    # ---------------- IMAGE SAVE ----------------
    if image_data and image_data.startswith("data:image"):
        header, encoded = image_data.split(",", 1)
        ext = header.split("/")[1].split(";")[0]

        image_filename = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(UPLOAD_DIR, image_filename)

        with open(path, "wb") as f:
            f.write(base64.b64decode(encoded))

    # ---------------- SAVE DB ----------------
    messages_collection.insert_one(
        {
            "ts": ts,
            "username": username,
            "message": message,
            "image": image_filename,
            "created_at": datetime.utcnow(),
        }
    )

    # ---------------- EMIT ----------------
    socketio.emit("receive_message", {
        "username": username,
        "message": message,
        "image_url": f"/uploads/{image_filename}" if image_filename else None,
        "time": ts
    })

# ---------------- AI ----------------
@app.route("/ai_summary")
def ai_summary():
    messages = load_messages()

    if not messages:
        return jsonify({"summary": "No messages yet! Start chatting to see a summary."})

    total_messages = len(messages)
    users = {}
    for m in messages:
        if m["username"] not in users:
            users[m["username"]] = 0
        users[m["username"]] += 1
    
    most_active_user = max(users.items(), key=lambda x: x[1])[0]
    num_users = len(users)
    
    text_summary = " ".join([m["message"] for m in messages if m["message"]])
    first_50_words = " ".join(text_summary.split()[:50])
    
    summary_parts = []
    summary_parts.append(f"📊 Total messages: {total_messages}")
    summary_parts.append(f"👥 Total users: {num_users}")
    summary_parts.append(f"🏆 Most active: {most_active_user}")
    if first_50_words:
        summary_parts.append(f"📝 Conversation preview: {first_50_words}...")
    
    return jsonify({"summary": "\n".join(summary_parts)})

# ---------------- RUN ----------------
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
