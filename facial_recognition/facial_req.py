#!/usr/bin/env python3

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import urllib.request
import numpy
import face_recognition
import imutils
import pickle
import time
import datetime

def timestamp():
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def logMsg(msg):
    logFile = open("./log/Fermax.log", "a")
    logFile.write(f"{msg}\n")
    logFile.close()

logMsg(f"{timestamp()} [INFO] Starting...")

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "Unknown"

#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
logMsg(f"{timestamp()} [INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())

# initialize the video stream and allow the camera sensor to warm up
# Set the ser to the followng
# src = 0 : for the build in single web cam, could be your laptop webcam
# src = 2 : I had to set it to 2 inorder to use the USB webcam attached to my laptop
vs = VideoStream(11, framerate=10).start()   # /dev/video11
#vs = VideoStream(usePiCamera=True).start()  # PiCamera
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

logMsg(f"{timestamp()} [INFO] Starting loop...")

# loop over frames from the video file stream
while True:
        # grab the frame from the threaded video stream
        frame = vs.read()

        # If no video detected, sleep 1 sec to lower CPU utilization
        if numpy.average(frame) == 0:
            time.sleep(1)
            continue

        # Detect the fce boxes
        boxes = face_recognition.face_locations(frame)

        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(frame, boxes)

        # loop over the facial embeddings
        for encoding in encodings:
                # attempt to match each face in the input image to our known
                # encodings
                matches = face_recognition.compare_faces(data["encodings"],
                        encoding, tolerance=0.5)
                name = "Unknown" #if face is not recognized, then print Unknown

                # check to see if we have found a match
                if True in matches:
                        # find the indexes of all matched faces then initialize a
                        # dictionary to count the total number of times each face
                        # was matched
                        matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                        counts = {}

                        # loop over the matched indexes and maintain a count for
                        # each recognized face face
                        for i in matchedIdxs:
                                name = data["names"][i]
                                counts[name] = counts.get(name, 0) + 1

                        # determine the recognized face with the largest number
                        # of votes (note: in the event of an unlikely tie Python
                        # will select first entry in the dictionary)
                        name = max(counts, key=counts.get)

                        #If someone in your dataset is identified, Open the door
                        if currentname != name:
                                currentname = name
                                logMsg(f"{timestamp()} Detected face: {currentname}")
                                if currentname != "Unknown":
                                    logMsg(f"{timestamp()} Opening door")
                                    html = urllib.request.urlopen("http://192.168.1.x:81/cgi-bin/sesam.cgi").read()
                                    currentname = "Unknown"

        # update the FPS counter
        fps.update()

# stop the timer and display FPS information
fps.stop()

# do a bit of cleanup
vs.stop()
