# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-12 11:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0026_auto_20161012_0157'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problem',
            name='cached_beta',
        ),
        migrations.AlterField(
            model_name='problem',
            name='weight',
            field=models.FloatField(default=1),
        ),
    ]
