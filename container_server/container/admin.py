#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import datetime
import os
import zipfile

from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import redirect
from import_export import resources
from import_export.fields import Field as ExportField

from config.constants import CONTAINER_HEIGHTS_DICT, CONTAINER_LENGTHS_DICT, LOG_INOUT_TYPES_DICT
from config.settings import STATIC_ROOT
from container.models import InOutHistory

admin.site.site_header = 'Terminal Management System'


# <editor-fold desc="Custom export bằng django-import-export">
# noinspection PyMethodMayBeStatic
class InOutHistoryResource(resources.ModelResource):
    class Meta:
        model = InOutHistory
        fields = (
            'history_id',
            'history_datetime',
            'inout',
            'container_code', 'container_length', 'container_height',
            'ocr_camera__camera_id', 'ocr_camera__camera_name',
        )
        export_order = fields

    def dehydrate_history_datetime(self, iohistory):
        return iohistory.history_datetime.strftime("%H:%M:%S %d/%m/%Y")

    def dehydrate_inout(self, iohistory):
        return LOG_INOUT_TYPES_DICT[iohistory.inout]

    def dehydrate_container_length(self, iohistory):
        return CONTAINER_LENGTHS_DICT[iohistory.container_length]

    def dehydrate_container_height(self, iohistory):
        return CONTAINER_HEIGHTS_DICT[iohistory.container_height]


# noinspection PyMethodMayBeStatic
class InOutHistoryResourceWithImage(InOutHistoryResource):
    ocr_image = ExportField()
    left_image = ExportField()
    right_image = ExportField()
    front_image = ExportField()
    back_image = ExportField()

    class Meta:
        model = InOutHistory
        fields = (
            'history_id',
            'history_datetime',
            'inout',
            'container_code', 'container_length', 'container_height',
            'ocr_camera__camera_id', 'ocr_camera__camera_name',
            'ocr_image', 'left_image', 'right_image', 'front_image', 'back_image',
        )
        export_order = fields

    def dehydrate_ocr_image(self, iohistory):
        ocr_image_filename = iohistory.captured_images.get('ocr_image', None)
        return f'=HYPERLINK("captured_images' \
               f'\\{iohistory.history_id}' \
               f'\\{ocr_image_filename}", "view_image")' if ocr_image_filename is not None else ''

    def dehydrate_left_image(self, iohistory):
        left_image_filename = iohistory.captured_images.get('left_image', None)
        return f'=HYPERLINK("captured_images' \
               f'\\{iohistory.history_id}' \
               f'\\{left_image_filename}", "view_image")' if left_image_filename is not None else ''

    def dehydrate_right_image(self, iohistory):
        right_image_filename = iohistory.captured_images.get('right_image', None)
        return f'=HYPERLINK("captured_images' \
               f'\\{iohistory.history_id}' \
               f'\\{right_image_filename}", "view_image")' if right_image_filename is not None else ''

    def dehydrate_front_image(self, iohistory):
        front_image_filename = iohistory.captured_images.get('front_image', None)
        return f'=HYPERLINK("captured_images' \
               f'\\{iohistory.history_id}' \
               f'\\{front_image_filename}", "view_image")' if front_image_filename is not None else ''

    def dehydrate_back_image(self, iohistory):
        back_image_filename = iohistory.captured_images.get('back_image', None)
        return f'=HYPERLINK("captured_images' \
               f'\\{iohistory.history_id}' \
               f'\\{back_image_filename}", "view_image")' if back_image_filename is not None else ''


# </editor-fold>


# <editor-fold desc="Tùy chỉnh hiển thị của các model">


def export_histories_to_csv(model_admin, request, queryset):
    try:
        if not os.path.exists(settings.TEMP_DIR_ROOT):
            os.makedirs(settings.TEMP_DIR_ROOT, exist_ok=True)
        if not os.path.exists(settings.TEMP_EMPTY_DIR):
            os.makedirs(settings.TEMP_EMPTY_DIR, exist_ok=True)
        csv_filename = f'container_histories_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
        csv_filepath = os.path.join(settings.TEMP_DIR_ROOT, f'{csv_filename}')
        with open(csv_filepath, 'wt') as csv_file:
            csv_file.write(
                InOutHistoryResource().export(queryset).export('csv')
            )

        return redirect(
            f'{settings.STATIC_URL}tmp/{csv_filename}'
        )

    except Exception as exc:
        messages.add_message(
            request,
            messages.ERROR,
            f'Export histories failed: {exc}',
        )

    return redirect('./')


