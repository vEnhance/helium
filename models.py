from __future__ import unicode_literals

from django.db import models
from django.contrib.auth import models as auth
from django.core.exceptions import ValidationError
import logging
import collections
from django.db.models import Sum


# Originally referenced registration models,
# but it seemed cleaner to just create a copy of the data here,
# so that (i) Helium is entirely divorced from registration,
# (ii) makes it easier to use Helium externally,
# (iii) reg models not written by me and all code not by me is bad.
# Actually re (iii) the whole {Mathlete/Team}{Nov/Feb} is bad
# and I think it should go die in a burning hole

# Moreover, teams and mathletes really should be the same object
# (namely, "contest takers")

# Contestant objects

class TeamManager(models.Manager):
	def get_queryset(self):
		return super(TeamManager, self).get_queryset().filter(is_team=True)
class MathleteManager(models.Manager):
	def get_queryset(self):
		return super(MathleteManager, self).get_queryset().filter(is_team=False)

class Entity(models.Model): # This is EITHER a team or mathlete (i.e. exam taker)
	name = models.CharField(max_length=80)
	team = models.ForeignKey('self', null=True, blank=True)
	is_team = models.BooleanField(default=False)
	number = models.IntegerField(null=True, blank=True,
			help_text = "You can assign (unique) numbers here "
			"if you can't assume names are pairwise distinct."
			"This isn't used internally by Helium itself.")

	def clean(self):
		if self.team is not None and self.is_team:
			raise ValidationError("LOL what?")

	def __unicode__(self):
		return self.name

	@property
	def verbose_name(self):
		if self.is_team:
			return '%s [%s]' %(self.name, self.team.name)
		else:
			return self.team.name

	objects = models.Manager() # why do I have to repeat this?
	teams = TeamManager()
	mathletes = MathleteManager()

	class Meta:
		unique_together = ('is_team', 'number')

# Exam/problem objects

class Exam(models.Model):
	name = models.CharField(max_length=50, help_text='Name of exam')
	color = models.CharField(max_length=50, default='#FFFFFF',\
			help_text='Color which exam is printed on (shows up when grading)')
	is_indiv = models.BooleanField()
	is_ready = models.BooleanField(default=True, help_text='Mark true if ready to grade this exam')
	is_alg_scoring = models.BooleanField()
	is_scanned = models.BoolenField(default=False,
			help_text = "Whether the scan grader will show this problem or not. "
			"For example, this should almost certainly be False for Guts round.")

	min_grades = models.IntegerField(default=3, help_text='Minimum number of graders per problem')
	min_override = models.IntegerField(default=3,
			help_text='Number of graders required to override a grading conflict.')

	def __unicode__(self): return self.name
	@property
	def problems(self):
		return self.problem_set.order_by('problem_number')

class Problem(models.Model):
	exam = models.ForeignKey(Exam)
	problem_number = models.IntegerField()
	answer = models.CharField(max_length=70, default='')

	weight = models.FloatField(default=1)
	allow_partial = models.BooleanField(default=False)
	def __unicode__(self): return self.exam.name + " #" + unicode(self.problem_number)

	@property
	def is_indiv(self):
		return self.exam.is_indiv

	@property
	def intweight(self):
		return int(self.weight) if self.weight.is_integer() else self.weight

	class Meta:
		unique_together = ('exam', 'problem_number')

# Grading Objects

class Verdict(models.Model):
	problem = models.ForeignKey(Problem) # You should know which problem

	# You might have verdicts for which you don't know whose yet
	# because the verdict is created by a to-be-matched scribble
	entity = models.ForeignKey(Entity, blank=True, null=True)
	score = models.IntegerField(blank=True, null=True) # integer, score for the problem
	is_valid = models.BooleanField(default=True,
			help_text = "Whether there is an answer consensus")
	is_done = models.BooleanField(default=False,
			help_text = "Whether this verdict should be read by more normal users")

	def __unicode__(self):
		if self.entity is not None:
			who = unicode(self.entity)
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
		weak_evidence = [e for e in queryset if e.god_mode is False]
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
			else:
				mode_score, n = collections.Counter(scores).most_common(1)[0]
				ratio = self.problem.exam.min_override
				min_grades = self.problem.exam.min_grades

				# Test validity: if we have the correct ratio
				if (ratio+1) * n >= ratio * len(scores):
					self.score = mode_score
					self.is_valid = True
				else:
					self.score = None
					self.is_valid = False

				# Now mark as done if valid and long
				self.is_done = (self.is_valid and len(scores) >= min_grades)
		self.save()

	def evidence_count(self):
		return self.evidence_set.count()

	@property
	def is_indiv(self):
		return self.problem.is_indiv

	class Meta:
		unique_together = ('problem', 'entity')
	
# Scribble objects
class ExamScribble(models.Model):
	exam = models.ForeignKey(Exam)
	entity = models.ForeignKey(Entity, blank=True, null=True)
	scan_image = models.ImageField(upload_to='scans/names/', blank=False, null=True)
		 # blargh. This should really be null=False, but it makes testing hard.

	def __unicode__(self):
		if self.entity is not None:
			who = unicode(self.entity)
		else:
			who = 'ID %05d' % self.id
		return unicode(self.exam) + ': ' + who

	@property
	def is_indiv(self):
		return self.exam.is_indiv

	def assign(self, entity):
		assert entity.is_team != self.exam.is_indiv
		self.entity = entity
		self.updateScribbles()
		self.save()

	def updateScribbles(self, queryset = None):
		"""Update all child scribbles once mathlete/team identified"""
		if queryset is None:
			queryset = self.problemscribble_set.all()
		for ps in queryset:
			ps.verdict.entity = self.entity
			ps.verdict.save()

	def checkConflictVerdict(self, entity=None, purge=False):
		"""Check that no collisions will arise before updateScribbles.
		Note that purge is DANGEROUS and should use with judgment."""
		if entity is None:
			entity = self.entity
		for ps in self.problemscribble_set.all():
			verdict = ps.verdict
			problem = verdict.problem
			try: # search for conflicts
				bad_v = Verdict.objects.get(entity=entity, problem=problem)
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
				else: # forcefully grab all evidence from v then delete it
					for e in bad_v.evidence_set.all():
						if Evidence.objects.filter(verdict=verdict, user=e.user).exists():
							# geez this is so bad --- we'd get a uniqueness integrity error
							# on move so delete the offending e
							logging.warn("Deleting " + str(e.id))
							e.delete()
						else:
							# No integrity
							e.verdict = verdict
							e.save()
					logging.warn("Deleting " + str(bad_v.id) + " = " + str(bad_v))
					bad_v.delete()
					verdict.updateDecisions()
		return None # no conflicts

	class Meta:
		unique_together = ('exam', 'entity')

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

# HMMT object to store pairs of alpha and entity

class EntityAlpha(models.Model):
	entity = models.OneToOneField(Entity, on_delete=models.CASCADE)
	cached_alpha = models.FloatField(blank=True, null=True)

# Auxiliary functions
def get_exam_scores(exam, entity):
	queryset = Verdict.objects.filter(entity=entity, problem__exam=exam, is_valid=True)\
					.order_by('problem__problem_number')
	return [v.problem.intweight * (v.score or 0)
		if not v.problem.allow_partial else (v.score or 0)
		for v in queryset]

def get_alpha(entity):
	m, _ = EntityAlpha.objects.get_or_create(entity=entity)
	return m.cached_alpha or 0

# vim: foldnestmax=1 foldlevel=1 fdm=indent
