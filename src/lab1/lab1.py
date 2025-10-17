#!/usr/bin/env python

# Import libraries
import socketio
import eventlet
from flask import Flask
import autodrive
import math

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
p = .45
d = .01

def determineTurn(lidar_data):
    global last_dif
    
    try :
        right_dist = dist(lidar_data[280], lidar_data[200], 20 * RADIANS_PER_ENTRY)
        left_dist = dist(lidar_data[800], lidar_data[880], 20 * RADIANS_PER_ENTRY)
        print(left_dist, right_dist, left_dist - right_dist)    
        k = left_dist - right_dist
        der = k - last_dif
        decision = p*k + d*der
        last_dif = k 
    except:
        decision = 0
    return decision

# Registering "Bridge" event handler for the server
@sio.on("Bridge")
def bridge(sid, data):
    if data:
        # Vehicle data
        f1tenth_1.parse_data(data, True)

        # Vehicle control
        f1tenth_1.throttle_command = 0.25  # [-1, 1]
        f1tenth_1.steering_command = determineTurn(f1tenth_1.lidar_range_array)  # generate your steering command 


        ########################################################################

        json_msg = f1tenth_1.generate_commands()

        try:
            sio.emit("Bridge", data=json_msg)
        except Exception as exception_instance:
            print(exception_instance)


################################################################################

if __name__ == "__main__":
    app = socketio.Middleware(
        sio, app
    )  # Wrap flask application with socketio's middleware
    eventlet.wsgi.server(
        eventlet.listen(("", 4567)), app
    )  # Deploy as an eventlet WSGI server
