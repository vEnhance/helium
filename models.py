from __future__ import unicode_literals

from django.db import models
from django.contrib.auth import models as auth
from django.core.exceptions import ValidationError
import registration.models as reg

def validateForeignKey(obj, is_indiv, nonempty=False):
    """Takes an object which has both a "team" and "mathlete" column.
    Args is_indiv, nonempty are booleans."""
    if is_indiv:
        if obj.team is not None:
            raise ValidationError("Individual problems can't have teams attached")
        if obj.mathlete is None and nonempty is True:
            raise ValidationError("Individual verdict has no individual attached")
    else:
        if obj.mathlete is not None:
            raise ValidationError("Team problems can't have mathletes attached")
        if obj.team is None and nonempty is True:
            raise ValidationError("Team problems has no team attached")


class Test(models.Model):
    name = models.CharField(max_length=50, help_text='Name of test')
    color = models.CharField(max_length=50, default='000000',\
            help_text='Hex code for color test printed on')
    is_indiv = models.BooleanField()
    algorithm_scoring = models.BooleanField()
    def __unicode__(self): return self.name

class Problem(models.Model):
    test = models.ForeignKey(Test)
    problem_number = models.IntegerField()

    cached_beta = models.FloatField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    allow_partial = models.BooleanField(default=False)
    def __unicode__(self): return self.test.name + " #" + unicode(self.problem_number)

# Scribble objects
class TestScribble(models.Model):
    test = models.ForeignKey(Test)
    mathlete = models.ForeignKey(reg.AbstractMathlete, blank=True, null=True)
    team = models.ForeignKey(reg.AbstractTeam, blank=True, null=True)
    scan_image = models.ImageField(upload_to='scans/names/')

    def clean(self):
        validateForeignKey(self, self.test.is_indiv)
    def __unicode__(self):
		if self.mathlete is not None:
			who = unicode(self.mathlete)
		elif self.team is not None:
			who = unicode(self.team)
		else:
			who = '???'
		return 'Scan ' + unicode(self.id) + ' for ' + who

class Verdict(models.Model):
    problem = models.ForeignKey(Problem) # You should know which problem

    # You might have verdicts for which you don't know whose yet
    # because the verdict is created by a to-be-matched scribble
    mathlete = models.ForeignKey(reg.AbstractMathlete, blank=True, null=True)
    team = models.ForeignKey(reg.AbstractTeam, blank=True, null=True)
    cached_score = models.IntegerField(blank=True, null=True) # integer, score for the problem
    cached_valid = models.NullBooleanField(default=None, blank=True, null=True) # whether all evidence makes sense

    def clean(self):
        if self.problem is not None:
            validateForeignKey(self, self.problem.test.is_indiv)
    def __unicode__(self):
        if self.mathlete is not None:
            who = unicode(self.mathlete)
        elif self.team is not None:
            who = unicode(self.team)
        else:
            who = '???'
        return unicode(self.problem) + ' for ' + who

class ProblemScribble(models.Model):
    problem_number = models.IntegerField()
    testscribble = models.ForeignKey(TestScribble)
    verdict = models.OneToOneField(Verdict, on_delete=models.CASCADE)
    scan_image = models.ImageField(upload_to='scans/problems/')

    # I have no idea what cascade does, lol
    def __unicode__(self): return unicode(self.verdict)
    
class Evidence(models.Model):
    verdict = models.ForeignKey(Verdict)
    user = models.ForeignKey(auth.User)
    score = models.IntegerField()
    god_mode = models.BooleanField(default=False)
    def __unicode__(self): return unicode(self.id)

# vim: expandtab
