import numpy as np
import face_recognition as fr
import cv2
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# Retrieve all files from current directory
cwd = os.getcwd()
images = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]

# Store all the images and corresponding names into list
known_face_encondings = []
known_face_names = []
for image in images:
    list = np.array(image.split("/"))
    name = "" + list[list.size - 1]
    if name.__contains__(".jpeg") or name.__contains__(".png"):
        known_face_encondings.append(fr.face_encodings(fr.load_image_file(name))[0])
        name = name.split(".")[0]
        known_face_names.append(name)

# Start the video
video_capture = cv2.VideoCapture(0)
current_name = "Unknown"

# Prepare Server
smtp_server_name = 'smtp.gmail.com'
server = smtplib.SMTP_SSL(smtp_server_name, 465)
server.login("prabjotram@gmail.com", "vwujsypnlvqwovdb")
FROM = 'prabjotram@gmail.com'
TO = "prabjotram@gmail.com"

# Detect the face
while True:
    ret, frame = video_capture.read()

    rgb_frame = frame[:, :, ::-1]

    face_locations = fr.face_locations(rgb_frame)
    face_encodings = fr.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

        matches = fr.compare_faces(known_face_encondings, face_encoding)

        face_distances = fr.face_distance(known_face_encondings, face_encoding)

        best_match_index = np.argmin(face_distances)

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        message = MIMEMultipart()
        message['Subject'] = 'Home Security System'
        message['From'] = FROM
        message['To'] = TO

        # Face detected
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            # Prepare actual message
            message.attach(MIMEText("%s walked in!" % name))
        else:
            # Prepare actual message
            name = "Unknown"
            message.attach(MIMEText("Intruder Alert!"))

        # Send the mail
        print(current_name)
        print(name)
        if current_name != name:
            current_name = name
            server.sendmail(FROM, TO, message.as_string())

    cv2.imshow('Webcam_facerecognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

server.quit()
video_capture.release()
cv2.destroyAllWindows()
