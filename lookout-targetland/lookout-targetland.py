#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code

# camera
from SoloCamera import SoloCamera
import cv2
import numpy as np
import threading

# server
from flask import Flask, Response, request, render_template

# drone control
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time, sys
import utm
import os

# If true, won't actually start motors
TEST_MODE = True
print "Running Lookout Targetland. TEST_MODE=%s" % TEST_MODE

# Global vehicle object represents drone or simulator
vehicle = None
homelocation_hacked = None
homelocation_local_hacked = None

def start_connect():
    global vehicle
    global homelocation_hacked
    global homelocation_local_hacked

    print 'Begin Connect'

    try:
        target = sys.argv[1] if len(sys.argv) >= 2 else 'tcp:127.0.0.1:5762'  #'udpin:0.0.0.0:14550'
        print 'Connecting to ' + target + '...'
        vehicle = connect(target, wait_ready=True)
    except Exception:
        print 'No simulator present, connecting to drone'
        target = sys.argv[1] if len(sys.argv) >= 2 else 'udpin:0.0.0.0:14550'  #'udpin:0.0.0.0:14550'
        print 'Connecting to ' + target + '...'
        vehicle = connect(target, wait_ready=True)

    # Reference for all commands/attributes
    print "Autopilot Firmware version: %s" % vehicle.version
    # print "Autopilot capabilities (supports ftp): %s" % vehicle.capabilities.ftp
    print "Global Location: %s" % vehicle.location.global_frame
    print "Global Location (relative altitude): %s" % vehicle.location.global_relative_frame
    print "Local Location: %s" % vehicle.location.local_frame    #NED
    print "Attitude: %s" % vehicle.attitude
    print "Velocity: %s" % vehicle.velocity
    print "GPS: %s" % vehicle.gps_0
    print "Groundspeed: %s" % vehicle.groundspeed
    print "Airspeed: %s" % vehicle.airspeed
    print "Gimbal status: %s" % vehicle.gimbal
    print "Battery: %s" % vehicle.battery
    print "EKF OK?: %s" % vehicle.ekf_ok
    print "Last Heartbeat: %s" % vehicle.last_heartbeat
    print "Rangefinder: %s" % vehicle.rangefinder
    print "Rangefinder distance: %s" % vehicle.rangefinder.distance
    print "Rangefinder voltage: %s" % vehicle.rangefinder.voltage
    print "Heading: %s" % vehicle.heading
    print "Is Armable?: %s" % vehicle.is_armable
    print "System status: %s" % vehicle.system_status.state
    print "Mode: %s" % vehicle.mode.name    # settable
    print "Armed: %s" % vehicle.armed    # settable

    # cmds = vehicle.commands
    # cmds.download()
    # cmds.wait_ready()

    # TODO: FIX THE ACTUAL HOME LOCATION
    homelocation_hacked = vehicle.location.global_frame
    homelocation_local_hacked = utm.from_latlon(homelocation_hacked.lat,\
                                                homelocation_hacked.lon)
    print " Home Location: %s" % homelocation_hacked
    print " Home Location Local: %s,%s,%s,%s" % homelocation_local_hacked

# Returns UTM in form (EASTING, NORTHING, ZONE NUMBER, ZONE LETTER)
def get_location_utm():
    l = vehicle.location.global_frame
    return utm.from_latlon(l.lat, l.lon)

def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    global vehicle, homelocation_hacked, homelocation_local_hacked

    print "Begin arm and takeoff"

    if TEST_MODE:
        return

    print "Basic pre-arm checks"
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print " Waiting for vehicle to initialise..."
        time.sleep(1)

    print "Arming motors"
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print " Waiting for arming..."
        time.sleep(1)

    print "Taking off!"
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print " Altitude: ", vehicle.location.global_relative_frame.alt
        #Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
            print "Reached target altitude"
            break
        time.sleep(1)

    vehicle.gimbal.rotate(-90,0,0)

