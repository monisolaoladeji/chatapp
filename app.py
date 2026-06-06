import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")
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
            "image": doc.get("image_data"),
            "time_display": doc.get("ts", ""),
            "line_index": i
        })
    return formatted

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/all_messages")
def all_messages():
    return render_template("all_messages.html")

@app.route("/api/messages", methods=["GET"])
def api_messages():
    return jsonify(get_all_messages())

@app.route("/api/messages", methods=["POST"])
def send_message():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "Anonymous")
    message = data.get("message", "")
    image_data = data.get("image")

    if not message.strip() and not image_data:
        return jsonify({"error": "Message or image required"}), 400

    ts = datetime.now().strftime("%I:%M %p")

    new_msg = {
        "ts": ts,
        "username": username,
        "message": message,
        "image_data": image_data,
        "created_at": datetime.utcnow(),
    }
    result = messages_collection.insert_one(new_msg)

    return jsonify({
        "id": str(result.inserted_id),
        "name": username,
        "body": message,
        "image": image_data,
        "time_display": ts
    }), 201

@app.route("/ai_summary")
def ai_summary():
    msgs = get_all_messages()
    if not msgs:
        return jsonify({"summary": "No messages yet!"})
    
    summary = f"📊 Total messages: {len(msgs)}\n👥 Users: {len(set(m['name'] for m in msgs))}"
    return jsonify({"summary": summary})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
