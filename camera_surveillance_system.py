# Web streaming example
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming

import io
import picamera
import logging
import socketserver
import numpy as np
import face_recognition as fr
import cv2
import smtplib
import os
from picamera.array import PiRGBArray
from threading import Condition
from http import server
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

PAGE="""\
<html>
<head>
<title>Raspberry Pi - Surveillance Camera</title>
</head>
<body>
<center><h1>Raspberry Pi - Surveillance Camera</h1></center>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.condition = Condition()
        self.buffer = io.BytesIO()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class FacialRecognition(object):
    def __init__(self):
        
        # Retrieve all files from current directory
        cwd = os.getcwd()
        images = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]

        # Store all the images and corresponding names into list
        self.known_face_encondings = []
        self.known_face_names = []
        for image in images:
            list = np.array(image.split("/"))
            name = "" + list[list.size - 1]
            if name.__contains__(".jpeg") or name.__contains__(".png"):
                self.known_face_encondings.append(fr.face_encodings(fr.load_image_file(name))[0])
                name = name.split(".")[0]
                self.known_face_names.append(name)

        self.current_name = "Unknown"
        
        # Prepare Server
        smtp_server_name = 'smtp.gmail.com'
        self.server = smtplib.SMTP_SSL(smtp_server_name, 465)
        server.login("prabjotram@gmail.com", "vwujsypnlvqwovdb")
        self.FROM = 'prabjotram@gmail.com'
        self.TO = "prabjotram@gmail.com"

        # Counter for people detected
        count = 0;
        
    def detect_face(self,frame):
    
        rgb_frame = frame[:, :, ::-1]
        face_locations = fr.face_locations(rgb_frame)
        face_encodings = fr.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            matches = fr.compare_faces(self.known_face_encondings, face_encoding)
            face_distances = fr.face_distance(self.known_face_encondings, face_encoding)
            best_match_index = np.argmin(face_distances)
        
            # Prepare email
            message = MIMEMultipart()
            message['Subject'] = 'Home Security System'
            message['From'] = self.FROM
            message['To'] = self.TO
            
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                print(name)
                
                # Prepare actual message
                path = os.path.join(cwd + "/known_people", '%d.png') % count
                cv2.imwrite(path, frame)
                count += 1
                message.attach(MIMEText("%s walked in!" % name))
                message.attach(MIMEImage(open(path, 'rb').read(), name=os.path.basename(path)))
            else:
                name = "Unknown"
                
                # Prepare actual message
                path = os.path.join(cwd + "/intruders", '%d.png') % count
                cv2.imwrite(path, frame)
                count += 1
                message.attach(MIMEText("Intruder Alert!"))
                message.attach(MIMEImage(open(path, 'rb').read(), name=os.path.basename(path)))
                
            # Send the mail
            if current_name != name:
                current_name = name
                self.server.sendmail(FROM, TO, message.as_string())
                
    def stop_detecting(self):
        server.quit()
        cv2.destroyAllWindows()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=28) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    
    detectFace = FacialRecognition()
    rawCapture= PiRGBArray(camera, size=(640,480))
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image =np.array(frame.array)
        
        detectFace.detect_face(image)
        
        rawCapture.truncate(0)
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
        detectFace