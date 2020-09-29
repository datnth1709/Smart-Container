#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django.utils.translation import gettext_lazy as _

LOG_INOUT_TYPES = (
    (-1, _('In')),
    (0, _('Unknown')),
    (1, _('Out')),
)
LOG_INOUT_TYPES_DICT = {
    -1: 'In',
    0: 'Unknown',
    1: 'Out',
}

CAMERA_SIDES = (
    (1, _('Front')),
    (2, _('Back')),
    (3, _('Left')),
    (4, _('Right')),
)

CAMERA_STATUSES = (
    (-1, _('Unknown')),
    (0, _('Disconnected')),
    (1, _('Ready')),
    (2, _('Running')),
)

WORKER_STATUSES = (
    (0, _('Stopped')),
    (1, _('Running')),
    (2, _('Error')),
)

CONTAINER_TYPES = (
    ('-', _('Unknown')),
    ('J', _('Detachale freight container related equipment')),
    ('R', _('Reefer (refridgerated) container')),
    ('U', _('freight container')),
    ('Z', _('Trailers and chassis')),
)

CONTAINER_LENGTHS = (
    ('-', _('Unknown')),
    ('2', _('20 feet')),
    ('4', _('40 feet')),
    ('L', _('45 feet')),
    ('M', _('48 feet')),
)
CONTAINER_LENGTHS_DICT = {
    '-': 'Unknown',
    '2': '20 feet',
    '4': '40 feet',
    'L': '45 feet',
    'M': '48 feet',
}

CONTAINER_HEIGHTS = (
    ('-', _('Unknown')),
    ('0', _('8 feet')),
    ('2', _('8 feet 6 inches')),
    ('5', _('9 feet 6 inches')),
)
CONTAINER_HEIGHTS_DICT = {
    '-': 'Unknown',
    '0': '8 feet',
    '2': '8 feet 6 inches',
    '5': '9 feet 6 inches',
}
