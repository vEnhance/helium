# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-12 01:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0024_auto_20161011_1854'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='entity',
            unique_together=set([('name', 'team')]),
        ),
    ]
