#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

# Generated by Django 2.2.6 on 2019-10-26 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0007_auto_20191026_1202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='camera',
            name='stream_url',
            field=models.CharField(default='rtsp://admin:Abc12345@192.168.1.100:554', max_length=2083),
        ),
    ]