def export_histories_to_xlsx(model_admin, request, queryset):
    try:
        if not os.path.exists(settings.TEMP_DIR_ROOT):
            os.makedirs(settings.TEMP_DIR_ROOT, exist_ok=True)
        if not os.path.exists(settings.TEMP_EMPTY_DIR):
            os.makedirs(settings.TEMP_EMPTY_DIR, exist_ok=True)
        xlsx_filename = f'container_histories_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        xlsx_filepath = os.path.join(settings.TEMP_DIR_ROOT, f'{xlsx_filename}')
        with open(xlsx_filepath, 'wb') as excel_file:
            excel_file.write(
                InOutHistoryResource().export(queryset).export('xlsx')
            )

        return redirect(
            f'{settings.STATIC_URL}tmp/{xlsx_filename}'
        )

    except Exception as exc:
        messages.add_message(
            request,
            messages.ERROR,
            f'Export histories failed: {exc}',
        )

    return redirect('./')


def download_as_zip(model_admin, request, queryset):
    try:
        if not os.path.exists(settings.TEMP_DIR_ROOT):
            os.makedirs(settings.TEMP_DIR_ROOT, exist_ok=True)
        if not os.path.exists(settings.TEMP_EMPTY_DIR):
            os.makedirs(settings.TEMP_EMPTY_DIR, exist_ok=True)
        name = f'container_histories_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        zip_filename = f'{name}.zip'
        zip_filepath = os.path.join(settings.TEMP_DIR_ROOT, f'{zip_filename}')

        with zipfile.ZipFile(zip_filepath, mode='w') as zf:
            zf.writestr(
                f'{name}.xlsx',
                InOutHistoryResourceWithImage().export(queryset).export('xlsx')
            )
            zf.write(
                settings.TEMP_EMPTY_DIR,
                arcname='captured_images',
            )
            for history in queryset:
                ocr_image_filename = history.captured_images.get('ocr_image', None)
                left_image_filename = history.captured_images.get('left_image', None)
                right_image_filename = history.captured_images.get('right_image', None)
                front_image_filename = history.captured_images.get('front_image', None)
                back_image_filename = history.captured_images.get('back_image', None)

                ocr_image_filepath = os.path.join(
                    STATIC_ROOT,
                    'captured_images',
                    f'{history.history_id}',
                    f'{ocr_image_filename}',
                )
                left_image_filepath = os.path.join(
                    STATIC_ROOT,
                    'captured_images',
                    f'{history.history_id}',
                    f'{left_image_filename}',
                ) if left_image_filename is not None else None
                right_image_filepath = os.path.join(
                    STATIC_ROOT,
                    'captured_images',
                    f'{history.history_id}',
                    f'{right_image_filename}',
                ) if right_image_filename is not None else None
                front_image_filepath = os.path.join(
                    STATIC_ROOT,
                    'captured_images',
                    f'{history.history_id}',
                    f'{front_image_filename}',
                ) if front_image_filename is not None else None
                back_image_filepath = os.path.join(
                    STATIC_ROOT,
                    'captured_images',
                    f'{history.history_id}',
                    f'{back_image_filename}',
                ) if back_image_filename is not None else None

                try:
                    zf.write(
                        ocr_image_filepath,
                        f'captured_images/{history.history_id}/{ocr_image_filename}'
                    )
                except Exception as exc:
                    print(exc)
                try:
                    zf.write(
                        left_image_filepath,
                        f'captured_images/{history.history_id}/{left_image_filename}'
                    )
                except Exception as exc:
                    print(exc)
                try:
                    zf.write(
                        right_image_filepath,
                        f'captured_images/{history.history_id}/{right_image_filename}'
                    )
                except Exception as exc:
                    print(exc)
                try:
                    zf.write(
                        front_image_filepath,
                        f'captured_images/{history.history_id}/{front_image_filename}'
                    )
                except Exception as exc:
                    print(exc)
                try:
                    zf.write(
                        back_image_filepath,
                        f'captured_images/{history.history_id}/{back_image_filename}'
                    )
                except Exception as exc:
                    print(exc)

        return redirect(
            f'{settings.STATIC_URL}tmp/{zip_filename}'
        )

    except Exception as exc:
        messages.add_message(
            request,
            messages.ERROR,
            f'Export histories failed: {exc}',
        )

    return redirect('./')


def register():
    pass
# </editor-fold>
