# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-30 12:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0048_auto_20161030_1216'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entirepdfscribble',
            name='scan_file',
        ),
        migrations.AlterField(
            model_name='entirepdfscribble',
            name='is_done',
            field=models.BooleanField(default=False, help_text='Whether the PDF is done converting.'),
        ),
    ]