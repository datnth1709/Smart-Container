#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import cv2

video = cv2.VideoCapture('rtsp://admin:love2love@192.168.101.50:9001')

while 1:
    grabbed, frame = video.read()
    if not grabbed:
        continue

    frame = cv2.resize(frame, (640, 360))
    cv2.imshow('Camera', frame)
    cv2.waitKey(1)
