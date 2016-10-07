from __future__ import unicode_literals

from django.db import models
from django.contrib.auth import models as auth
from django.core.exceptions import ValidationError
import registration.models as reg
import logging
import collections

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
    color = models.CharField(max_length=50, default='#FFFFFF',\
            help_text='Color which exam is printed on (shows up when grading)')
    is_indiv = models.BooleanField()
    is_ready = models.BooleanField(default=True, help_text='Mark true if ready to grade this exam')
    is_alg_scoring = models.BooleanField()
    def __unicode__(self): return self.name

class Problem(models.Model):
    exam = models.ForeignKey(Exam)
    problem_number = models.IntegerField()
    answer = models.CharField(max_length=70, default='')

    cached_beta = models.FloatField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    allow_partial = models.BooleanField(default=False)
    def __unicode__(self): return self.exam.name + " #" + unicode(self.problem_number)

    @property
    def is_indiv(self):
        return self.exam.is_indiv

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
            who = 'ID %05d' % self.id
        return unicode(self.exam) + ': ' + who


    @property
    def whom(self):
        return self.mathlete if self.is_indiv else self.team
    @property
    def is_indiv(self):
        return self.exam.is_indiv

    def assign(self, whom):
        if self.is_indiv: # indiv exam
            self.assignMathlete(whom)
        else: # team exam
            self.assignMathlete(whom)

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

    def checkConflictVerdict(self, whom, purge=False):
        """Check that no collisions will arise before updateScribbles.
        Note that purge is DANGEROUS and should use with judgment."""
        for ps in self.problemscribble_set.all():
            verdict = ps.verdict
            problem = verdict.problem
            try: # search for conflicts
                bad_v = query_verdict("get", whom, problem)
            except Verdict.DoesNotExist: 
                pass
            else:
                if bad_v == verdict:
                    # wef, these are the same?
                    # OK, something really screwy must have happened,
                    # but this is fine
                    continue
                # UH-OH, there's already a verdict attached
                if not purge: return bad_v # return counterexample and exit
                else: # forcefully grab all evidence form v then delete it
                    for e in bad_v.evidence_set.all():
                        if e.user == self.user and Evidence.objects.filter\
                                (verdict=verdict, user=self.user).exists():
                            # geez this is so bad
                            logging.warn("Deleting " + str(e.id))
                            e.delete()
                        else:
                            e.verdict = verdict
                            e.save()
                    logging.warn("Deleting " + str(bad_v.id) + " = " + str(bad_v))
                    bad_v.delete()
                    verdict.updateDecisions()
        return None # no conflicts

    class Meta:
        unique_together = (('exam', 'mathlete'), ('exam', 'team'))

class Verdict(models.Model):
    problem = models.ForeignKey(Problem) # You should know which problem

    # You might have verdicts for which you don't know whose yet
    # because the verdict is created by a to-be-matched scribble
    mathlete = models.ForeignKey(reg.AbstractMathlete, blank=True, null=True)
    team = models.ForeignKey(reg.AbstractTeam, blank=True, null=True)
    score = models.IntegerField(blank=True, null=True) # integer, score for the problem
    is_valid = models.BooleanField(default=True,
            help_text = "Whether there is an answer consensus")
    is_done = models.BooleanField(default=False,
            help_text = "Whether this verdict should be read by more normal users")

    def clean(self):
        if self.problem is not None:
            validateMathleteVsTeam(self, self.is_indiv)
    def __unicode__(self):
        if self.mathlete is not None:
            who = unicode(self.mathlete)
        elif self.team is not None:
            who = unicode(self.team)
        else:
            who = 'ID %05d' % self.id
        return unicode(self.problem) + ': ' + who

    def submitEvidence(self, user, score, god_mode=False):
        """Creates an evidence object for a given verdict, and updates self."""
        try:
            e = Evidence.objects.get(verdict=self, user=user)
            e.score = score
            e.god_mode = god_mode
        except Evidence.DoesNotExist:
            e = Evidence.objects.create(verdict=self, user=user, score=score, god_mode=god_mode)
        e.save()
        self.updateDecisions()

    def updateDecisions(self, queryset = None):
        """Reads through all evidence available to self and gives verdict.
        Can restrict search to a particular queryset.
        NOTE: queryset should NOT be a generator"""
        if queryset is None:
            queryset = self.evidence_set.all()
        strong_evidence = [e for e in queryset if e.god_mode is True]
        weak_evidence   = [e for e in queryset if e.god_mode is False]
        if len(strong_evidence) > 1:
            # We have more than one "god mode" evidence, this is bad. GIVE UP.
            self.score = None
            self.is_valid, self.is_done = False, True
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
            elif len(scores) == 1:
                self.score = scores[0] # TODO dubious --- but fun for prelim results?
                self.is_valid, self.is_done = True, False
            elif len(scores) == 2 :
                if scores[0] == scores[1]:
                    self.score = scores[0]
                    self.is_valid, self.is_done = True, False
                else:
                    self.score = None
                    self.is_valid, self.is_done = False, False
            else: # see if we have consensus
                mode_score, n = collections.Counter(scores).most_common(1)[0]
                if 4 * n >= 3 * len(scores): # need at least 3/4 majority
                    self.score = mode_score
                    self.is_valid, self.is_done = True, True
                else: # not good enough consensus
                    self.score = None
                    self.is_valid, self.is_done = False, False
        self.save()

    def evidence_count(self):
        return self.evidence_set.count()

    @property
    def is_indiv(self):
        return self.problem.is_indiv
    @property
    def whom(self):
        return self.mathlete if self.is_indiv else self.team

    class Meta:
        unique_together = (('problem', 'mathlete'), ('problem', 'team'))

class ProblemScribble(models.Model):
    examscribble = models.ForeignKey(ExamScribble)
    verdict = models.OneToOneField(Verdict, on_delete=models.CASCADE)
    scan_image = models.ImageField(upload_to='scans/problems/', blank=False, null=True)
         # blargh. This should really be null=False, but it makes testing hard.

    def __unicode__(self): return unicode(self.verdict)

    def submitEvidence(self, *args, **kwargs):
        self.verdict.submitEvidence(*args, **kwargs)
    
class Evidence(models.Model):
    verdict = models.ForeignKey(Verdict)
    user = models.ForeignKey(auth.User)
    score = models.IntegerField()
    god_mode = models.BooleanField(default=False)
    def __unicode__(self): return unicode(self.id)

    def clean(self):
        if not self.verdict.problem.allow_partial and not self.score in (0,1):
            raise ValidationError("All-or-nothing problem with non-binary score")

    class Meta:
        unique_together = ('verdict', 'user')

def query_verdict(method, whom, problem, *args, **kwargs):
    """Wrapper function to get a verdict for either mathlete or team"""
    method_func = getattr(Verdict.objects, method)
    if problem.exam.is_indiv:
        return method_func(*args, mathlete = whom, problem = problem, **kwargs)
    else:
        return method_func(*args, team = whom, problem = problem, **kwargs)

# vim: expandtab fdm=indent foldnestmax=1
