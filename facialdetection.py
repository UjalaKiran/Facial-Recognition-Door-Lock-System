import pandas as pd
import cv2
import urllib.request
import numpy as np
import os
from datetime import datetime
import face_recognition
import requests

# ESP32 URL
esp32_url = "http://192.168.159.177"
path = r'C:\Users\HP\Downloads\pp\image_folder'
url = f"{esp32_url}/cam-hi.jpg"

# Create attendance file if it doesn't exist
attendance_folder = os.path.join(os.getcwd(), 'data')
os.makedirs(attendance_folder, exist_ok=True)

attendance_file = os.path.join(attendance_folder, 'Data.csv')
if os.path.exists(attendance_file):
    print("data file exists. Removing it for a fresh start.")
    os.remove(attendance_file)
else:
    print("data file donot exists.")
    

df = pd.DataFrame()
df.to_csv(attendance_file, index=False)

# Load images and names
images = []
classNames = []
myList = os.listdir(path)
print(f"Found images: {myList}")

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    if curImg is not None:
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])
print(f"Class names: {classNames}")

# Unlock solenoid lock
def unlock_solenoid():
    try:
        response = requests.get(f"{esp32_url}/unlock")
        if response.status_code == 200:
            print("Solenoid lock activated!")
        else:
            print("Failed to activate solenoid lock.")
    except Exception as e:
        print(f"Error unlocking solenoid: {e}")

# Encode images
def findEncodings(images):
    encodeList = []
    for img in images:
        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodes = face_recognition.face_encodings(img)
            if encodes:  # Ensure encodings exist
                encodeList.append(encodes[0])
        except Exception as e:
            print(f"Error encoding image: {e}")
    return encodeList

# Mark attendance
def markAttendance(name):
    with open(attendance_file, 'r+') as f:
        myDataList = f.readlines()
        nameList = [line.split(',')[0] for line in myDataList]
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'{name},{dtString}\n')

encodeListKnown = findEncodings(images)
print('Encoding Complete')

# Start face recognition
while True:
    try:
        img_resp = urllib.request.urlopen(url)
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgnp, -1)

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace, tolerance=0.4)  # Stricter tolerance
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            print(f"Face distances: {faceDis}")  # Debugging distances

            matchIndex = np.argmin(faceDis)
            if matches[matchIndex] and faceDis[matchIndex] < 0.4:  # Additional check on distance
                name = classNames[matchIndex].upper()
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                markAttendance(name)
                unlock_solenoid()
            else:
                print("No accurate match found.")  # Debugging

        cv2.imshow('Webcam', img)
        key = cv2.waitKey(5)
        if key == ord('q'):
            break

    except Exception as e:
        print(f"Error during face recognition: {e}")
        break

cv2.destroyAllWindows()
