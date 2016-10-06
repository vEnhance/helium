# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-06 11:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0005_auto_20160928_0008'),
        ('helium', '0010_auto_20161006_1118'),
    ]

    operations = [
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of exam', max_length=50)),
                ('color', models.CharField(default='000000', help_text='Hex code for color exam printed on', max_length=50)),
                ('is_indiv', models.BooleanField()),
                ('alg_scoring', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='ExamScribble',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scan_image', models.ImageField(null=True, upload_to='scans/names/')),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helium.Exam')),
                ('mathlete', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registration.AbstractMathlete')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registration.AbstractTeam')),
            ],
        ),
        migrations.RemoveField(
            model_name='testscribble',
            name='mathlete',
        ),
        migrations.RemoveField(
            model_name='testscribble',
            name='team',
        ),
        migrations.RemoveField(
            model_name='testscribble',
            name='test',
        ),
        migrations.RemoveField(
            model_name='problem',
            name='test',
        ),
        migrations.RemoveField(
            model_name='problemscribble',
            name='testscribble',
        ),
        migrations.DeleteModel(
            name='Test',
        ),
        migrations.DeleteModel(
            name='TestScribble',
        ),
        migrations.AddField(
            model_name='problem',
            name='exam',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='helium.Exam'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='problemscribble',
            name='examscribble',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='helium.ExamScribble'),
            preserve_default=False,
        ),
    ]
