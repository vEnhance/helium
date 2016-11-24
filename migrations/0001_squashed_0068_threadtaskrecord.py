# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-24 16:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [(b'helium', '0001_initial'), (b'helium', '0002_auto_20161004_1910'), (b'helium', '0003_auto_20161004_1919'), (b'helium', '0004_auto_20161004_2007'), (b'helium', '0005_auto_20161004_2008'), (b'helium', '0006_auto_20161005_2145'), (b'helium', '0007_problem_answer'), (b'helium', '0008_auto_20161005_2154'), (b'helium', '0009_auto_20161005_2154'), (b'helium', '0010_auto_20161006_1118'), (b'helium', '0011_auto_20161006_1154'), (b'helium', '0012_auto_20161006_1215'), (b'helium', '0013_auto_20161006_1306'), (b'helium', '0014_exam_ready'), (b'helium', '0015_auto_20161006_1413'), (b'helium', '0016_auto_20161006_1415'), (b'helium', '0017_auto_20161006_1830'), (b'helium', '0018_auto_20161008_1213'), (b'helium', '0019_auto_20161008_1216'), (b'helium', '0020_mathletealpha'), (b'helium', '0021_auto_20161008_1601'), (b'helium', '0022_auto_20161011_1543'), (b'helium', '0023_auto_20161011_1547'), (b'helium', '0024_auto_20161011_1854'), (b'helium', '0025_auto_20161012_0140'), (b'helium', '0026_auto_20161012_0157'), (b'helium', '0027_auto_20161012_1142'), (b'helium', '0028_auto_20161012_1538'), (b'helium', '0029_auto_20161012_1654'), (b'helium', '0030_gutsfunc'), (b'helium', '0031_auto_20161021_0156'), (b'helium', '0032_auto_20161021_0219'), (b'helium', '0033_auto_20161021_0221'), (b'helium', '0034_auto_20161021_0227'), (b'helium', '0035_auto_20161023_1426'), (b'helium', '0036_auto_20161023_1446'), (b'helium', '0037_auto_20161029_0008'), (b'helium', '0038_auto_20161029_0126'), (b'helium', '0039_auto_20161029_1518'), (b'helium', '0040_auto_20161029_1525'), (b'helium', '0041_auto_20161029_1528'), (b'helium', '0042_auto_20161029_2229'), (b'helium', '0043_auto_20161029_2238'), (b'helium', '0044_auto_20161029_2300'), (b'helium', '0045_auto_20161029_2304'), (b'helium', '0046_entirepdfscribble_is_done'), (b'helium', '0047_problemscribble_last_sent_time'), (b'helium', '0048_auto_20161030_1216'), (b'helium', '0049_auto_20161030_1238'), (b'helium', '0050_entirepdfscribble_exam'), (b'helium', '0051_examscribble_needs_attention'), (b'helium', '0052_auto_20161103_1919'), (b'helium', '0053_auto_20161105_1508'), (b'helium', '0054_auto_20161114_1106'), (b'helium', '0055_auto_20161115_1242'), (b'helium', '0056_auto_20161115_1249'), (b'helium', '0057_entityexamscores_rank'), (b'helium', '0058_auto_20161115_1325'), (b'helium', '0059_auto_20161115_1336'), (b'helium', '0060_auto_20161115_1402'), (b'helium', '0061_auto_20161115_1403'), (b'helium', '0062_auto_20161115_1418'), (b'helium', '0063_auto_20161115_1419'), (b'helium', '0064_auto_20161115_1420'), (b'helium', '0065_auto_20161115_1421'), (b'helium', '0066_exam_can_upload_scan'), (b'helium', '0055_examscribble_last_sent_time'), (b'helium', '0067_merge'), (b'helium', '0068_threadtaskrecord')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('registration', '0005_auto_20160928_0008'),
    ]

    operations = [
        migrations.CreateModel(
            name='Evidence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('god_mode', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_number', models.IntegerField(null=True)),
                ('cached_beta', models.FloatField(null=True)),
                ('weight', models.IntegerField()),
                ('allow_partial', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ProblemScribble',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_number', models.IntegerField()),
                ('testscan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helium.TestScribble')),
            ],
        ),
        migrations.CreateModel(
            name='Verdict',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(blank=True, null=True)),
                ('mathlete', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registration.AbstractMathlete')),
                ('problem', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='helium.Problem')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registration.AbstractTeam')),
                ('is_done', models.BooleanField(default=False, help_text='Whether this verdict should be read by more normal users')),
                ('is_valid', models.BooleanField(default=True, help_text='Whether there is an answer consensus')),
            ],
        ),
        migrations.AddField(
            model_name='problemscribble',
            name='verdict',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='helium.Verdict'),
        ),
        migrations.AddField(
            model_name='evidence',
            name='verdict',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='helium.Verdict'),
        ),
        migrations.RemoveField(
            model_name='problem',
            name='cached_beta',
        ),
        migrations.AlterField(
            model_name='problem',
            name='problem_number',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='problem',
            name='weight',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.RenameField(
            model_name='problemscribble',
            old_name='testscan',
            new_name='testscribble',
        ),
        migrations.AddField(
            model_name='problemscribble',
            name='prob_image',
            field=models.ImageField(null=True, upload_to='scans/problems/'),
        ),
        migrations.AddField(
            model_name='problem',
            name='answer',
            field=models.CharField(blank=True, default='', help_text='The answer for a problem, which is shown in help texts.', max_length=70),
        ),
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
                ('entity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='helium.Entity')),
            ],
        ),
        migrations.RemoveField(
            model_name='problemscribble',
            name='testscribble',
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
        migrations.RemoveField(
            model_name='problemscribble',
            name='problem_number',
        ),
        migrations.AlterUniqueTogether(
            name='evidence',
            unique_together=set([('verdict', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='examscribble',
            unique_together=set([('exam', 'entity')]),
        ),
        migrations.AlterField(
            model_name='problem',
            name='weight',
            field=models.FloatField(default=1),
        ),
        migrations.AlterField(
            model_name='problem',
            name='allow_partial',
            field=models.BooleanField(default=False, help_text='If true, all recorded scores should be 0 or 1. If false, all recorded scores should be integers from 0 to the weight.'),
        ),
        migrations.AlterUniqueTogether(
            name='problem',
            unique_together=set([('exam', 'problem_number')]),
        ),
        migrations.AddField(
            model_name='verdict',
            name='entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='helium.Entity'),
        ),
        migrations.RemoveField(
            model_name='verdict',
            name='mathlete',
        ),
        migrations.RemoveField(
            model_name='verdict',
            name='team',
        ),
        migrations.AlterUniqueTogether(
            name='verdict',
            unique_together=set([('problem', 'entity')]),
        ),
        migrations.AddField(
            model_name='exam',
            name='is_ready',
            field=models.BooleanField(default=True, help_text='Mark true if you want users to be able to grade this exam. You should set it to False if you are waiting for scans for example. You can also set it to False after the exam is *done* grading, so as not to distract users. Note that this does not affect validation, it only affects the UI: in other words users can still navigate directly to a URL to grade this exam.'),
        ),
        migrations.RenameField(
            model_name='exam',
            old_name='alg_scoring',
            new_name='is_alg_scoring',
        ),
        migrations.AlterField(
            model_name='evidence',
            name='verdict',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidences', to='helium.Verdict'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='color',
            field=models.CharField(default='#FFFFFF', help_text='Color which exam is printed on (shows up when grading)', max_length=50),
        ),
        migrations.AlterField(
            model_name='evidence',
            name='verdict',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helium.Verdict'),
        ),
        migrations.AddField(
            model_name='exam',
            name='min_grades',
            field=models.IntegerField(default=3, help_text='This is the minimum number of graders required before  a problem is marked as `done grading` by the system.'),
        ),
        migrations.AddField(
            model_name='exam',
            name='min_override',
            field=models.IntegerField(default=3, help_text='Number of graders required to override a grading conflict. For example, the default setting is that a 3:1 majority is sufficient to override a conflicting grade.'),
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('is_team', models.BooleanField(default=False)),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='helium.Entity')),
            ],
        ),
        migrations.CreateModel(
            name='EntityAlpha',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cached_alpha', models.FloatField(blank=True, null=True)),
                ('entity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='helium.Entity')),
            ],
        ),
        migrations.AddField(
            model_name='entity',
            name='number',
            field=models.IntegerField(blank=True, help_text="You can assign (unique) numbers here if you can't assume names are pairwise distinct.This isn't used internally by Helium itself.", null=True),
        ),
        migrations.AddField(
            model_name='entity',
            name='shortname',
            field=models.CharField(blank=True, default='', help_text='For teams, a shorter version of their name. This is used instead when attached to mathletes. Leave this blank to just use the team name instead. Leave this blank for individuals.', max_length=80),
        ),
        migrations.AlterUniqueTogether(
            name='entity',
            unique_together=set([('is_team', 'number')]),
        ),
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
            model_name='examscribble',
            name='entity',
            field=models.ForeignKey(blank=True, help_text='This is the entity the scan belongs to. It is None if the scan has not yet been identified.', null=True, on_delete=django.db.models.deletion.CASCADE, to='helium.Entity'),
        ),
        migrations.RenameField(
            model_name='examscribble',
            old_name='scan_image',
            new_name='name_image',
        ),
        migrations.AlterField(
            model_name='examscribble',
            name='name_image',
            field=models.ImageField(help_text='This is the image of the `name` field for the scan. ', null=True, upload_to='scans/names/'),
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
        migrations.CreateModel(
            name='GutsScoreFunc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_number', models.IntegerField(help_text='This is the problem number on Guts Round.', unique=True)),
                ('answer', models.CharField(help_text='True answer for problem, not actually used by model, shown in grader.', max_length=80)),
                ('scoring_function', models.TextField(default='function (x) {\n\treturn Math.round(Math.max(0, WEIGHT-Math.abs(ANS-x)));\n}', help_text='Javascript syntax for a one-variable function. This is the score reported if a staff member enters input x.\nCan span multiple lines.')),
                ('problem_help_text', models.CharField(blank=True, default='Input an integer.', help_text='An optional text that will display to help the staff member. For example, `input a string of seven letters`.', max_length=120)),
                ('description', models.CharField(blank=True, help_text='A brief description of the problem, shown only in admin interface.', max_length=80)),
            ],
        ),
        migrations.AlterField(
            model_name='evidence',
            name='score',
            field=models.IntegerField(help_text='The score assigned by the user'),
        ),
        migrations.AlterField(
            model_name='evidence',
            name='god_mode',
            field=models.BooleanField(default=False, help_text='If enabled, this piece of evidence is in GOD MODE. That means that all other evidences are ignored for that verdict.If more than one evidence is in God mode, the verdict will be marked invalid. '),
        ),
        migrations.AddField(
            model_name='examscribble',
            name='full_image',
            field=models.ImageField(help_text='This is the image of the entire scan.', null=True, upload_to='scans/full/'),
        ),
        migrations.AlterField(
            model_name='examscribble',
            name='name_image',
            field=models.ImageField(help_text='This is the image of the `name` field for the scan.', null=True, upload_to='scans/names/'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='is_alg_scoring',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='exam',
            name='is_indiv',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='exam',
            name='color',
            field=models.CharField(default='#FFFFFF', help_text="Color which exam is printed on. Grading pages will be tinted with this color so that e.g. we don't accidentally have someone enter Algebra scores into Geometry. (This was a very common mistake in old Babbage.) This color is page background so it should be VERY light (like #EEFFEE light).", max_length=50),
        ),
        migrations.CreateModel(
            name='EntirePDFScribble',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the PDF file, which must be unique (this is a safety feature to prevent accidental double uploads). ', max_length=80, unique=True)),
                ('is_done', models.BooleanField(default=False, help_text='Whether the PDF is done converting.')),
                ('exam', models.ForeignKey(default=6, help_text='The exam associated to this PDF.', on_delete=django.db.models.deletion.CASCADE, to='helium.Exam')),
            ],
        ),
        migrations.AddField(
            model_name='examscribble',
            name='pdf_scribble',
            field=models.ForeignKey(help_text='The PDF from which the exam scribble comes from.', on_delete=django.db.models.deletion.CASCADE, to='helium.EntirePDFScribble'),
        ),
        migrations.AlterField(
            model_name='examscribble',
            name='exam',
            field=models.ForeignKey(help_text='The exam associated to an exam scribble file.', on_delete=django.db.models.deletion.CASCADE, to='helium.Exam'),
        ),
        migrations.AddField(
            model_name='problemscribble',
            name='last_sent_time',
            field=models.IntegerField(blank=True, help_text='Most recent time the scan was sent out (in seconds since Epoch);reset to None when the problem is graded. This prevents the scan grader from accidentally giving duplicates.', null=True),
        ),
        migrations.AddField(
            model_name='examscribble',
            name='needs_attention',
            field=models.CharField(blank=True, default='', help_text='Text description of an issue with this scan (no name, no such student, et cetera).', max_length=80),
        ),
        migrations.AlterField(
            model_name='exam',
            name='name',
            field=models.CharField(help_text='Name of exam', max_length=50, unique=True),
        ),
        migrations.CreateModel(
            name='EntityExamScores',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cached_score_string', models.CharField(blank=True, help_text='A comma-separated list of float values which are scores for that exam.', max_length=400)),
                ('entity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='helium.Entity')),
                ('category', models.CharField(default='', help_text='Category for this score list (for example, name of exam).', max_length=80)),
                ('rank', models.IntegerField(default=0, help_text='Relative rank of this result row')),
                ('total', models.FloatField(default=0, help_text='Total score')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='entityexamscores',
            unique_together=set([('category', 'entity')]),
        ),
        migrations.RenameModel(
            old_name='EntityExamScores',
            new_name='ScoreRow',
        ),
        migrations.AlterField(
            model_name='scorerow',
            name='rank',
            field=models.IntegerField(help_text='Relative rank of this result row', null=True),
        ),
        migrations.AlterField(
            model_name='scorerow',
            name='cached_score_string',
            field=models.CharField(blank=True, default='', help_text='A comma-separated list of float values which are scores for that exam.', max_length=400),
        ),
        migrations.AlterUniqueTogether(
            name='scorerow',
            unique_together=set([]),
        ),
        migrations.AlterField(
            model_name='scorerow',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helium.Entity'),
        ),
        migrations.AlterUniqueTogether(
            name='scorerow',
            unique_together=set([('category', 'entity')]),
        ),
        migrations.AddField(
            model_name='exam',
            name='can_upload_scan',
            field=models.BooleanField(default=False, help_text='Mark true if you want users to be able to upload scans this exam. You should set it to False after all exams are scanned, to decrease the chance that someone uploads a scan to the wrong place.'),
        ),
        migrations.AddField(
            model_name='examscribble',
            name='last_sent_time',
            field=models.IntegerField(blank=True, help_text='Most recent time the scan was sent out (in seconds since Epoch);this prevents the name-match from giving duplicates.', null=True),
        ),
        migrations.CreateModel(
            name='ThreadTaskRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, help_text='Name of the task being fired', max_length=80)),
                ('status', models.NullBooleanField(help_text='True for success and False for failed task')),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('output', models.TextField(help_text='Output from the task')),
                ('user', models.ForeignKey(help_text='This is the user requesting the task', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
