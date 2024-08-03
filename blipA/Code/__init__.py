from flask import Flask
from config import Config
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*")

from app import routes
