import eventlet.monkey
eventlet.monkey.patch_all()  # Replace the eventlet monkey patch with this

from flask import Flask, render_template, request, jsonify # ... rest of imports
from flask_socketio import SocketIO

# ... other code ...

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")
# FIX: Force eventlet and allow origins for Railway
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
CORS(app)

# ---------------- DATABASE ----------------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://monisola:portfolio2026@cluster0.eaer1cp.mongodb.net/?appName=Cluster0")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["chatapp_db"]
messages_collection = mongo_db["messages"]

# ---------------- HELPERS ----------------
def get_all_messages():
    docs = list(messages_collection.find({}).sort("_id", 1))
    formatted = []
    for i, doc in enumerate(docs):
        formatted.append({
            "id": str(doc["_id"]),
            "name": doc.get("username", "Anonymous"),
            "body": doc.get("message", ""),
            "image": doc.get("image_data"), # We now store the string directly
            "time_display": doc.get("ts", ""),
            "line_index": i
        })
    return formatted

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/messages")
def api_messages():
    return jsonify(get_all_messages())

# ---------------- SOCKET ----------------
@socketio.on("send_message")
def handle_message(data):
    username = data.get("username", "Anonymous")
    message = data.get("message", "")
    image_data = data.get("image") # This is the base64 string from frontend

    if not message.strip() and not image_data:
        return

    ts = datetime.now().strftime("%I:%M %p")

    # SAVE TO DB (Stays forever even if Railway restarts)
    new_msg = {
        "ts": ts,
        "username": username,
        "message": message,
        "image_data": image_data, 
        "created_at": datetime.utcnow(),
    }
    result = messages_collection.insert_one(new_msg)

    # EMIT TO EVERYONE
    socketio.emit("receive_message", {
        "username": username,
        "message": message,
        "image": image_data,
        "time": ts
    })

@app.route("/ai_summary")
def ai_summary():
    msgs = get_all_messages()
    if not msgs:
        return jsonify({"summary": "No messages yet!"})
    
    summary = f"📊 Total messages: {len(msgs)}\n👥 Users: {len(set(m['name'] for m in msgs))}"
    return jsonify({"summary": summary})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
