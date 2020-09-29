#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django import template

from container.models import InOutHistory

register = template.Library()


@register.inclusion_tag('web_admin/custom_tags/history_filter.html')
def history_filter():
    io_historys = InOutHistory.objects.all()
    return {
        'io_historys': io_historys,
    }


