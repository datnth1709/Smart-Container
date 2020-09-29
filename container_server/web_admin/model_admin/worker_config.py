#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django.contrib import admin
from django.db.models import BLANK_CHOICE_DASH


class WorkerConfigAdmin(admin.ModelAdmin):
    list_display = (
        'worker_id',
        'ocr_camera', 'front_camera', 'left_camera', 'right_camera',
        'text_area_min_size',
        'status',
    )
    list_display_links = list_display
    readonly_fields = ('ocr_camera', 'status',)

    def get_action_choices(self, request, default_choices=BLANK_CHOICE_DASH):
        choices = super(WorkerConfigAdmin, self).get_action_choices(request)
        choices.pop(0)
        return choices

    def get_model_perms(self, *args, **kwargs):
        perms = admin.ModelAdmin.get_model_perms(self, *args, **kwargs)
        perms['list_hide'] = True
        return perms
