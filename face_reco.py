import face_recognition as fr
import cv2
import numpy as np
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

class FacialRecognition(object):
    def __init__(self):
        
        # Retrieve all files from current directory
        self.cwd = os.getcwd()
        images = [os.path.join(self.cwd, f) for f in os.listdir(self.cwd) if os.path.isfile(os.path.join(self.cwd, f))]

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
        self.server.login("prabjotram@gmail.com", "udhcvsjhxijfdwbd")
        self.FROM = 'prabjotram@gmail.com'
        self.TO = "prabjotram@gmail.com"

        # Counter for people detected
        self.count = 0;
        
    def detect_face(self,frame):
        
        rgb_frame = frame[:, :, ::-1]
        face_locations = fr.face_locations(rgb_frame,model="cnn")
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
                name = self.known_face_names[best_match_index]
                
                # Prepare actual message
                path = os.path.join(self.cwd+"/household/", '%d.png') % self.count
                if cv2.imwrite(path, frame):
                    self.count += 1
                    message.attach(MIMEText("%s walked in!" % name))
                    message.attach(MIMEImage(open(path, 'rb').read(), name=os.path.basename(path)))
            else:
                name = "Unknown"
                
                # Prepare actual message
                path = os.path.join(self.cwd+"/intruder/", '%d.png') % self.count
                print(path)
                if cv2.imwrite(path, frame):
                    self.count += 1
                    message.attach(MIMEText("Intruder Alert!"))
                    message.attach(MIMEImage(open(path, 'rb').read(), name=os.path.basename(path)))
                
            print(name)
            # Send the mail
            if self.current_name != name:
                self.current_name = name
                self.server.sendmail(self.FROM, self.TO, message.as_string())
                