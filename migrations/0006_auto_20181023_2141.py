# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2018-10-24 01:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0005_verdict_scanned_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entityalpha',
            name='entity',
        ),
        migrations.DeleteModel(
            name='EntityAlpha',
        ),
    ]