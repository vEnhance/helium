# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-05 21:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0008_auto_20161005_2154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemscribble',
            name='scan_image',
            field=models.ImageField(default=None, upload_to='scans/problems/'),
            preserve_default=False,
        ),
    ]
