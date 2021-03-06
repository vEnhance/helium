# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-29 15:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0040_auto_20161029_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='shortname',
            field=models.CharField(blank=True, default='', help_text='For teams, a shorter version of their name. This is used instead when attached to mathletes. Leave this blank to just use the team name instead. Leave this blank for individuals.', max_length=80),
        ),
    ]
