from flask import Flask, render_template
from flask_socketio import SocketIO, send
from sense_hat import SenseHat
import subprocess
import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

#=======================================================================
#               index.html
#=======================================================================
@app.route('/')
def index():
    """Serve the index HTML"""
    return render_template('index.html')

#=======================================================================
#               socketio ( websocket )
#=======================================================================
@socketio.on('message')
def handle_message(message):
    print("create")
    print("message:" + message)
    #emit('mess_from_server', message)
    send(message,broadcast=True)

#=======================================================================        
if __name__ == '__main__':
    socketio.run(app, host='192.168.1.111', debug=True)
