# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-15 12:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0054_auto_20161114_1106'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityExamScores',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cached_score_string', models.CharField(blank=True, help_text='A comma-separated list of float values which are scores for that exam.', max_length=400)),
                ('entity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='helium.Entity')),
            ],
        ),
    ]