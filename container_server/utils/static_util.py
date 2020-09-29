#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import os
import shutil
import time

import cv2

from config.settings import STATIC_ROOT, STATIC_URL


class StaticUtil:
    @classmethod
    def filepath2url(cls, filepath):
        if filepath is None:
            return None
        relpath = os.path.relpath(filepath, STATIC_ROOT).replace('\\', '/').replace('./', '')
        return f'{STATIC_URL}{relpath}'

    @classmethod
    def save_image(cls, image, history_id, name_prefix=''):
        filepath = os.path.join(STATIC_ROOT, 'captured_images', str(history_id))
        os.makedirs(filepath, exist_ok=True)
        image_name = f'{name_prefix}{int(round(time.time() * 1000))}.jpg'
        image_path = os.path.join(filepath, image_name)
        cv2.imwrite(image_path, image)
        return image_path, image_name

    @classmethod
    def delete(cls, history_id):
        filepath = os.path.join(STATIC_ROOT, 'captured_images', str(history_id))
        if os.path.exists(filepath):
            shutil.rmtree(filepath)
