#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code

# camera
# from SoloCamera import SoloCamera
# import cv2
# import numpy as np
# import threading

# CV
# import target_detect

# server
from flask import Flask, Response, request, render_template

# drone control
import FireflyUAV
import uavutil

#### Start Server Code
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kolibri_secret_key'


uav = FireflyUAV.FireflyUAV(TEST_MODE=False)
uav.connect()

# Actual takeoff/land endpoints
@app.route('/api/arm_takeoff', methods=['POST'])
def arm_takeoff():
    print "Got POST request to arm_takeoff_endpoint"
    response_message = uav.arm_and_takeoff(15)
    uav.set_heading(0)

    return Response(response_message,
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

movement_amount = 10 #m

@app.route('/api/move_north', methods=['POST'])
def move_north():
    print "Got POST request to move_north"
    uav.set_heading(0)
    uav.move_relative(dN=movement_amount, dE=0)
    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/move_south', methods=['POST'])
def move_south():
    print "Got POST request to move_south"
    uav.set_heading(0)
    uav.move_relative(dN=-movement_amount, dE=0)
    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/move_east', methods=['POST'])
def move_east():
    print "Got POST request to move_east"
    uav.set_heading(0)
    uav.move_relative(dN=0, dE=movement_amount)
    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/move_west', methods=['POST'])
def move_west():
    print "Got POST request to move_west"
    uav.set_heading(0)
    uav.move_relative(dN=0, dE=-movement_amount)
    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/return_home', methods=['POST'])
def return_home():
    print "Got POST request to return_home"
    response_message = uav.return_home()

    return Response("Return home recieved",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/land', methods=['POST'])
def land():
    print "Got POST request to land"
    response_message = uav.land()

    return Response("Land request recieved",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

#### End Server Code
app.run(host='0.0.0.0', port=5000, debug=False)

#### Video Code
# # To handle debug video stream
# #open HDMI-In as a video capture device
# #BE SURE YOU HAVE RUN `SOLO VIDEO ACQUIRE`
# video_capture = SoloCamera()
#
# def get_frame():
#     # video_capture.clear()
#     ret, frame = video_capture.read()
#     frame = cv2.resize(frame, (frame.shape[1]/4, frame.shape[0]/4))
#     x,y,frame,debug = target_detect.get_target_coords(frame)
#
#     print "Target Found: %s, %s" % (x,y)
#
#     # outimg = cv2.hconcat((frame,inrange))
#     print frame.shape
#     print debug.shape
#
#     ret, framejpeg = cv2.imencode('.jpg', frame)
#     ret, debugjpeg = cv2.imencode('.jpg', debug)
#
#     print framejpeg.shape
#     print debugjpeg.shape
#     return np.concatenate((framejpeg, debugjpeg)).tostring()
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
# def gen():
#     while True:
#         frame = get_frame()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
# @app.route('/video_feed')
# def video_feed():
#     return Response(gen(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')
