# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-04 20:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0004_auto_20161004_2007'),
    ]

    operations = [
        migrations.RenameField(
            model_name='testscribble',
            old_name='name_field',
            new_name='scan_image',
        ),
    ]
