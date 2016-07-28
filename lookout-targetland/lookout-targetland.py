#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code

from pymavlink import mavutil # Needed for command message definitions
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time, sys

try:
    target = sys.argv[1] if len(sys.argv) >= 2 else 'tcp:127.0.0.1:5762'  #'udpin:0.0.0.0:14550'
    print 'Connecting to ' + target + '...'
    vehicle = connect(target, wait_ready=True)
except Exception:
    target = sys.argv[1] if len(sys.argv) >= 2 else 'udpin:0.0.0.0:14550'  #'udpin:0.0.0.0:14550'
    print 'Connecting to ' + target + '...'
    vehicle = connect(target, wait_ready=True)

# Reference for all
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

# FIX THE ACTUAL HOME LOCATION
homelocation_hacked = vehicle.location.global_frame
homelocation_local_hacked = vehicle.location.local_frame
print " Home Location: %s" % homelocation_hacked
print " Home Location Local: %s" % homelocation_local_hacked

# code.interact(local=locals())

def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

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

# Return relative North, East offset of landing zone
def acquire_target_NED_location():
    dN = vehicle.location.local_frame.north - homelocation_local_hacked.north
    dE = vehicle.location.local_frame.east - homelocation_local_hacked.east
    return (dN + 1, dE + 1)

def land_control_velocity(dN, dE):
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

    v_d = .1
    return (v_n, v_e, v_d)

def precision_land():
    print "Going home to Home Location: %s" % homelocation_hacked
    vehicle.gimbal.rotate(-90,0,0)
    above_home_loc = LocationGlobalRelative(homelocation_hacked.lat, \
                                            homelocation_hacked.lon, \
                                            10)
    vehicle.simple_goto(above_home_loc)

    # Put loop here
    time.sleep(10)

    print "Lowering to 5 m"
    above_home_loc = LocationGlobalRelative(homelocation_hacked.lat, \
                                            homelocation_hacked.lon, \
                                            5)

    vehicle.simple_goto(above_home_loc, groundspeed=.3)

    # Loop here
    time.sleep(10)


    send_ned_velocity(0, 0, .1)

    while(True):
        (dN, dE) = acquire_target_NED_location()
        (v_n, v_e, v_d) = land_control_velocity(dN, dE)

        print "dN: %s, dE: %s, v_n: %s, v_e: %s, v_d: %s" % (dN, dE, v_n, v_e, v_d)
        send_ned_velocity(v_n, v_e, v_d)
        time.sleep(.1)
    # time.sleep(10)
    #
    # while(True):
    #     send_land_message(0,0)
    #     time.sleep(1)
    #vehicle.mode = VehicleMode("LAND")
    pass

# def send_land_message(x, y):
#     msg = vehicle.message_factory.landing_target_encode(
#         0,       # time_boot_ms (not used)
#         0,       # target num
#         0,       # frame
#         x,       #x
#         y,       #y
#         0,       # altitude.  Not supported.
#         0,0)     # size of target in radians
#     vehicle.send_mavlink(msg)
#     vehicle.flush()

def send_ned_velocity(velocity_x, velocity_y, velocity_z):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000111, # type_mask (only speeds enabled)
        0, 0, 0, # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    vehicle.send_mavlink(msg)

arm_and_takeoff(5)
time.sleep(10)
precision_land()

print "Close vehicle object"
vehicle.close()
