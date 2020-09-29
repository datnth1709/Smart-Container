#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import sys

from django.db.models import signals as db_signals

from config.settings import log


class CameraSignalHandler:
    @classmethod
    def post_save(
            cls, sender, instance,
            created, raw, using, update_fields,
            **kwargs,
    ):
        from container.models import WorkerConfig
        if created:
            # Nếu mới tạo camera mà set nó là dùng để OCR thì tạo config cho worker
            if instance.use_for_ocr:
                log.debug(f'Camera OCR mới [{instance}], tạo worker...')
                worker_config = WorkerConfig(
                    ocr_camera=instance,
                )
                worker_config.save()
                log.debug(f'Camera OCR mới [{instance}], tạo worker thành công')

            log.debug(f'Camera mới [{instance}], check status...')
            from ocr_worker.video_source import check
            connected = check(instance.stream_url)
            instance.status = 1 if connected else 0
            instance.save()
            log.debug(f'Camera mới [{instance}], check status và lưu thành công')

        elif update_fields is not None:
            if 'use_for_ocr' in update_fields:
                # Nếu thay đổi trường "dùng cho OCR"
                if instance.use_for_ocr:
                    # Chuyển từ không phải dùng cho OCR sang dùng cho OCR
                    log.debug(f'Camera đổi sang OCR [{instance}], tạo worker...')
                    worker_config = WorkerConfig(
                        ocr_camera=instance,
                    )
                    worker_config.save()
                    log.debug(f'Camera đổi sang OCR [{instance}], tạo worker thành công [{worker_config}]')
                else:
                    # Chuyển từ dùng cho OCR sang không dùng cho OCR
                    log.debug(f'Camera không dùng cho OCR nữa [{instance}], xóa worker...')
                    worker_config = WorkerConfig.objects.get(
                        ocr_camera=instance,
                    )
                    worker_config.delete()
                    log.debug(f'Camera không dùng cho OCR nữa [{instance}], xóa worker thành công')

            if 'stream_url' in update_fields:
                log.debug(f'Camera bị đổi stream_url [{instance}], check status')
                from ocr_worker.video_source import check
                connected = check(instance.stream_url)
                instance.status = 1 if connected else 0
                instance.save()
                log.debug(f'Camera bị đổi stream_url [{instance}], check status và lưu thành công')


class WorkerSignalHandler:
    @classmethod
    def post_delete(
            cls, sender, instance, using,
            **kwargs,
    ):
        from ocr_worker.manager import WorkerManager
        WorkerManager.stop_worker(instance)


class InOutHistorySignalHandler:
    # noinspection PyBroadException
    @classmethod
    def post_delete(
            cls, sender, instance, using,
            **kwargs,
    ):
        if instance.captured_images.get('ocr_image', None) is not None:
            try:
                from utils.static_util import StaticUtil
                StaticUtil.delete(
                    instance.ocr_camera.camera_id, instance.history_id
                )
            except Exception as exc:
                log.error(f'InOutHistory [{instance.history_id}] - remove images failed: {exc}')


def register():
    from container.models import Camera, WorkerConfig, InOutHistory
    db_signals.post_save.connect(
        CameraSignalHandler.post_save, sender=Camera,
    )

    db_signals.post_delete.connect(
        WorkerSignalHandler.post_delete, sender=WorkerConfig,
    )

    db_signals.post_delete.connect(
        InOutHistorySignalHandler.post_delete, sender=InOutHistory,
    )
