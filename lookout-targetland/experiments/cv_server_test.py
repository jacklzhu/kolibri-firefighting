import cv2
import sys
import time
import threading
import signal
from SoloCamera import SoloCamera
import target_detect
import numpy as np
from flask import Flask, Response, request, render_template

#### Start Server Code
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kolibri_secret_key'

#open HDMI-In as a video capture device
#BE SURE YOU HAVE RUN `SOLO VIDEO ACQUIRE`
video_capture = SoloCamera()

latest_frame = None;

def process_frame(frame):
    # video_capture.clear()
    frame = cv2.resize(frame, (frame.shape[1]/4, frame.shape[0]/4))
    x,y,frame,debug = target_detect.get_target_coords(frame)

    print "Target Found: %s, %s" % (x,y)

    frame = np.concatenate((frame, cv2.cvtColor(debug,cv2.COLOR_GRAY2RGB)), axis=1)
    ret, framejpeg = cv2.imencode('.jpg', frame)

    print framejpeg.shape
    return framejpeg.tostring()

def get_latest_frame():
    return latest_frame.copy()

def update_frame():
    global latest_frame
    start = time.time()
    ret, latest_frame = video_capture.read()
    fps = round(1/(time.time()-start),2)
    return fps

@app.route('/')
def index():
    return render_template('index.html')

def gen():
    while True:
        frame = process_frame(get_latest_frame())
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(.5)

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


#### End Server Code
# Don't freak out on signals
run_update_thread = True
def sigint_handler(signum, frame):
    run_update_thread = False

signal.signal(signal.SIGINT, sigint_handler)

# Run a thread to update the current frame

def update_frame_loop():
    while run_update_thread:
        fps = update_frame()
        print "Frame Update: %s fps" % fps
    print "Child exit"

thr = threading.Thread(target=update_frame_loop)
thr.start()

# Run Script
app.run(host='0.0.0.0', port=5000, debug=False)
