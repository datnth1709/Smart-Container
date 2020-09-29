#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

# Generated by Django 2.2.6 on 2019-10-26 09:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0012_auto_20191026_1635'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlehandlingworkerconfig',
            name='text_area_min_size',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)]),
        ),
        migrations.AlterField(
            model_name='camera',
            name='container_side',
            field=models.IntegerField(choices=[(1, 'Front'), (2, 'Back'), (3, 'Left'), (4, 'Right')], default=2),
        ),
    ]