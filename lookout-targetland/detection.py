import serial
import signal
import sys
import time
import threading

class Detector:
    def __init__(self, detection_callback, threshold_cm=100, numsensors=3):
        self.numsensors = numsensors
        self.filters = [0] * self.numsensors
        self.detection_callback = detection_callback
        self.threshold_cm = threshold_cm

    def check_detection(self):
        for f in self.filters:
            if 0 < f < self.threshold_cm:
                self.detection_callback(self.filters)
                return

    def register_measurement(self, measurements_cm):
        if len(measurements_cm) != self.numsensors:
            print "ERROR: Not enough measurements"
            return

        # Todo some filtering scheme
        for i,measure in enumerate(measurements_cm):
            self.filters[i] = measure

        # print measurements_cm
        self.check_detection()

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

    def start_thread(self):
        print "STARTING"
        self.detector_running = True
        self.process_thread.start()

    def stop_thread(self):
        print "STOPPING"
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

if __name__ == "__main__":
    def OhNo(measurements):
        print "Oh No!: ", measurements

    detector = Detector(numsensors=3, detection_callback=OhNo)
    detectorserial = DetectorSerial(detector=detector)

    def signal_handler(signal, frame):
        print('Got SIGINT. Stopping Thread.')
        detectorserial.stop_thread()
    signal.signal(signal.SIGINT, signal_handler)

    detectorserial.start_thread()

    time.sleep(100000)
    detectorserial.stop_thread()
