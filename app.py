from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_socketio import SocketIO

import os
import uuid
import sqlite3
import base64
from datetime import datetime

# ---------------- SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        username TEXT,
        message TEXT,
        image TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOAD MESSAGES ----------------
def load_messages(with_index=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, ts, username, message, image FROM messages ORDER BY id ASC")
    rows = cur.fetchall()

    conn.close()

    messages = []
    for i, r in enumerate(rows):
        msg = {
            "ts": r[1],
            "username": r[2],
            "message": r[3],
            "image": r[4],
            "id": r[0]
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
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
    return redirect(url_for("all_messages"))

@app.route("/delete_all")
def delete_all_messages():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
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
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO messages (ts, username, message, image) VALUES (?, ?, ?, ?)",
        (ts, username, message, image_filename)
    )

    conn.commit()
    conn.close()

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
    socketio.run(app, debug=True, host="0.0.0.0")
