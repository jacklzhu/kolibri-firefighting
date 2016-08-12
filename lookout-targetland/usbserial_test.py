import serial
import signal
import sys
import time
import threading

class Detector:
    def __init__(self, detection_callback, numsensors=3):
        self.numsensors = numsensors
        self.filters = [0] * self.numsensors

    def register_measurement(self, measurements_cm):
        if len(measurements_cm) != self.numsensors:
            print "ERROR: Not enough measurements"
            return

        # Todo some filtering scheme
        for i,measure in enumerate(measurements_cm):
            self.filters[i] = measure

        print measurements_cm

    def get_measurements(self):
        return self.filters

class DetectorSerial:
    def __init__(self, detector):
        self.detector = detector

        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0)
        except serial.serialutil.SerialException:
            self.ser = serial.Serial('/dev/cu.usbserial-A702PYR6', 115200, timeout=0)

        self.kStartChar = 'S'
        self.kDelimiter = ' '
        self.kNumSensors = 3
        self.kPacketLength = 1 + (1 + 3)*self.kNumSensors + 1

        self.process_thread = threading.Thread(target=self.process_thread_func)

        def signal_handler(signal, frame):
            print('Got SIGINT. Stopping Thread.')
            self.stop_thread()

        signal.signal(signal.SIGINT, signal_handler)

    def __del__(self):
        print "Deleting"

    def start_thread(self):
        self.detector_running = True
        self.process_thread.start()

    def stop_thread(self):
        self.detector_running = False
        self.process_thread.join()

    def process_thread_func(self):
        while (self.detector_running):
            s = self.ser.readline()
            if len(s) == self.kPacketLength:
                s = s[2:-1]
                s_int = [int(x) for x in s.split(self.kDelimiter)]
                self.detector.register_measurement(s_int)

        print('Exiting');
        self.ser.close()

def OhNo(measurements):
    print "Oh No!: ", measurements

detector = Detector(numsensors=3, detection_callback=OhNo)
detectorserial = DetectorSerial(detector=detector)
detectorserial.start_thread()
