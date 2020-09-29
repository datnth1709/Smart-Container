#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import datetime

from django.contrib import admin
from django.db.models import BLANK_CHOICE_DASH

from config.settings import log
from container.admin import download_as_zip, export_histories_to_csv, export_histories_to_xlsx


class InOutHistoryAdmin(admin.ModelAdmin):
    from web_admin.utils import get_captured_image_thumbnail
    list_display = (
        'history_id',
        'history_datetime', 'ocr_camera', 'inout',
        'container_code', 'container_length', 'container_height',
        'get_captured_image_thumbnail',
    )
    list_display_links = (
        'history_id',
        'history_datetime', 'ocr_camera', 'inout',
        'container_code', 'container_length', 'container_height',
    )
    list_filter = ('inout', 'history_datetime')
    search_fields = ('container_code',)
    actions = [export_histories_to_csv, export_histories_to_xlsx, download_as_zip]
    readonly_fields = ('captured_images', 'ocr_camera', 'left_camera', 'front_camera', 'right_camera',)
    change_list_template = 'web_admin/io_history/change_list.html'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        try:
            request.GET = request.GET.copy()

            container_code = request.GET.pop('container_code', None)
            inout = request.GET.pop('inout', None)
            start_date = request.GET.pop('start_date', None)
            end_date = request.GET.pop('end_date', None)

            if container_code is not None and container_code[0] != '*':
                if container_code[0] != '-1':
                    queryset = queryset.filter(container_code=container_code[0])
                else:
                    queryset = queryset.filter(container_code=None)

            if inout is not None and inout[0] != '*':
                queryset = queryset.filter(inout=inout[0])

            if start_date is not None and start_date[0] != '':
                try:
                    start_date_dt = datetime.datetime.strptime(start_date[0], '%d/%m/%Y, %H:%M')
                    queryset = queryset.filter(
                        history_datetime__gte=start_date_dt
                    )
                except Exception as error:
                    print('query date fail', error)
                    pass
            if end_date is not None and end_date[0] != '':
                try:
                    end_date_dt = datetime.datetime.strptime(end_date[0], '%d/%m/%Y, %H:%M')
                    queryset = queryset.filter(
                        history_datetime__lte=end_date_dt
                    )
                except Exception as error:
                    print('query date fail', error)
                    pass
        except Exception as exc:
            log.error(f'Query histories failed: {exc}')

        return queryset

    get_captured_image_thumbnail.short_description = 'captured image'

    def get_action_choices(self, request, default_choices=BLANK_CHOICE_DASH):
        choices = super(InOutHistoryAdmin, self).get_action_choices(request)
        choices.pop(0)
        return choices
