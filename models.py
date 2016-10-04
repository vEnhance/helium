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
        if obj.indiv is not None:
            raise ValidationError("Team problems can't have mathletes attached")
        if obj.mathlete is None and nonempty is True:
            raise ValidationError("Team problems has no team attached")


class Test(models.Model):
    name = models.CharField(max_length=50, help_text='Name of test', null=False)
    color = models.CharField(max_length=50, default='000000',\
            help_text='Hex code for color test printed on')
    is_indiv = models.BooleanField(null=False)
    algorithm_scoring = models.BooleanField(null=False)

class Problem(models.Model):
    test = models.ForeignKey(Test, null=False)
    problem_number = models.IntegerField(null=True)

    cached_beta = models.FloatField(null=True)
    weight = models.IntegerField(null=False)
    allow_partial = models.BooleanField(default=False, null=False)

# Scribble objects
class TestScribble(models.Model):
    test = models.ForeignKey(Test, null=False)
    mathlete = models.ForeignKey(reg.AbstractMathlete, null=True)
    team = models.ForeignKey(reg.AbstractTeam, null=True)
    scan_image = models.FileField(null=False)

    def clean(self):
        validateForeignKey(self, self.problem.test.is_indiv)

class Verdict(models.Model):
    # You might have verdicts for which you don't know any of these
    # because the verdict is created by a to-be-matched scribble
    problem = models.ForeignKey(Problem, null=True)
    mathlete = models.ForeignKey(reg.AbstractMathlete, null=True)
    team = models.ForeignKey(reg.AbstractTeam, null=True)
    cached_score = models.IntegerField(null=True) # integer, score for the problem
    cached_valid = models.NullBooleanField(default=None, null=True) # whether all evidence makes sense

    def clean(self):
        validateForeignKey(self, self.problem.test.is_indiv)

class ProblemScribble(models.Model):
    problem_number = models.IntegerField(null=False)
    testscan = models.ForeignKey(TestScribble, null=False)
    verdict = models.OneToOneField(Verdict, on_delete=models.CASCADE)
    # I have no idea what cascade does, lol
    
class Evidence(models.Model):
    verdict = models.ForeignKey(Verdict, null=True)
    user = models.ForeignKey(auth.User, null=False)
    score = models.IntegerField(null=False)
    god_mode = models.BooleanField(default=False, null=False) # I'm Sherlock, do what I say
