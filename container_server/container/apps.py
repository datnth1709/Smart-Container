#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django.apps import AppConfig

from container import signal_handlers


class ContainerConfig(AppConfig):
    name = 'container'

    def ready(self):
        # Đăng ký handler cho các sự kiện của model
        signal_handlers.register()
