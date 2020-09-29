#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import django_filters

from .models import InOutHistory


class InOutHistoryFilter(django_filters.FilterSet):
    class Meta:
        model = InOutHistory
        fields = ('history_id', 'history_datetime', 'inout', 'container_code',)