# Return relative North, East offset of landing zone
def acquire_target_NED_location():
    global vehicle, homelocation_hacked, homelocation_local_hacked
    current_E,current_N,_,_=get_location_utm()

    dE = current_E - homelocation_local_hacked[0]
    dN = current_N - homelocation_local_hacked[1]
    return (dN, dE)

def land_control_velocity(dN, dE):
    global vehicle, homelocation_hacked, homelocation_local_hacked

    threshold = .1
    v = .1
    v_n = 0
    v_e = 0

    if (dN < -threshold):
        v_n = v
    if (dN > threshold):
        v_n = -v

    if (dE < -threshold):
        v_e = v
    if (dE > threshold):
        v_e = -v

    v_d = .3
    return (v_n, v_e, v_d)

def precision_land():
    global vehicle, homelocation_hacked, homelocation_local_hacked
    print "Begin Precision Land"

    if TEST_MODE:
        return

    print "Going home to Home Location: %s" % homelocation_hacked
    vehicle.gimbal.rotate(-90,0,0)
    above_home_loc = LocationGlobalRelative(homelocation_hacked.lat, \
                                            homelocation_hacked.lon, \
                                            10)
    vehicle.simple_goto(above_home_loc)

    # TODO Put loop here
    time.sleep(10)

    print "Lowering to 5 m"
    above_home_loc = LocationGlobalRelative(homelocation_hacked.lat, \
                                            homelocation_hacked.lon, \
                                            5)

    vehicle.simple_goto(above_home_loc, groundspeed=.3)

    # TODO Loop here
    time.sleep(10)

    # TODO Setting for land threshold
    while(vehicle.location.global_relative_frame.alt > .3):
        (dN, dE) = acquire_target_NED_location()
        (v_n, v_e, v_d) = land_control_velocity(dN, dE)

        print "dN: %s, dE: %s, v_n: %s, v_e: %s, v_d: %s" % (dN, dE, v_n, v_e, v_d)
        send_ned_velocity(v_n, v_e, v_d)
        time.sleep(.5)

    vehicle.mode = VehicleMode("LAND")

def send_ned_velocity(velocity_x, velocity_y, velocity_z):
    global vehicle, homelocation_hacked, homelocation_local_hacked
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,          # time_boot_ms (not used)
        0, 0,       # target system, target component
        1,          # NED frame constant
        0b0000111111000111, # type_mask (only speeds enabled)
        0, 0, 0,    # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
        0, 0, 0,    # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)       # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    vehicle.send_mavlink(msg)

#### Start Server Code
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kolibri_secret_key'

# To handle debug video stream

#open HDMI-In as a video capture device
#BE SURE YOU HAVE RUN `SOLO VIDEO ACQUIRE`
video_capture = SoloCamera()

def get_frame():
    # video_capture.clear()
    ret, frame = video_capture.read()
    ret, jpeg = cv2.imencode('.jpg', frame)
    return jpeg.tostring()

@app.route('/')
def index():
    return render_template('index.html')

def gen():
    while True:
        frame = get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# Actual takeoff/land endpoints
@app.route('/api/arm_takeoff_endpoint', methods=['POST'])
def arm_takeoff_endpoint():
    print "Got POST request to arm_takeoff_endpoint"
    response_message = "Unknown Error"

    if vehicle is not None:
        if (homelocation_hacked is not None) and (homelocation_local_hacked is not None):
            arm_and_takeoff(15)
            response_message = "Takeoff Successful"
    else:
        response_message = "Takeoff Failed: Vehicle was None"

    return Response(response_message,
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/land_endpoint', methods=['POST'])
def land_endpoint():
    print "Got POST request to land_endpoint"

    precision_land()

    print "Close vehicle object"
    vehicle.close()
    return Response("Land request recieved",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})
#### End Server Code

# Run Script
app.run(host='0.0.0.0', port=5000, debug=False)

start_connect()
