import eventlet
eventlet.monkey_patch()

from app import socketio, app

if __name__ == "__main__":
    socketio.run(app)