#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django.contrib import admin, messages
from django.db.models import BLANK_CHOICE_DASH
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.html import format_html
from django.urls import re_path, reverse

from utils import camera_web_livestream


class CameraAdmin(admin.ModelAdmin):
    list_display = ('camera_id', 'camera_name', 'use_for_ocr', 'stream_url', 'status', 'stream', 'action',)
    list_display_links = ('camera_id', 'camera_name', 'use_for_ocr', 'stream_url', 'status', 'stream',)
    readonly_fields = ('status',)
    change_list_template = 'web_admin/camera/change_list.html'

    def action(self, obj):
        worker_config = None
        if obj.use_for_ocr:
            print("action use for ocr")
            from container.models import WorkerConfig
            worker_config = WorkerConfig.objects.filter(ocr_camera=obj)[0]

        if worker_config is None:
            print("worker config is None")
            return format_html(
                f'<a href="{reverse("admin:container_camera_live_stream", args=[obj.camera_id])}?scale_width=960" '
                f'target="_blank" class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">Stream</span></a>'
                f'<a href="{reverse("admin:container_camera_delete", args=[obj.camera_id])}" '
                f'class="btn btn-danger" style="margin:5px;"><span class="text" style="color:white">Delete</span></a>'
            )
        if worker_config.status == 0:
            print("worker_config.status == 0")
            return format_html(
                f'<a href="{reverse("admin:container_camera_live_stream", args=[obj.camera_id])}?scale_width=960" '
                f'target="_blank" class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">Stream</span></a>'
                f'<a href="{reverse("admin:container_camera_config_worker", args=[obj.camera_id])}" '
                f'class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">Config</span></a>'
                f'<a href="{reverse("admin:container_camera_start_worker", args=[obj.camera_id])}" '
                f'class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">Start Worker</span></a>'
                f'<a href="{reverse("admin:container_inouthistory_changelist")}'
                f'?ocr_camera__camera_id__exact={obj.camera_id}" '
                f'class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">View Logs</span></a>'
                f'<a href="{reverse("admin:container_camera_delete", args=[obj.camera_id])}" '
                f'class="btn btn-danger" style="margin:5px;"><span class="text" style="color:white">Delete</span></a>'
            )
        return format_html(
            f'<a href="{reverse("admin:container_camera_live_stream", args=[obj.camera_id])}?scale_width=960" '
            f'target="_blank" class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">Stream</span></a>'
            f'<a href="{reverse("admin:container_camera_stop_worker", args=[obj.camera_id])}" '
            f'class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">Stop Worker</span></a>'
            f'<a href="{reverse("admin:container_inouthistory_changelist")}'
            f'?ocr_camera__camera_id__exact={obj.camera_id}" '
            f'class="btn btn-primary" style="margin:5px;"><span class="text" style="color:white">View Logs</span></a>'
            f'<a href="{reverse("admin:container_camera_delete", args=[obj.camera_id])}" '
            f'class="btn btn-danger" style="margin:5px;"><span class="text" style="color:white">Delete</span></a>'
        )

    @classmethod
    def stream(cls, obj):
        return format_html(
            f'<img src="{reverse("admin:container_camera_live_stream", args=[obj.camera_id])}?scale_width=150" '
            f'alt="Stream error" width="150">'
        )

    action.short_description = 'actions'

    def get_action_choices(self, request, default_choices=BLANK_CHOICE_DASH):
        choices = super(CameraAdmin, self).get_action_choices(request)
        choices.pop(0)
        return choices

    def get_urls(self):
        urls = super().get_urls()
        print("get_urls")
        extend_urls = [
            re_path(
                r'^(?P<camera_id>.+)/config-worker/$',
                self.admin_site.admin_view(self.config_worker),
                name=f'container_camera_config_worker',
            ),
            re_path(
                r'^(?P<camera_id>.+)/start-worker/$',
                self.admin_site.admin_view(self.start_worker),
                name=f'container_camera_start_worker',
            ),
            re_path(
                r'^(?P<camera_id>.+)/stop-worker/$',
                self.admin_site.admin_view(self.stop_worker),
                name=f'container_camera_stop_worker',
            ),
            re_path(
                r'^(?P<camera_id>.+)/live-stream/$',
                self.admin_site.admin_view(self.live_stream),
                name=f'container_camera_live_stream',
            ),
        ]
        return extend_urls + urls

    @classmethod
    def config_worker(cls, request, camera_id):
        try:
            print("config_worker")
            from container.models import Camera, WorkerConfig
            worker_config = WorkerConfig.objects.filter(ocr_camera__camera_id=camera_id)[0]

            return HttpResponseRedirect(reverse(
                'admin:container_workerconfig_change',
                args=[worker_config.worker_id],
            ))

        except Exception as exc:
            print("exception config worker")
            messages.add_message(
                request,
                messages.ERROR,
                f'Goto WorkerConfig for camera [{camera_id}] failed: {exc}',
            )
            # return HttpResponseRedirect(reverse('admin:container_camera_changelist'))
            return redirect('./')

    @classmethod
    def start_worker(cls, request, camera_id):
        try:
            print("Start worker 1 ...")
            from container.models import Camera, WorkerConfig
            camera = Camera.objects.get(camera_id=camera_id)
            if not camera.use_for_ocr:
                raise ValueError(f'camera is not used for ocr')
            worker_config = WorkerConfig.objects.filter(ocr_camera__camera_id=camera_id)[0]
            print("Start worker 2 ...")
            from ocr_worker.manager import WorkerManager
            WorkerManager.start_worker(worker_config=worker_config)
            worker_config.status = 1
            worker_config.save()
            print("Start worker 3 ...")
            messages.add_message(
                request,
                messages.INFO,
                f'Start OCRWorker for camera [{camera}] successfully',
            )
            return HttpResponseRedirect(reverse('admin:container_camera_changelist'))
            print("Start worker 1 ...")
        except Exception as exc:
            print("Start worker except ...")
            messages.add_message(
                request,
                messages.ERROR,
                f'Start OCRWorker for camera [{camera_id}] failed: {exc}',
            )
            # return HttpResponseRedirect(reverse('admin:container_camera_changelist'))
            return redirect('./')

    @classmethod
    def stop_worker(cls, request, camera_id):
        try:
            print("stop worker")
            from container.models import Camera, WorkerConfig
            camera = Camera.objects.get(camera_id=camera_id)
            if not camera.use_for_ocr:
                raise ValueError(f'camera is not used for ocr')
            worker_config = WorkerConfig.objects.filter(ocr_camera__camera_id=camera_id)[0]

            from ocr_worker.manager import WorkerManager
            WorkerManager.stop_worker(worker_config=worker_config)
            worker_config.status = 0
            worker_config.save()

            messages.add_message(
                request,
                messages.INFO,
                f'Stop OCRWorker for camera [{camera}] successfully',
            )
            return HttpResponseRedirect(reverse('admin:container_camera_changelist'))

        except Exception as exc:
            print("exception stop_worker")
            messages.add_message(
                request,
                messages.ERROR,
                f'Stop OCRWorker for camera [{camera_id}] failed: {exc}',
            )
            # return HttpResponseRedirect(reverse('admin:container_camera_changelist'))
            return redirect('./')

    @classmethod
    def live_stream(cls, request, camera_id):
        print("live_stream")
        return camera_web_livestream.live_stream(request, camera_id)
