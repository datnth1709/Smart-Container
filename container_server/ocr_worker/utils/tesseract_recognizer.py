#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Edward J. C. Ashenbert - Miyuki Nogizaka - Nguyen Quang Binh, May 2020
import pytesseract
import cv2
import os
import numpy as np
class tesseract_text_recognize():
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.config = ("-l eng --oem 3 --psm 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
        self.all_text_images = []

    def sort_contours(self, cnts, method="left-to-right"):
        reverse = False
        i = 0
        if method == "right-to-left" or method == "bottom-to-top":
            reverse = True
        if method == "top-to-bottom" or method == "bottom-to-top":
            i = 1
        boundingBoxes = [cv2.boundingRect(c) for c in cnts]
        (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
                                            key=lambda b: b[1][i], reverse=reverse))
        return (cnts, boundingBoxes)

    def preprocess_image(self, frame):
        height, width, _ = frame.shape
        frame = cv2.resize(frame, (width * 3, height * 3))
        height, width, _ = frame.shape
        image = np.zeros((height, width, 3), np.uint8)
        image[:] = (255, 255, 255)
        img = frame.copy()
        res_img = image - img
        thresh1 = 0
        thresh2 = 170
        thresh3 = 0
        indices = res_img[:, :] > (thresh1, thresh2, thresh3)
        res_img[indices] = 255
        res_img[indices == False] = 0
        indices = res_img[:, :] == 255
        res_img[indices] = 0
        res_img[indices == False] = 255
        res = cv2.cvtColor(res_img, cv2.COLOR_BGR2GRAY)
        res = cv2.threshold(res, 0, 255, cv2.THRESH_BINARY)[1]
        res = cv2.medianBlur(res, 5)
        cnts = cv2.findContours(res, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        mask = np.zeros((height, width), np.uint8)

        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            if x == 0 or x + w >= width or y == 0 or y + h >= height - 10 or w * h < 100:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)  # cv2.boxPoints(rect) for OpenCV 3.x
                # print(box[0][1])
                box = np.int0(box)
                cv2.drawContours(res, [box], 0, 0, -1)
            elif w * h > 100 and w * h < 8000 and h < 200:
                # cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 1)
                roi = res[y:y + h, x:x + w]
                mask[y:y + h, x:x + w] = roi

        sqKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
        res = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, sqKernel)
        # cv2.imwrite('mophology/' + filename, res)
        cnts = cv2.findContours(res, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 3000:
                group_of_text_image = np.zeros((height, width), np.uint8)
                offset = 0
                group_of_text_image[y - offset:y + h + offset, x - offset:x + offset + w] = mask[
                                                                                            y - offset:y + h + offset,
                                                                                            x - offset:x + offset + w]
                group_of_text_image = cv2.threshold(group_of_text_image, 0, 255, cv2.THRESH_BINARY_INV)[1]
                self.all_text_images.append(group_of_text_image)
        return self.all_text_images

    def recognize_image(self, images):
        global real_results
        if len(images) > 2:
            results = []
            for img in images:
                text = pytesseract.image_to_string(img, config=self.config)

                if len(text) >= 3:
                    results.append(text)

            if results != None:
                real_results = [None] * len(results)
                for res in results:

                    if not res.isdecimal() and not res.isalpha() and len(results) >= 3:
                        real_results[2] = res
                    elif res.isdecimal() and not res.isalpha() and len(results) >= 2:
                        if len(res) > 6:
                            res = res[:6]
                        real_results[1] = res
                    elif not res.isdecimal() and res.isalpha()  and len(results) >= 1:
                        real_results[0] = res
                if len(real_results) >= 2:
                    return_text = str(real_results[0]) + str(real_results[1])
                    return return_text
                else:
                    return 'Cannot recognize due to something I dont know'


