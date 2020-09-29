#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django.contrib import admin
from django.urls import include, path

from container import views

urlpatterns = [
    path('', admin.site.urls),
    path('api/', include([
        path('rm_tmp', views.rm_tmp),
    ])),
]
