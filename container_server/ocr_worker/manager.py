#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020
import copy
import sys
import time

from config.settings import log
from ocr_worker.video_source import VideoSource
from .ocr_worker import OCRWorker
from ocr_worker.video_source import VideoSourceStt
from container.models import Camera

class WorkerManager:
    workers = {}
    camera_sources = {}

    @classmethod
    def start_worker(
            cls,
            worker_config,
    ):
        if worker_config.worker_id in cls.workers:
            return

        try:
            print("manager start worker")
            (
                ocr_vidsrc, front_vidsrc,
                left_vidsrc, right_vidsrc,
            ) = cls._prepare_vidsrc_for_worker(
                worker_config,
            )
 
            ocr_worker = OCRWorker(
                worker_config=worker_config,
                ocr_vidsrc=ocr_vidsrc,
                left_vidsrc=left_vidsrc,
                right_vidsrc=right_vidsrc,
                front_vidsrc=front_vidsrc,
            )
            cls.workers[worker_config.worker_id] = ocr_worker
            ocr_worker.start()

        except Exception as exc:
            print("except manager except start worker")
            log.error(
                f'WorkerManager::start [{worker_config}] error: {exc}',
                file=sys.stderr,
            )
            if worker_config.worker_id in cls.workers:
                del cls.workers[worker_config.worker_id]
            raise IOError(f'WorkerManager::start [{worker_config}] error: {exc}')

    @classmethod
    def stop_worker(
            cls, worker_config,
    ):
        print("manager stop worker")
        if worker_config.worker_id not in cls.workers:
            return

        cls.workers[worker_config.worker_id].stop()
        del cls.workers[worker_config.worker_id]
        time.sleep(10)
        cls._clear_unused_vidsrc()

    @classmethod
    def get_vidsrc(
            cls,
            camera,
    ):  
        print("manager get_vidsrc")
        if camera is None:
            return None

        camera_id = camera.camera_id
        if camera_id in cls.camera_sources:
            camera_source = cls.camera_sources[camera_id]
        else:
            camera_stream_url = camera.stream_url
            camera_source = VideoSource(
                camera_stream_url,
                video_config={
                    **VideoSource.DfConfig,
                    'auto_pass': not camera.offline_video,
                },
                video_source_id=camera_id,
                event_listener=cls._vidsrc_callback,
            )
            cls.camera_sources[camera_id] = camera_source

        return camera_source

    @classmethod
    def _prepare_vidsrc_for_worker(cls, worker_config, ):
        return (
            cls.get_vidsrc(worker_config.ocr_camera),
            cls.get_vidsrc(worker_config.front_camera),
            cls.get_vidsrc(worker_config.left_camera),
            cls.get_vidsrc(worker_config.right_camera),
        )

    @classmethod
    def _clear_unused_vidsrc(cls):
        used_camera_ids = set()
        for worker in cls.workers.values():
            worker_config = worker.worker_config
            used_camera_ids.add(worker_config.ocr_camera.camera_id)
            if worker_config.front_camera is not None:
                used_camera_ids.add(worker_config.front_camera.camera_id)
            if worker_config.left_camera is not None:
                used_camera_ids.add(worker_config.left_camera.camera_id)
            if worker_config.right_camera is not None:
                used_camera_ids.add(worker_config.right_camera.camera_id)

        for camera_id in copy.deepcopy(list(cls.camera_sources.keys())):
            if camera_id not in used_camera_ids:
                cls.camera_sources[camera_id].stop()
                del cls.camera_sources[camera_id]

    @classmethod
    def _vidsrc_callback(cls, vidsrc_id, event):
        log.debug(
            f'Manager::_vidsrc_callback - Camera[{vidsrc_id}] set status to [{event}]'
        )

        if vidsrc_id not in cls.camera_sources:
            return

        try:
            if event is VideoSourceStt.Stopped:
                camera = Camera.objects.get(camera_id=vidsrc_id)
                camera.status = 0
                camera.save()

            elif event is VideoSourceStt.Running:
                camera = Camera.objects.get(camera_id=vidsrc_id)
                camera.status = 1
                camera.save()

        except Exception as exc:
            log.error(
                f'Manager::_vidsrc_callback - update model status failed: {exc}'
            )
