# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-29 00:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0036_auto_20161023_1446'),
    ]

    operations = [
        migrations.AddField(
            model_name='examscribble',
            name='full_image',
            field=models.ImageField(help_text='This is the image of the entire scan.', null=True, upload_to='scans/full/'),
        ),
        migrations.AlterField(
            model_name='examscribble',
            name='scan_image',
            field=models.ImageField(help_text='This is the image of the `name` field for the scan.', null=True, upload_to='scans/names/'),
        ),
    ]
