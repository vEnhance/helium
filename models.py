from __future__ import unicode_literals

from django.db import models
from django.contrib.auth import models as auth
from django.core.exceptions import ValidationError
import registration.models as reg

def validateMathleteVsTeam(obj, is_indiv, nonempty=False):
    """Takes an object which has both a "team" and "mathlete" column.
    Args is_indiv, nonempty are booleans."""
    if is_indiv:
        if obj.team is not None:
            obj.team = None
            raise ValidationError("Individual problems can't have teams attached")
        if obj.mathlete is None and nonempty is True:
            raise ValidationError("Individual verdict has no individual attached")
    else:
        if obj.mathlete is not None:
            obj.mathlete = None
            raise ValidationError("Team problems can't have mathletes attached")
        if obj.team is None and nonempty is True:
            raise ValidationError("Team problems has no team attached")


class Exam(models.Model):
    name = models.CharField(max_length=50, help_text='Name of exam')
    color = models.CharField(max_length=50, default='000000',\
            help_text='Hex code for color exam printed on')
    is_indiv = models.BooleanField()
    alg_scoring = models.BooleanField()
    def __unicode__(self): return self.name

class Problem(models.Model):
    exam = models.ForeignKey(Exam)
    problem_number = models.IntegerField()
    answer = models.CharField(max_length=70, default='')

    cached_beta = models.FloatField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    allow_partial = models.BooleanField(default=False)
    def __unicode__(self): return self.exam.name + " #" + unicode(self.problem_number)

    class Meta:
        unique_together = ('exam', 'problem_number')

# Scribble objects
class ExamScribble(models.Model):
    exam = models.ForeignKey(Exam)
    mathlete = models.ForeignKey(reg.AbstractMathlete, blank=True, null=True)
    team = models.ForeignKey(reg.AbstractTeam, blank=True, null=True)
    scan_image = models.ImageField(upload_to='scans/names/', blank=False, null=True)
         # blargh. This should really be null=False, but it makes testing hard.

    def clean(self):
        validateMathleteVsTeam(self, self.exam.is_indiv)
    def __unicode__(self):
        if self.mathlete is not None:
            who = unicode(self.mathlete)
        elif self.team is not None:
            who = unicode(self.team)
        else:
            who = '???'
        return 'Scan ' + unicode(self.id) + ' for ' + who

    def assignTeam(self, team):
        self.team = team
        self.save()
        self.clean()
        self.updateScribbles()
    def assignMathlete(self, mathlete):
        self.mathlete = mathlete
        self.save()
        self.clean()
        self.updateScribbles()

    def updateScribbles(self):
        """Update all child scribbles once mathlete/team identified"""
        for ps in self.problemscribble_set.all():
            ps.verdict.mathlete = self.mathlete
            ps.verdict.team = self.team
            ps.verdict.save()

    class Meta:
        unique_together = ('exam', 'mathlete', 'team')

class Verdict(models.Model):
    problem = models.ForeignKey(Problem) # You should know which problem

    # You might have verdicts for which you don't know whose yet
    # because the verdict is created by a to-be-matched scribble
    mathlete = models.ForeignKey(reg.AbstractMathlete, blank=True, null=True)
    team = models.ForeignKey(reg.AbstractTeam, blank=True, null=True)
    score = models.IntegerField(blank=True, null=True) # integer, score for the problem
    is_valid = models.BooleanField(default=True)  # whether all evidence makes sense
    is_done = models.BooleanField(default=False)  # whether enough evidence to arrive at final verdict

    def clean(self):
        if self.problem is not None:
            validateMathleteVsTeam(self, self.problem.exam.is_indiv)
    def __unicode__(self):
        if self.mathlete is not None:
            who = unicode(self.mathlete)
        elif self.team is not None:
            who = unicode(self.team)
        else:
            who = '???'
        return unicode(self.problem) + ' for ' + who

    def submitEvidence(self, user, score, god_mode=False):
        """Creates an evidence object for a given verdict, and updates self."""
        evidence = Evidence.objects.create(verdict=self, user=user, score=score, god_mode=god_mode)
        self.updateDecisions()
        return evidence

    def updateDecisions(self):
        """Reads through all evidence available to self and gives verdict."""
        all_evidence = self.evidence_set.all()
        strong_evidence = [e for e in all_evidence if e.god_mode is True]
        weak_evidence   = [e for e in all_evidence if e.god_mode is False]
        if len(strong_evidence) > 1:
            # We have more than one "god mode" evidence, this is bad. GIVE UP.
            self.score = None
            self.is_valid, self.is_done = False, False
        elif len(strong_evidence) == 1:
            # Follow god mode evidence
            e = strong_evidence[0]
            self.score = e.score
            self.is_valid, self.is_done = True, True
        else: # len(strong_evidence) == 0
            scores = [e.score for e in weak_evidence]
            if len(scores) == 0: # have no data
                self.score = None
                self.is_valid, self.is_done = True, False
            elif len(scores) == 1: # have one evidence, but need double grading
                self.score = scores[0]
                self.is_valid, self.is_done = True, False
            elif scores.count(scores[0]) == len(scores): # all >= 2 scores agree
                self.score = scores[0]
                self.is_valid, self.is_done = True, True
            else: # conflict in scores
                self.score = None
                self.is_valid, self.is_done = False, False
        self.save()

    class Meta:
        unique_together = ('problem', 'mathlete', 'team')

class ProblemScribble(models.Model):
    examscribble = models.ForeignKey(ExamScribble)
    verdict = models.OneToOneField(Verdict, on_delete=models.CASCADE)
    scan_image = models.ImageField(upload_to='scans/problems/', blank=False, null=True)
         # blargh. This should really be null=False, but it makes testing hard.

    # I have no idea what cascade does, lol
    def __unicode__(self): return unicode(self.verdict)
    
class Evidence(models.Model):
    verdict = models.ForeignKey(Verdict)
    user = models.ForeignKey(auth.User)
    score = models.IntegerField()
    god_mode = models.BooleanField(default=False)
    def __unicode__(self): return unicode(self.id)

    class Meta:
        unique_together = ('verdict', 'user')

# vim: expandtab
