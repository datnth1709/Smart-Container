#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import cv2
import numpy as np
from PIL import ImageDraw, ImageFont

from ocr_worker.utils.yolov3_detector import convert_to_original_size


def process_data_container(filtered_boxes, img, classes, img_size):
    draw = ImageDraw.Draw(img)
    open_cv_image = np.array(img)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    for cls, bboxs in filtered_boxes.items():
        color = tuple(np.random.randint(0, 256, 3))
        for box, score in bboxs:
            box = convert_to_original_size(box, np.array(img_size),
                                           np.array(img.size),
                                           True)

            if score * 100 < 95.:
                continue

            x1, x2, y1, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            image_box = open_cv_image[x2:y2, x1:y1]
            cv2.imwrite('./data/d.png', image_box)
            draw.rectangle(box, outline=color)
            draw.text([x1 - 30, x2 - 20], '{} {:.2f}%'.format(classes[cls], score * 100),
                      fill=color,
                      font=ImageFont.truetype('arial'))
            draw.text([x1 - 30, x2 - 10], '{}'.format('KKKK XXXX UUU III'),
                      fill=color,
                      font=ImageFont.truetype('arial'))
