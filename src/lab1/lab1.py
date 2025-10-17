#!/usr/bin/env python

# Import libraries
import socketio
import eventlet
from flask import Flask
import autodrive
import math
import warnings

################################################################################

# Initialize vehicle(s)
f1tenth_1 = autodrive.F1TENTH()
f1tenth_1.id = "V1"

# Initialize the server
sio = socketio.Server()

# Flask (web) app
app = Flask(__name__)  # '__main__'


# Registering "connect" event handler for the server
@sio.on("connect")
def connect(sid, environ):
    print("Connected!")

RADIANS_PER_ENTRY = .004

def dist(a, b, theta):
    alpha = math.atan((a * math.cos(theta)  - b)/ (a * math.sin(theta)))
    distance = b * math.sin(alpha)
    return distance

last_dif = 0
p = .5
d = .17

def determineTurn(lidar_data):
    global last_dif
    
    try :
        right_dist = dist(lidar_data[260], lidar_data[180], 20 * RADIANS_PER_ENTRY)
        left_dist = dist(lidar_data[820], lidar_data[900], 20 * RADIANS_PER_ENTRY)
        print(left_dist, right_dist, left_dist - right_dist)    
        k = left_dist - right_dist
        der = k - last_dif
        decision = p*k + d*der
        last_dif = k 
    except Exception:
        decision = -.1
        return decision
    return decision

acceleration_cap = .5
accel_floor = .25
accel = acceleration_cap

def determineThrottle(steering):
    global accel
    mag = abs(steering)
    if (accel < acceleration_cap):
        accel = accel + .05
    if mag > .12:
        accel = accel - .1
    if (accel < accel_floor):
        accel = accel_floor
    return accel

def crash(f1tenth):
    if (f1tenth.lidar_range_array[540] < .5):
        f1tenth.throttle_command = -.1
        f1tenth.steering_command = 10


# Registering "Bridge" event handler for the server
@sio.on("Bridge")
def bridge(sid, data):
    if data:
        # Vehicle data
        f1tenth_1.parse_data(data, True)

        # Vehicle control
        f1tenth_1.steering_command = determineTurn(f1tenth_1.lidar_range_array)  # generate your steering command 
        f1tenth_1.throttle_command = determineThrottle(f1tenth_1.steering_command)  # [-1, 1]
        crash(f1tenth_1)
        ########################################################################

        json_msg = f1tenth_1.generate_commands()

        try:
            sio.emit("Bridge", data=json_msg)
        except Exception as exception_instance:
            print(exception_instance)


################################################################################

if __name__ == "__main__":
    warnings.filterwarnings("error")
    app = socketio.Middleware(
        sio, app
    )  # Wrap flask application with socketio's middleware
    eventlet.wsgi.server(
        eventlet.listen(("", 4567)), app
    )  # Deploy as an eventlet WSGI server
