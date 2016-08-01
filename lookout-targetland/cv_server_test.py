import cv2
import sys
import time
import threading
from SoloCamera import SoloCamera

from flask import Flask, Response, request, render_template

#open HDMI-In as a video capture device
#BE SURE YOU HAVE RUN `SOLO VIDEO ACQUIRE`
video_capture = SoloCamera()
ret, frame = video_capture.read()

#### Start Server Code
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kolibri_secret_key'

def get_frame():
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

#### End Server Code

# Run Script
app.run(host='0.0.0.0', port=5000, debug=False)
