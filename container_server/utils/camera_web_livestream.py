#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import time

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators import gzip

camera_sources = {}


def gen_camera_stream_resp(
        camera_source,
        fps=10,
        scale_width=720,
        scale_height=-1,
):
    while True:
        # noinspection PyBroadException
        try:
            frame = camera_source.get_stream_data(
                scale_width=scale_width,
                scale_height=scale_height,
            ).tobytes()
            yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n'
            )
            time.sleep(float(1) / fps)

        except BaseException:
            time.sleep(0.3)
            continue


@gzip.gzip_page
def live_stream(request, camera_id):
    try:
        fps = int(request.GET.get('fps', 10))
        scale_width = int(request.GET.get('scale_width', 720))
        scale_height = int(request.GET.get('scale_height', -1))

        from container.models import Camera
        from ocr_worker.manager import WorkerManager
        from ocr_worker.video_source import VideoSource, VideoSourceStt

        # Cách này là lấy video source dùng chung với worker
        # camera_source = WorkerManager.get_vidsrc(Camera.objects.get(camera_id=camera_id))
        # if (
        #         camera_source is not None
        #         and camera_source.stt is VideoSourceStt.Init
        #         or camera_source.stt is VideoSourceStt.Stopped
        # ):
        #     camera_source.start()

        # Stream là tạo video source riêng, worker là dùng video source riêng
        if camera_id not in camera_sources:
            camera = Camera.objects.get(camera_id=camera_id)
            camera_source = VideoSource(camera.stream_url, video_source_id=camera_id)
            camera_sources[camera_id] = camera_source
            camera_source.start()
        else:
            camera_source = camera_sources[camera_id]

        return StreamingHttpResponse(
            gen_camera_stream_resp(
                camera_source,
                fps=fps,
                scale_width=scale_width,
                scale_height=scale_height,
            ),
            content_type='multipart/x-mixed-replace;boundary=frame',
        )

    except Exception as exc:
        return JsonResponse({
            'Error': f'Bad Request: {exc}'
        }, status=400)
