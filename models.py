"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

models.py

General overview of models:

* Entity objects represent either a team or mathlete
* These Entity's takes several Exams, with several Problems
* For every Entity and Problem, we have a Verdict (which gives the score)
  based on Evidence (one for each grader who read the problem)
* ExamScribble and ProblemScrrible objects keep track of scans
* EntirePDFScribble is a container for keeping track of uploaded PDF's
* EntityAlpha is a way to store alpha values (so we don't have to keep recomputing them)
* GutsScoreFunc is a stupid applet that lets you compute guts estimation scores


Notes on data creation:

* The Exam and Guts Scoring Function objects are meant to be edited
  directly through the admin interface.
* The Entity table is populated using the command heliumimport.


"""

from __future__ import unicode_literals

from django.db import models
from django.contrib.auth import models as auth
from django.core.exceptions import ValidationError
import logging
import collections

# Originally referenced registration models,
# but it seemed cleaner to just create a copy of the data here,
# so that (i) Helium is entirely divorced from registration,
# (ii) makes it easier to use Helium externally,
# (iii) reg models not written by me and all code not by me is bad.
# Actually re (iii) the whole {Mathlete/Team}{Nov/Feb} is bad
# and I think it should go die in a burning hole

# Moreover, teams and mathletes really should be the same object
# (namely, "contest takers")


### CONTESTANT Objects ###

# These are used to provide Entity.teams and Entity.mathletes
class TeamManager(models.Manager):
	def get_queryset(self):
		return super(TeamManager, self).get_queryset().filter(is_team = True)
class MathleteManager(models.Manager):
	def get_queryset(self):
		return super(MathleteManager, self).get_queryset().filter(is_team=False)

class Entity(models.Model):
	"""This represents EITHER a team or a mathlete --- i.e. a test taker.
	There are managers Entity.teams and Entity.mathletes to grab either
	(as well as Entity.objects, as usual).
	
	The `team` attribute points to another Entity,
	and should be set to None for (i) actual teams, and (ii) individuals without teams.
	In particular, in a contest with no teams this should always be None.
	The Boolean is_team distinguishes between use cases (i) and (ii).
	
	For HMMT, the management command heliumimport will copy data from registration into here.
	
	In addition to Entity.objects, the managers Entity.teams and Entity.mathletes."""

	name = models.CharField(max_length=80)
	shortname = models.CharField(max_length=80, default='', blank=True,
			help_text = "For teams, a shorter version of their name. "
			"This is used instead when attached to mathletes. "
			"Leave this blank to just use the team name instead. "
			"Leave this blank for individuals.")
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
		if self.team is not None:
			if self.team.shortname:
				return '%s [%s]' %(self.name, self.team.shortname)
			else:
				return '%s [%s]' %(self.name, self.team.name)
		elif self.is_team:
			if self.shortname:
				return '%s (%s)' %(self.name, self.shortname)
			else:
				return self.name
		else:
			return self.name

	objects = models.Manager() # why do I have to repeat this?
	teams = TeamManager()
	mathletes = MathleteManager()

	def size(self):
		"""This is the size of a team (or None on individuals)"""
		if not self.is_team: return None
		else: return self.entity_set.count()

	class Meta:
		unique_together = ('is_team', 'number')

# Exam/problem objects

class Exam(models.Model):
	name = models.CharField(max_length=50, help_text = 'Name of exam', unique = True)
	color = models.CharField(max_length=50, default="#FFFFFF",\
			help_text="Color which exam is printed on. "
			"Grading pages will be tinted with this color so that e.g. "
			"we don't accidentally have someone enter Algebra scores into Geometry. "
			"(This was a very common mistake in old Babbage.) "
			"This color is page background so it should be VERY light (like #EEFFEE light).")
	is_indiv = models.BooleanField(default=True)
	is_ready = models.BooleanField(default=True,
			help_text = "Mark true if you want users to be able to grade this exam. "
			"You should set it to False if you are waiting for scans for example. "
			"You can also set it to False after the exam is *done* grading, "
			"so as not to distract users. "
			"Note that this does not affect validation, it only affects the UI: "
			"in other words users can still navigate directly to a URL to grade this exam.")
	is_alg_scoring = models.BooleanField(default=True)
	is_scanned = models.BooleanField(default=False,
			help_text = "Whether the scan grader will show this problem or not. "
			"For example, this should almost certainly be False for Guts round.")

	min_grades = models.IntegerField(default=3,
			help_text="This is the minimum number of graders required before "
			" a problem is marked as `done grading` by the system.") 
	min_override = models.IntegerField(default=3,
			help_text="Number of graders required to override a grading conflict. "
			"For example, the default setting is that a 3:1 majority is sufficient "
			"to override a conflicting grade.")

	def __unicode__(self): return self.name
	@property
	def problems(self):
		return self.problem_set.order_by('problem_number')

class Problem(models.Model):
	exam = models.ForeignKey(Exam)
	problem_number = models.IntegerField(help_text = "Must be unique per exam.")
	answer = models.CharField(max_length=70, default='', blank=True,
			help_text = "The answer for a problem, which is shown in help texts.")

	weight = models.FloatField(default=1,
			help_text = "This is the weight of the problem. "
			"For tests with algorithmic scoring, this is overwritten later with beta values, "
			"and therefore the value of the weight is unimportant. "
			"For tests scored traditionally this weight should be an integer.")
	allow_partial = models.BooleanField(default=False,
			help_text = "If true, all recorded scores should be 0 or 1. "
			"If false, all recorded scores should be integers from 0 to the weight.")
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
	"""The Verdict object represents a collection of EVIDENCES,
	which are attached to a pair of (problem, entity).
	For example, `Algebra #3 score for Evan.`
	The entity will be None if grading a scan which has not yet been matched with an entity.
	"""
	problem = models.ForeignKey(Problem) # You should know which problem

	# You might have verdicts for which you don't know whose yet
	# because the verdict is created by a to-be-matched scribble
	entity = models.ForeignKey(Entity, blank=True, null=True,
			help_text = "This should be None for scans which have not yet been matched.")
	score = models.IntegerField(blank=True, null=True,
			help_text = "This should be 0 or 1 for all-or-nothing problems, "
			"and the actual score for problems which have weights. "
			"You should not need to touch this setting; it is auto-computed.")
	is_valid = models.BooleanField(default=True,
			help_text = "This is True if there are no conflicts in grading "
			"as determined by the min_override setting of the exam. "
			"You should not need to touch this setting; it is auto-computed.")
	is_done = models.BooleanField(default=False,
			help_text = "Whether this verdict should be read by more normal users "
			"as determined by the min_grades setting of the exam. "
			"You should not need to touch this setting; it is auto-computed.")

	def __unicode__(self):
		if self.entity is not None:
			who = unicode(self.entity)
		else:
			who = 'ID %05d' % self.id
		return unicode(self.problem) + ': ' + who

	def submitEvidence(self, user, score, god_mode=False):
		"""This is the main process called if a USER submits a SCORE.
		It creates an Evidence object for that user unless one already exists,
		and then the Verdict will recompute the score and validity."""
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
		NOTE: queryset should NOT be a generator
		
		It should not really be necessary to call this function because
		submitEvidence will do it for you."""
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
class EntirePDFScribble(models.Model):
	"""This holds the name of a PDF (self.name) and the associated exam (self.exam),
	as well as is_done boolean."""
	name = models.CharField(max_length=80, unique = True,
			help_text = "The name of the PDF file, which must be unique "\
			"(this is a safety feature to prevent accidental double uploads). ")
	exam = models.ForeignKey(Exam, help_text = "The exam associated to this PDF.")
	is_done = models.BooleanField(default=False, help_text = "Whether the PDF is done converting.")
	def __unicode__(self): return unicode(self.name)

class ExamScribble(models.Model):
	"""This object represents the entire scan for an entity taking some exam.
	Several `problem scribbles`, which represent the individual answers of the scan,
	should be created at the same time an exam scribble is created.

	Call the `assign` function in order to identify the scribble."""
	
	pdf_scribble = models.ForeignKey(EntirePDFScribble,
			help_text = "The PDF from which the exam scribble comes from.")
	exam = models.ForeignKey(Exam,
			help_text = "The exam associated to an exam scribble file.")
	# ^ technically redundant, TODO rewrite to pdf_scribble__exam
	entity = models.ForeignKey(Entity, blank=True, null=True,
			help_text = "This is the entity the scan belongs to. "
			"It is None if the scan has not yet been identified.")
	full_image = models.ImageField(upload_to='scans/full/', blank=False, null=True,
			help_text = "This is the image of the entire scan.")
	name_image = models.ImageField(upload_to='scans/names/', blank=False, null=True,
			help_text = "This is the image of the `name` field for the scan.")
		# blargh. These should really be null=False, but it makes testing hard.
	needs_attention = models.CharField(max_length=80, blank=True, default='',
			help_text = "Text description of an issue with this scan "
			"(no name, no such student, et cetera).")

	def __unicode__(self):
		if self.entity is not None:
			who = unicode(self.entity)
		else:
			who = 'ID %05d' % self.id
		return unicode(self.exam) + ': ' + who

	@property
	def is_indiv(self):
		return self.exam.is_indiv

	def createProblemScribble(self, n, prob_image):
		"""Creates a problem scribble from problem number (n) and prob_image"""
		problem = Problem.objects.get(problem_number = n, exam = self.exam)
		v = Verdict.objects.create(problem = problem)
		v.save()
		ps = ProblemScribble.objects.create(
				examscribble = self,
				verdict = v,
				prob_image = prob_image)

	def assign(self, entity):
		"""Identifies the scan as being owned by an entity.
		This will update all the attached problem scribbles accordingly."""
		assert entity.is_team != self.exam.is_indiv
		self.entity = entity
		if not self.checkConflictVerdict():
			self.updateScribbles()
		self.save()

	def updateScribbles(self, queryset = None):
		"""Update all child scribbles once mathlete/team identified.
		This should not need to be called directly; assign will do it for you."""
		if queryset is None:
			queryset = self.problemscribble_set.all()
		for ps in queryset:
			ps.verdict.entity = self.entity
			ps.verdict.save()

	def checkConflictVerdict(self, entity=None, purge=False):
		"""Check that no integrity errors (uniqueness)
		will arise before updateScribbles.
		If passed with the `purge` option, it will instead destroy
		existing Verdict and Evidence objects that conflict.
		Returns None if no issues arise,
		otherwise returns an example of a Verdict which is bad.
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
					logging.warn("Deleting " + str(bad_v.id) + " = " + str(bad_v))
					bad_v.delete()
					verdict.updateDecisions()
		return None # no conflicts

	class Meta:
		unique_together = ('exam', 'entity')

class ProblemScribble(models.Model):
	"""This is attached to a Verdict which is being graded by scan.
	It contains the data of scanned image and the ExamScribble it came from.
	For convenience, it contains a submitEvidence wrapper function
	which links to the original Verdict function."""

	examscribble = models.ForeignKey(ExamScribble)
	verdict = models.OneToOneField(Verdict, on_delete=models.CASCADE)
	prob_image = models.ImageField(upload_to='scans/problems/', blank=False, null=True)
		# blargh. This should really be null=False, but it makes testing hard.
	last_sent_time = models.IntegerField(blank=True, null=True,
			help_text = "Most recent time the scan was sent out (in seconds since Epoch);"\
			"reset to None when the problem is graded. "\
			"This prevents the scan grader from accidentally giving duplicates.")

	def __unicode__(self): return unicode(self.verdict)

	def submitEvidence(self, *args, **kwargs):
		self.verdict.submitEvidence(*args, **kwargs)


class Evidence(models.Model):
	"""This represents a single input by a given user for a verdict:
	`Evan entered a score of 1 on Algebra #3 for X`
	is an example of a valid interpretation."""

	verdict = models.ForeignKey(Verdict)
	user = models.ForeignKey(auth.User)
	score = models.IntegerField(help_text = "The score assigned by the user")
	god_mode = models.BooleanField(default=False, help_text = 
			"If enabled, this piece of evidence is in GOD MODE. "
			"That means that all other evidences are ignored for that verdict."
			"If more than one evidence is in God mode, the verdict will be marked invalid. ")
	def __unicode__(self): return unicode(self.id)

	def clean(self):
		if not self.verdict.problem.allow_partial and not self.score in (0,1):
			raise ValidationError("All-or-nothing problem with non-binary score")
		if not user.is_superuser and self.god_mode is True:
			raise ValidationError("Only super-users may submit in GOD MODE")

	class Meta:
		unique_together = ('verdict', 'user')

class GutsScoreFunc(models.Model):
	"""Stores a scoring function for Guts Estimation.
	This is pretty self-explanatory."""

	problem_number = models.IntegerField(unique=True,
			help_text = "This is the problem number on Guts Round.")
	description = models.CharField(max_length=80, blank=True,
			help_text = "A brief description of the problem, shown only in admin interface.")
	answer = models.CharField(max_length=80,
			help_text = "True answer for problem, not actually used by model, shown in grader.")
	scoring_function = models.TextField(
			default="function (x) {\n\treturn Math.round(Math.max(0, WEIGHT-Math.abs(ANS-x)));\n}",
			help_text =
			"Javascript syntax for a one-variable function. "
			"This is the score reported if a staff member enters input x.\n"
			"Can span multiple lines.")
	problem_help_text = models.CharField(max_length=120, blank=True,
			default="Input an integer.",
			help_text = "An optional text that will display to help the staff member. "
			"For example, `input a string of seven letters`.")

	def __unicode__(self):
		return "Guts %d" %self.problem_number
	

# HMMT object to store pairs of alpha and entity
class EntityAlpha(models.Model):
	"""This is a storage object which keeps the alpha value for an entity.
	(Algorithmic scoring for HMMT.)"""
	entity = models.OneToOneField(Entity, on_delete=models.CASCADE)
	cached_alpha = models.FloatField(blank=True, null=True)

# Auxiliary functions
# not in use, since it's too slow when called in succession
# better to group all verdicts together ("bucket sort")
# rather than repeatedly filter

#def get_exam_scores(exam, entity):
#	"""Returns all (valid) Verdicts for an entity taking some exam.
#	For Verdicts with no score yet, a score of zero is reported."""
#	queryset = Verdict.objects.filter(entity=entity, problem__exam=exam, is_valid=True)\
#					.order_by('problem__problem_number')
#	return [v.problem.intweight * (v.score or 0)
#		if not v.problem.allow_partial else (v.score or 0)
#		for v in queryset]

def get_alpha(entity):
	"""Wrapper function to look up the alpha value for an entity.
	Creates the EntityAlpha object if it doesn't yet exist.
	Returns 0 if no alpha value has been assigned yet."""
	m, _ = EntityAlpha.objects.get_or_create(entity=entity)
	return m.cached_alpha or 0

# vim: foldnestmax=1 foldlevel=1 fdm=indent
