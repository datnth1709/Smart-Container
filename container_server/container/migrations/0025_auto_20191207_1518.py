#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

# Generated by Django 2.2.6 on 2019-12-07 08:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0024_auto_20191207_1502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inouthistory',
            name='front_camera',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_front_camera', to='container.Camera'),
        ),
        migrations.AlterField(
            model_name='inouthistory',
            name='left_camera',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_left_camera', to='container.Camera'),
        ),
        migrations.AlterField(
            model_name='inouthistory',
            name='ocr_camera',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_ocr_camera', to='container.Camera'),
        ),
        migrations.AlterField(
            model_name='inouthistory',
            name='right_camera',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_right_camera', to='container.Camera'),
        ),
    ]
