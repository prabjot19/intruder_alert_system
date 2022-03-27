import numpy as np
import face_recognition as fr
import cv2
import smtplib

video_capture = cv2.VideoCapture(0)

paolo_image = fr.load_image_file("paolo.jpeg")
paula_image = fr.load_image_file("paula.png")
ishmail_image = fr.load_image_file("ishmail.jpeg")
paolo_face_encoding = fr.face_encodings(paolo_image)[0]
paula_face_encoding = fr.face_encodings(paula_image)[0]
ishmail_face_encoding = fr.face_encodings(ishmail_image)[0]

known_face_encondings = [paolo_face_encoding,ishmail_face_encoding,paula_face_encoding]
known_face_names = ["Paolo","Ishmail","Paula"]

current_name = "Unknown"

while True:
    ret, frame = video_capture.read()

    rgb_frame = frame[:, :, ::-1]

    face_locations = fr.face_locations(rgb_frame)
    face_encodings = fr.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

        matches = fr.compare_faces(known_face_encondings, face_encoding)

        face_distances = fr.face_distance(known_face_encondings, face_encoding)

        best_match_index = np.argmin(face_distances)


        # SERVER = "Preparation"
        FROM = 'prabjotram@gmail.com'
        TO = "prabjotram@gmail.com"

        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            print(name)

            # Prepare actual message
            message = "Subject: Home Security System\n\n %s walked in!" % name

        else:
            # Prepare actual message
            message = "Subject: Home Security System\n\nIntruder Alert!"
            name = "Unknown"

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Send the mail
        smtp_server_name = 'smtp.gmail.com'
        server = smtplib.SMTP_SSL(smtp_server_name, 465)
        server.login("prabjotram@gmail.com","vwujsypnlvqwovdb")
        if current_name != name:
            current_name = name
            server.sendmail(FROM, TO, message)

    cv2.imshow('Webcam_facerecognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

server.quit()
video_capture.release()
cv2.destroyAllWindows()
