#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import jsonfield
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from config.constants import CAMERA_STATUSES, CONTAINER_HEIGHTS, CONTAINER_LENGTHS, LOG_INOUT_TYPES, WORKER_STATUSES


class Camera(models.Model):
    camera_id = models.AutoField(primary_key=True)
    camera_name = models.CharField(
        max_length=45,
        default='Camera',
    )
    stream_url = models.CharField(
        max_length=2083,
        default='rtsp://custom_admin:Abc12345@192.168.1.100:554',
        unique=True,
    )
    use_for_ocr = models.BooleanField(
        default=True,
    )
    offline_video = models.BooleanField(
        default=False,
    )
    status = models.IntegerField(
        choices=CAMERA_STATUSES,
        default=-1,
    )

    def __str__(self):
        return f'{self.camera_id}. {self.camera_name}'


class InOutHistory(models.Model):
    history_id = models.AutoField(primary_key=True)
    history_datetime = models.DateTimeField(auto_now=True)
    inout = models.IntegerField(choices=LOG_INOUT_TYPES, default=0)
    container_code = models.CharField(max_length=18, null=False, blank=True)
    container_str = models.CharField(max_length=18, null=False, blank=True)
    container_length = models.CharField(choices=CONTAINER_LENGTHS, default='-', max_length=18, )
    container_height = models.CharField(choices=CONTAINER_HEIGHTS, default='-', max_length=18,)
    captured_images = jsonfield.JSONField()
    ocr_camera = models.ForeignKey(
        Camera,
        null=True, blank=True, default=None,
        on_delete=models.SET_NULL,
        related_name='log_ocr_camera',
    )
    left_camera = models.ForeignKey(
        Camera,
        null=True, blank=True, default=None,
        on_delete=models.SET_NULL,
        related_name='log_left_camera',
    )
    right_camera = models.ForeignKey(
        Camera,
        null=True, blank=True, default=None,
        on_delete=models.SET_NULL,
        related_name='log_right_camera',
    )
    front_camera = models.ForeignKey(
        Camera,
        null=True, blank=True, default=None,
        on_delete=models.SET_NULL,
        related_name='log_front_camera',
    )

    def __str__(self):
        return f'{self.history_id}. {self.container_code} {self.inout} {self.history_datetime}'


class WorkerConfig(models.Model):
    worker_id = models.AutoField(primary_key=True)
    ocr_camera = models.ForeignKey(
        Camera,
        null=True, default=None,
        on_delete=models.CASCADE,
        related_name='ocr_worker_ocr_camera',
    )
    front_camera = models.ForeignKey(
        Camera,
        null=True, default=None,
        on_delete=models.SET_NULL,
        related_name='ocr_worker_front_camera',
    )
    left_camera = models.ForeignKey(
        Camera,
        null=True, default=None,
        on_delete=models.SET_NULL,
        related_name='ocr_worker_left_camera',
    )
    right_camera = models.ForeignKey(
        Camera,
        null=True, default=None,
        on_delete=models.SET_NULL,
        related_name='ocr_worker_right_camera',
    )
    text_area_min_size = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    status = models.IntegerField(
        choices=WORKER_STATUSES,
        default=0,
    )

    def __str__(self):
        return f'OCRWorker [{self.worker_id}][{self.ocr_camera.camera_name}]'
