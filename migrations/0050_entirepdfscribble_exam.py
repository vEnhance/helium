# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-03 18:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0049_auto_20161030_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='entirepdfscribble',
            name='exam',
            field=models.ForeignKey(default=6, help_text='The exam associated to this PDF.', on_delete=django.db.models.deletion.CASCADE, to='helium.Exam'),
            preserve_default=False,
        ),
    ]