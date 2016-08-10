from dronekit import mavutil, connect, VehicleMode, LocationGlobal, LocationGlobalRelative
import time, sys, os
import uavutil

class FireflyUAV:
    def __init__(self, altitude=40, TEST_MODE=True):
        self.vehicle = None
        self.takeoff_location = None
        self.TEST_MODE = TEST_MODE
        self.altitude = altitude

        # If true, won't actually start motors
        print "FireflyUAV Initialized. Altitude=%s, TEST_MODE=%s" % (self.altitude, self.TEST_MODE)

    def connect(self):
        print 'Begin Connect'

        try:
            # Try to connect to simulator. This will fail if there isn't a simulator present
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

        print "Set Altitude is: ", self.altitude

        return (True, "")

    def is_armable(self):
        return self.vehicle.is_armable

    def is_active(self):
        # TODO: Make this check more robust
        # Should return true if the robot is able to take movement commands.
        return self.vehicle.armed

    def arm_and_takeoff(self):
        """
        Arms vehicle and fly to self.altitude.

        Note: This is now Non-blocking.
        """

        print "Begin arm and takeoff"

        if self.TEST_MODE:
            return (True, "Test Mode")

        self.takeoff_location = self.vehicle.location.global_relative_frame
        print "Takeoff Location: %s" % self.takeoff_location

        # TODO: Coalesce takeoff_location and home_location
        if self.takeoff_location is None:
            return (False, "ERROR: takeoff_location was None.")

        print "Basic pre-arm checks"
        # Don't try to arm until autopilot is ready
        if not self.is_armable():
            return (False, "Vehicle is not armable yet.")

        print "Arming motors"
        # Copter should arm in GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")
        self.vehicle.armed = True

        # Confirm vehicle armed before attempting to take off
        while not self.vehicle.armed:
            print " Waiting for arming..."
            time.sleep(1)

        print "Taking off!"
        self.vehicle.simple_takeoff(self.altitude) # Take off to target altitude
        return (True, "")

    def is_at_altitude(self):
        '''
        Returns True if the vehicle is close to its intended altitude
        '''
        return self.vehicle.location.global_relative_frame.alt >= self.altitude*0.95;

    def goto_correct_altitude(self):
        '''
        Send command to rise to self.altitude
        '''
        targetlocation = self.vehicle.location.global_relative_frame
        targetlocation.alt = self.altitude
        self.goto_position_global(targetlocation)

    def goto_correct_altitude_blocking(self):
        '''
        Block until we reach self.altitude
        '''
        if self.is_at_altitude():
            return (True, "Already at altitude")
        else:
            self.goto_correct_altitude()

        print "Target Altitude: ", self.altitude
        while not self.is_at_altitude():
            print " Altitude: ", self.vehicle.location.global_relative_frame.alt
            time.sleep(1)

        print "Reached Target Altitude"
        return (True, "Reached target altitude")

    def set_altitude(self, newAltitude):
        if newAltitude < 5:
            emsg = "Error: Altitude is too low (<5 m)"
            return (False, emsg)
        if newAltitude > 100:
            emsg = "Error: Altitude is too high (>100 m)"
            return (False, emsg)

        self.altitude = newAltitude
        self.goto_correct_altitude()
        return (True, "")

    def return_home(self):
        # Just use RTL for now, we'll figure something else later
        while (self.vehicle.mode != VehicleMode("RTL")):
            self.vehicle.mode = VehicleMode("RTL")
            time.sleep(.1)

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

        DO NOT RUN DIRECTLY FROM SERVER!!!! There is no bound checking here.
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

    def move_relative(self, dN, dE):
        '''
        Moves dN in the North direction and dE in the East direction
        '''
        if not self.is_active():
            return (False,"Error: Not Flying")

        self.goto_correct_altitude_blocking()

        targetLocation = uavutil.get_location_metres(self.vehicle.location.global_relative_frame,
                                                     dNorth=dN, dEast=dE)
        self.goto_position_global(targetLocation)

        return (True,"")

    def move_latlong(self, lat, lng):
        '''
        Moves to latlong, with a 100m maximum distance. Maintains the current altitude.
        '''
        if not self.is_active():
            return (False,"Error: Not Flying")

        self.goto_correct_altitude_blocking()

        targetLocation = LocationGlobal(lat, lng, self.altitude)

        if uavutil.get_distance_metres(self.vehicle.location.global_frame, targetLocation) > 100:
            emsg="ERROR: Too far (>100m)"
            print emsg
            return (False, emsg)

        self.goto_position_global(targetLocation)
        return (True, "")

    def get_latlong(self):
        return {"lat":self.vehicle.location.global_frame.lat,
                "long":self.vehicle.location.global_frame.lon,
                "alt":self.vehicle.location.global_relative_frame.alt}

    # def goto_blocking(self, targetLocation):
    #     currentLocation = self.vehicle.location.global_frame
    #     targetDistance = uavutil.get_distance_metres(currentLocation, targetLocation)
    #     self.goto_position_global(targetLocation)
    #
    #     while self.vehicle.mode.name=="GUIDED": #Stop action if we are no longer in guided mode.
    #         remainingDistance = uavutil.get_distance_metres(self.vehicle.location.global_frame, targetLocation)
    #         print "Distance to target: ", remainingDistance
    #         if remainingDistance <= .3 : #Just below target, in case of undershoot.
    #             print "Reached target"
    #             break;
    #         time.sleep(2)
