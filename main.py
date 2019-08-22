from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from json import dumps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['MASTER_PASSWORD'] = 'fvc^0943!'

socketio = SocketIO(app)

class Device:
    def __init__(self, sid, name="?", temperature=None, heater=False):
        self.sid = sid
        self.name = name
        self.temperature = temperature
        self.heater = heater

    def __repr__(self):
        return "Device {0.sid}: name='{0.name}' T={0.temperature} heater={0.heater}".format(self)

    def toJSON(self):
        return {k:self.__getattribute__(k) for k in ['name','temperature','heater']}

class Status:
    def __init__(self):
        self.devices = []
        self.master = None
        self.set_point_high = 20.0
        self.set_point_low = 18.0

    @property
    def mean(self):
        try:
            mean = sum([d.temperature for d in self.devices if d.temperature is not None])/sum([1 for d in self.devices if d.temperature is not None])
        except ZeroDivisionError:
            mean = None
        return mean

    def add_device(self, sid, name):
        self.devices.append(Device(sid=sid, name=name))

    def remove_device(self, sid):
        if status[sid]:
            self.devices.remove(status[sid])

    def getJSON(self):
        return dumps([d.toJSON() for d in self.devices])

    def __getitem__(self, sid):
        for d in self.devices:
            if d.sid == sid:
                return d
        else:
            return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/master")
def master():
    return render_template("master.html")


#@socketio.on('connect')
#def connect():
#    print("Client connected!")
#    status.add_device(request.sid)
#    update()
#

@socketio.on('disconnect')
def disconnect():
    status.remove_device(request.sid)
    update()

@socketio.on('register_master')
def register_master(message):
    if message == app.config['MASTER_PASSWORD']:
        status.master = request.sid

@socketio.on('name')
def set_device_name(message):
    status.add_device(sid=request.sid, name=message)

@socketio.on('temperature')
def temperature(t):
    status[request.sid].temperature = t
    update()

@socketio.on('setpoint')
def setpoint(hi, lo):
    status.set_point_high = int(hi)
    status.set_point_low = int(lo)

def update():
    for d in status.devices:
        if d.temperature < status.set_point_low:
            d.heater = True
            emit('heater', d.heater, room=d.sid)
        elif d.temperature > status.set_point_high:
            d.heater = False
            emit('heater', d.heater, room=d.sid)
    if status.master is not None:
        emit('status', status.getJSON(), room=status.master)


if __name__ == '__main__':
    status = Status()
    socketio.run(app, debug=True)
