from dronekit import mavutil, connect, VehicleMode, LocationGlobal, LocationGlobalRelative
import time, sys, os
import uavutil

class FireflyUAV:
    def __init__(self, TEST_MODE=True):
        self.vehicle = None
        self.takeoff_location = None
        self.TEST_MODE = TEST_MODE

        # If true, won't actually start motors
        TEST_MODE = True
        print "FireflyUAV Initialized. TEST_MODE=%s" % self.TEST_MODE

    def connect(self):
        print 'Begin Connect'

        try:
            target = sys.argv[1] if len(sys.argv) >= 2 else 'tcp:127.0.0.1:5762'
            print 'Connecting to ' + target + '...'
            self.vehicle = connect(target, wait_ready=True)
        except Exception:
            print 'No simulator present, connecting to drone'
            target = sys.argv[1] if len(sys.argv) >= 2 else 'udpin:0.0.0.0:14550'
            print 'Connecting to ' + target + '...'
            self.vehicle = connect(target, wait_ready=True)

        # Reference for all commands/attributes
        print "Autopilot Firmware version: %s" % self.vehicle.version
        print "Global Location: %s" % self.vehicle.location.global_frame
        print "Global Location (relative altitude): %s" % self.vehicle.location.global_relative_frame
        print "Local Location: %s" % self.vehicle.location.local_frame    #NED
        print "Attitude: %s" % self.vehicle.attitude
        print "Velocity: %s" % self.vehicle.velocity
        print "GPS: %s" % self.vehicle.gps_0
        print "Groundspeed: %s" % self.vehicle.groundspeed
        print "Airspeed: %s" % self.vehicle.airspeed
        print "Gimbal status: %s" % self.vehicle.gimbal
        print "Battery: %s" % self.vehicle.battery
        print "EKF OK?: %s" % self.vehicle.ekf_ok
        print "Last Heartbeat: %s" % self.vehicle.last_heartbeat
        print "Rangefinder: %s" % self.vehicle.rangefinder
        print "Rangefinder distance: %s" % self.vehicle.rangefinder.distance
        print "Rangefinder voltage: %s" % self.vehicle.rangefinder.voltage
        print "Heading: %s" % self.vehicle.heading
        print "Is Armable?: %s" % self.vehicle.is_armable
        print "System status: %s" % self.vehicle.system_status.state
        print "Mode: %s" % self.vehicle.mode.name    # settable
        print "Armed: %s" % self.vehicle.armed    # settable

        self.takeoff_location = self.vehicle.location.global_relative_frame
        print "Takeoff Location: %s" % self.takeoff_location

        # Settings
        print "Set default/target airspeed to 3"
        self.vehicle.airspeed = 3

    def arm_and_takeoff(self, aTargetAltitude):
        """
        Arms vehicle and fly to aTargetAltitude.
        """

        print "Begin arm and takeoff"

        if self.TEST_MODE:
            return "Test Mode"

        self.takeoff_location = self.vehicle.location.global_relative_frame
        print "Takeoff Location: %s" % self.takeoff_location

        if self.takeoff_location is None:
            return "ERROR: takeoff_location was None."

        print "Basic pre-arm checks"
        # Don't try to arm until autopilot is ready
        while not self.vehicle.is_armable:
            print " Waiting for vehicle to initialise..."
            time.sleep(1)

        print "Arming motors"
        # Copter should arm in GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")
        self.vehicle.armed = True

        # Confirm vehicle armed before attempting to take off
        while not self.vehicle.armed:
            print " Waiting for arming..."
            time.sleep(1)

        print "Taking off!"
        self.vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude
        self.wait_for_target_altitude(aTargetAltitude)

    def wait_for_target_altitude(self, aTargetAltitude):
        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        print "Target Altitude: ", aTargetAltitude
        while True:
            print " Altitude: ", self.vehicle.location.global_relative_frame.alt
            #Break and return from function just below target altitude.
            if self.vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
                print "Reached target altitude"
                break
            time.sleep(1)

    def goto_relative_altitude(self, aTargetAltitude):
        targetlocation = self.vehicle.location.global_relative_frame
        targetlocation.alt = aTargetAltitude
        self.goto_blocking(targetlocation)

    def land(self):
        self.vehicle.mode = VehicleMode("RTL")

    def return_home(self):
        # TEST
        return_altitude = 15 # meters
        self.goto_relative_altitude(return_altitude);
        targetlocation = self.takeoff_location;
        targetlocation.alt = return_altitude
        self.goto_blocking(targetlocation)
        self.land()

    def send_ned_velocity(self, velocity_x, velocity_y, velocity_z):
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

    def set_heading(self, heading, relative=False):
        """
        Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).

        This method sets an absolute heading by default, but you can set the `relative` parameter
        to `True` to set yaw relative to the current yaw heading.

        By default the yaw of the vehicle will follow the direction of travel. After setting
        the yaw using this function there is no way to return to the default yaw "follow direction
        of travel" behaviour (https://github.com/diydrones/ardupilot/issues/2427)

        For more information see:
        http://copter.ardupilot.com/wiki/common-mavlink-mission-command-messages-mav_cmd/#mav_cmd_condition_yaw
        """
        if relative:
            is_relative = 1 #yaw relative to direction of travel
        else:
            is_relative = 0 #yaw is an absolute angle
        # create the CONDITION_YAW command using command_long_encode()
        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
            0, #confirmation
            heading,    # param 1, yaw in degrees
            0,          # param 2, yaw speed deg/s
            1,          # param 3, direction -1 ccw, 1 cw
            is_relative, # param 4, relative offset 1, absolute angle 0
            0, 0, 0)    # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(msg)

    # The goto command, non-blocking
    def goto_position_global(self, aLocation):
        """
        Send SET_POSITION_TARGET_GLOBAL_INT command to request the vehicle fly to a specified LocationGlobal.

        For more information see: https://pixhawk.ethz.ch/mavlink/#SET_POSITION_TARGET_GLOBAL_INT

        See the above link for information on the type_mask (0=enable, 1=ignore).
        At time of writing, acceleration and yaw bits are ignored.
        """
        msg = self.vehicle.message_factory.set_position_target_global_int_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT, # frame
            0b0000111111111000, # type_mask (only speeds enabled)
            aLocation.lat*1e7, # lat_int - X Position in WGS84 frame in 1e7 * meters
            aLocation.lon*1e7, # lon_int - Y Position in WGS84 frame in 1e7 * meters
            aLocation.alt, # alt - Altitude in meters in AMSL altitude, not WGS84 if absolute or relative, above terrain if GLOBAL_TERRAIN_ALT_INT
            0, # X velocity in NED frame in m/s
            0, # Y velocity in NED frame in m/s
            0, # Z velocity in NED frame in m/s
            0, 0, 0, # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
            0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
        # send command to vehicle
        self.vehicle.send_mavlink(msg)

    def goto_blocking(self, targetLocation):
        currentLocation = self.vehicle.location.global_frame
        targetDistance = uavutil.get_distance_metres(currentLocation, targetLocation)
        self.goto_position_global(targetLocation)

        while self.vehicle.mode.name=="GUIDED": #Stop action if we are no longer in guided mode.
            remainingDistance = uavutil.get_distance_metres(self.vehicle.location.global_frame, targetLocation)
            print "Distance to target: ", remainingDistance
            if remainingDistance <= .2 : #Just below target, in case of undershoot.
                print "Reached target"
                break;
            time.sleep(2)

        self.wait_for_target_altitude(targetLocation.alt)

    def move_relative(self, dN, dE):
        targetLocation = uavutil.get_location_metres(self.vehicle.location.global_relative_frame,
                                                     dNorth=dN, dEast=dE)
        self.goto_position_global(targetLocation)

    # def land_control_velocity(dN, dE):
    #     global vehicle, homelocation_hacked, homelocation_local_hacked
    #
    #     threshold = .1
    #     v = .1
    #     v_n = 0
    #     v_e = 0
    #
    #     if (dN < -threshold):
    #         v_n = v
    #     if (dN > threshold):
    #         v_n = -v
    #
    #     if (dE < -threshold):
    #         v_e = v
    #     if (dE > threshold):
    #         v_e = -v
    #
    #     v_d = .3
    #     return (v_n, v_e, v_d)

    # # Returns UTM in form (EASTING, NORTHING, ZONE NUMBER, ZONE LETTER)
    # def get_location_utm():
    #     l = vehicle.location.global_frame
    #     return utm.from_latlon(l.lat, l.lon)
    #
    # # Return relative North, East offset of landing zone
    # def acquire_target_NED_location():
    #     global vehicle, homelocation_hacked, homelocation_local_hacked
    #     current_E,current_N,_,_=get_location_utm()
    #
    #     dE = current_E - homelocation_local_hacked[0]
    #     dN = current_N - homelocation_local_hacked[1]
    #     return (dN, dE)
