# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-21 01:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0029_auto_20161012_1654'),
    ]

    operations = [
        migrations.CreateModel(
            name='GutsFunc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_number', models.IntegerField(help_text='This is the problem number on Guts Round.', unique=True)),
                ('answer', models.CharField(help_text='Answer for problem, not actually used by model, shown in grader.', max_length=80)),
                ('scoring_function', models.TextField(help_text='Javascript syntax for a one-variable function. This is the score reported if a staff member enters input x. For example `function (x) { return 0; }`. Can span multiple lines.')),
                ('problem_help_text', models.CharField(help_text='An optional text that will display to help the staff member. For example, `input a string of seven letters`.', max_length=120)),
            ],
        ),
    ]
