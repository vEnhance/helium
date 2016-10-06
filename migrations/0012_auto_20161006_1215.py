# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-06 12:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0011_auto_20161006_1154'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problemscribble',
            name='problem_number',
        ),
        migrations.AddField(
            model_name='problemscribble',
            name='problem',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='helium.Problem'),
            preserve_default=False,
        ),
    ]
