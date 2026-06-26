import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from config import SECRET_KEY
from state import state
from handlers.admin import register_admin_handlers
from handlers.team import register_team_handlers

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

register_admin_handlers(socketio)
register_team_handlers(socketio)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/team")
def team():
    return render_template("team.html")


@app.route("/obs")
def obs():
    return render_template("obs.html")


@socketio.on("connect")
def on_connect():
    emit("state_update", state)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
