# Chat App - Portfolio Project

A simple real-time chat application built with Flask, Flask-SocketIO, and SQLite.

## Features

- ✅ Real-time messaging with WebSockets
- ✅ Image upload support
- ✅ Mobile-responsive design
- ✅ Message search functionality
- ✅ AI-powered chat summary (statistics + preview)
- ✅ Media gallery (view all images)
- ✅ Message deletion (single or all)

## How to Run

1. **Install Python**: Make sure you have Python 3.7+ installed on your computer.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the server**:
   ```bash
   python app.py
   ```
4. **Open the app**: Go to `http://localhost:5000` in your browser.

## How to Test

1. **Sending Messages**:
   - Type your name (or leave blank for "Anonymous")
   - Write a message
   - Optional: Upload an image
   - Click "Send"

2. **Real-time Updates**:
   - Open the app in two different browser windows/tabs
   - Send a message from one and watch it appear in the other

3. **Search**:
   - Type a name or date in the search box
   - Click "Search" (matching messages will be highlighted in yellow and scrolled into view)

4. **AI Summary**:
   - Click the "🧠 AI" button
   - See: total messages, total users, most active user, and a conversation preview
   - Click outside the panel to close it

5. **Media Gallery**:
   - Click the "🖼 Media" button
   - See all images that have been uploaded
   - Click outside the panel to close it

6. **View All Messages & Delete**:
   - Go to `http://localhost:5000/all_messages`
   - To delete a single message: click the red trash can (🗑️) on it
   - To delete all messages: click "Delete all messages" at the bottom

## Tech Stack

- Backend: Flask, Flask-SocketIO, SQLite
- Frontend: Vanilla HTML/CSS/JavaScript, Socket.IO
