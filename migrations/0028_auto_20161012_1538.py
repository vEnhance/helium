# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-12 15:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('helium', '0027_auto_20161012_1142'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='is_scanned',
            field=models.BooleanField(default=False, help_text='Whether the scan grader will show this problem or not. For example, this should almost certainly be False for Guts round.'),
        ),
        migrations.AlterField(
            model_name='evidence',
            name='god_mode',
            field=models.BooleanField(default=False, help_text='If enabled, this piece of evidence is in GOD MODE. That means that all other evidences are ignored for that verdict. If more than one evidence is in God mode, the verdict will be marked invalid. This option is not present in the user interface; it is meant to be set manually from inside the administration interface.'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='color',
            field=models.CharField(default='#FFFFFF', help_text="Color which exam is printed on. Grading pages will be tinted with this color so that e.g. we don't accidentally have someone enter Algebra scores into Geometry. (This was a very common mistake in old Babbage.", max_length=50),
        ),
        migrations.AlterField(
            model_name='exam',
            name='min_grades',
            field=models.IntegerField(default=3, help_text='This is the minimum number of graders required before  a problem is marked as `done grading` by the system.'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='min_override',
            field=models.IntegerField(default=3, help_text='Number of graders required to override a grading conflict. For example, the default setting is that a 3:1 majority is sufficient to override a conflicting grade.'),
        ),
        migrations.AlterField(
            model_name='examscribble',
            name='entity',
            field=models.ForeignKey(blank=True, help_text='This is the entity the scan belongs to. It is None if the scan has not yet been identified.', null=True, on_delete=django.db.models.deletion.CASCADE, to='helium.Entity'),
        ),
        migrations.AlterField(
            model_name='examscribble',
            name='scan_image',
            field=models.ImageField(help_text='This is the image of the `name` field for the scan. ', null=True, upload_to='scans/names/'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='allow_partial',
            field=models.BooleanField(default=False, help_text='If true, all recorded scores should be 0 or 1. If false, all recorded scores should be integers from 0 to the weight.'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='answer',
            field=models.CharField(default='', help_text='The answer for a problem, which is shown in help texts.', max_length=70),
        ),
        migrations.AlterField(
            model_name='problem',
            name='problem_number',
            field=models.IntegerField(help_text='Must be unique per exam.'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='weight',
            field=models.FloatField(default=1, help_text='This is the weight of the problem. For tests with algorithmic scoring, this is overwritten later with beta values, and therefore the value of the weight is unimportant. For tests scored traditionally this weight should be an integer.'),
        ),
        migrations.AlterField(
            model_name='verdict',
            name='entity',
            field=models.ForeignKey(blank=True, help_text='This should be None for scans which have not yet been matched.', null=True, on_delete=django.db.models.deletion.CASCADE, to='helium.Entity'),
        ),
        migrations.AlterField(
            model_name='verdict',
            name='is_done',
            field=models.BooleanField(default=False, help_text='Whether this verdict should be read by more normal users as determined by the min_grades setting of the exam. You should not need to touch this setting; it is auto-computed.'),
        ),
        migrations.AlterField(
            model_name='verdict',
            name='is_valid',
            field=models.BooleanField(default=True, help_text='This is True if there are no conflicts in grading as determined by the min_override setting of the exam. You should not need to touch this setting; it is auto-computed.'),
        ),
        migrations.AlterField(
            model_name='verdict',
            name='score',
            field=models.IntegerField(blank=True, help_text='This should be 0 or 1 for all-or-nothing problems, and the actual score for problems which have weights. You should not need to touch this setting; it is auto-computed.', null=True),
        ),
    ]
