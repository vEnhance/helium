# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-21 02:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0032_auto_20161021_0219'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gutsscorefunc',
            name='answer',
            field=models.CharField(blank=True, help_text='Answer for problem, not actually used by model, shown in grader.', max_length=80),
        ),
        migrations.AlterField(
            model_name='gutsscorefunc',
            name='description',
            field=models.CharField(blank=True, help_text='A brief description of the problem, for admin interface use', max_length=80),
        ),
        migrations.AlterField(
            model_name='gutsscorefunc',
            name='problem_help_text',
            field=models.CharField(blank=True, help_text='An optional text that will display to help the staff member. For example, `input a string of seven letters`.', max_length=120),
        ),
    ]
