#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

# Generated by Django 2.2.6 on 2019-12-07 08:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0023_auto_20191207_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inouthistory',
            name='ocr_camera',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_ocr_camera', to='container.Camera'),
        ),
    ]
