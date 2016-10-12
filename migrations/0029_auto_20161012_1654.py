# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-12 16:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0028_auto_20161012_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='shortname',
            field=models.CharField(default='', help_text='For teams, a shorter version of their name. This is used instead when attached to mathletes. Leave this blank to just use the team name instead.', max_length=80),
        ),
        migrations.AlterField(
            model_name='exam',
            name='is_ready',
            field=models.BooleanField(default=True, help_text='Mark true if you want users to be able to grade this exam. You should set it to False if you are waiting for scans for example. You can also set it to False after the exam is *done* grading, so as not to distract users. Note that this does not affect validation, it only affects the UI: in other words users can still navigate directly to a URL to grade this exam.'),
        ),
    ]
