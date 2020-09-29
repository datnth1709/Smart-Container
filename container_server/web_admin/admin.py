#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django.contrib import admin

from container.models import InOutHistory, Camera, WorkerConfig
from web_admin.model_admin.camera import CameraAdmin
from web_admin.model_admin.io_historys import InOutHistoryAdmin
from web_admin.model_admin.worker_config import WorkerConfigAdmin

admin.site.register(InOutHistory, InOutHistoryAdmin)
admin.site.register(Camera, CameraAdmin)
admin.site.register(WorkerConfig, WorkerConfigAdmin)
