#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code
import json

# server
from flask import Flask, Response, request, render_template, jsonify

# drone control
import FireflyUAV
import uavutil

#### Start Server Code
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kolibri_secret_key'

# Make False if there isn't a drone or a simulator
USE_DRONE = False;

if USE_DRONE:
    uav = FireflyUAV.FireflyUAV(TEST_MODE=False)
    uav.connect()

movement_amount = 10 #m
altitude = 20 #m

# Actual takeoff/land endpoints
@app.route('/api/arm_takeoff', methods=['POST'])
def arm_takeoff():
    print "Got POST request to arm_takeoff_endpoint"

    if USE_DRONE:
        response_message = uav.arm_and_takeoff(altitude)
        uav.set_heading(0)
    else:
        response_message = "Got takeoff message [test mode]"

    return Response(response_message,
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})


@app.route('/api/move_north', methods=['POST'])
def move_north():
    print "Got POST request to move_north"

    if USE_DRONE:
        uav.set_heading(0)
        uav.move_relative(dN=movement_amount, dE=0)

    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/move_south', methods=['POST'])
def move_south():
    print "Got POST request to move_south"

    if USE_DRONE:
        uav.set_heading(0)
        uav.move_relative(dN=-movement_amount, dE=0)

    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/move_east', methods=['POST'])
def move_east():
    print "Got POST request to move_east"

    if USE_DRONE:
        uav.set_heading(0)
        uav.move_relative(dN=0, dE=movement_amount)

    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/move_west', methods=['POST'])
def move_west():
    print "Got POST request to move_west"

    if USE_DRONE:
        uav.set_heading(0)
        uav.move_relative(dN=0, dE=-movement_amount)

    return Response("",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/return_home', methods=['POST'])
def return_home():
    print "Got POST request to return_home"

    if USE_DRONE:
        response_message = uav.return_home()

    return Response("Return home recieved",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/move_latlong', methods=['POST'])
def goto_latlong():
    print "Got POST request to goto_latlong"

    lat = float(request.args.get("lat"))
    lng = float(request.args.get("long"))

    print lat, lng

    if USE_DRONE:
        uav.set_heading(0)
        response_message = uav.move_latlong(lat,lng)

    return Response("goto Latlong Recieved",
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

@app.route('/api/get_latlong', methods=['GET'])
def get_latlong():
    print "GET request to get_latlong"
    if USE_DRONE:
        response_message = json.dumps(uav.get_latlong())
    else:
        # Response for testing
        response_message = json.dumps({"lat":37.422911, "long":-122.199350})

    return Response(response_message,
            mimetype='application/text',
            headers={'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'})

# @app.route('/api/land', methods=['POST'])
# def land():
#     print "Got POST request to land"
#     response_message = uav.land()
#
#     return Response("Land request recieved",
#             mimetype='application/text',
#             headers={'Cache-Control': 'no-cache',
#             'Access-Control-Allow-Origin': '*'})

#### End Server Code
app.run(host='0.0.0.0', port=5000, debug=False)
