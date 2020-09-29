#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

# Generated by Django 2.2.6 on 2019-10-26 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0013_auto_20191026_1643'),
    ]

    operations = [
        migrations.AddField(
            model_name='containerhandling',
            name='handling_type',
            field=models.IntegerField(choices=[(1, 'Single'), (2, 'Double')], default=1),
        ),
    ]
