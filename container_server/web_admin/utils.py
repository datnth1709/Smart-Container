#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import os

from django.utils.html import format_html

from config.settings import STATIC_ROOT
from utils.static_util import StaticUtil


def get_captured_image_thumbnail(self, obj):
    # noinspection PyBroadException
    try:
        ocr_image_filename = obj.captured_images.get('ocr_image', None)
        left_image_filename = obj.captured_images.get('left_image', None)
        right_image_filename = obj.captured_images.get('right_image', None)
        front_image_filename = obj.captured_images.get('front_image', None)
        back_image_filename = obj.captured_images.get('back_image', None)

        ocr_image_filepath = os.path.join(
            STATIC_ROOT,
            'captured_images',
            f'{obj.history_id}',
            f'{ocr_image_filename}',
        )
        left_image_filepath = os.path.join(
            STATIC_ROOT,
            'captured_images',
            f'{obj.history_id}',
            f'{left_image_filename}',
        ) if left_image_filename is not None else None
        right_image_filepath = os.path.join(
            STATIC_ROOT,
            'captured_images',
            f'{obj.history_id}',
            f'{right_image_filename}',
        ) if right_image_filename is not None else None
        front_image_filepath = os.path.join(
            STATIC_ROOT,
            'captured_images',
            f'{obj.history_id}',
            f'{front_image_filename}',
        ) if front_image_filename is not None else None
        back_image_filepath = os.path.join(
            STATIC_ROOT,
            'captured_images',
            f'{obj.history_id}',
            f'{back_image_filename}',
        ) if back_image_filename is not None else None

        ocr_image_url = StaticUtil.filepath2url(ocr_image_filepath)
        left_image_url = StaticUtil.filepath2url(left_image_filepath) if left_image_filepath is not None else '#'
        right_image_url = StaticUtil.filepath2url(right_image_filepath) if right_image_filepath is not None else '#'
        front_image_url = StaticUtil.filepath2url(front_image_filepath) if front_image_filepath is not None else '#'
        back_image_url = StaticUtil.filepath2url(back_image_filepath) if back_image_filepath is not None else '#'

    except Exception:
        ocr_image_url = '#'
        left_image_url = '#'
        right_image_url = '#'
        front_image_url = '#'
        back_image_url = '#'

    return format_html(
        f'<a href="{ocr_image_url}" target="{"_blank" if ocr_image_url != "#" else ""}">'
        f'<img src="{ocr_image_url}" style="max-width:120px; max-height:120px;">'
        f'</a>'
        f'<a href="{left_image_url}" target="{"_blank" if left_image_url != "#" else ""}">'
        f'<img src="{left_image_url}" style="max-width:120px; max-height:120px;">'
        f'</a>'
        f'<a href="{right_image_url}" target="{"_blank" if right_image_url != "#" else ""}">'
        f'<img src="{right_image_url}" style="max-width:120px; max-height:120px;">'
        f'</a>'
        f'<a href="{front_image_url}" target="{"_blank" if front_image_url != "#" else ""}">'
        f'<img src="{front_image_url}" style="max-width:120px; max-height:120px;">'
        f'</a>'
        f'<a href="{back_image_url}" target="{"_blank" if back_image_url != "#" else ""}">'
        f'<img src="{back_image_url}" style="max-width:120px; max-height:120px;">'
        f'</a>'
    )
